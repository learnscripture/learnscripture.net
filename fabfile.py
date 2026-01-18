"""
fabfile for deploying and managing LearnScripture.net
"""

import glob
import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from shlex import quote

from fabric.connection import Connection
from fabutils import apt, disks, files, locales, postgresql, services, ssh, ssl, users
from fabutils.connections import local_task, managed_connection_task
from fabutils.templates import Template, upload_template_and_reload

# from fabric.api import env, hide, local, run, task
# from fabric.context_managers import cd, lcd, prefix, shell_env
# from fabric.contrib.files import append, exists, upload_template
# from fabric.decorators import with_settings
# from fabric.operations import get, put


Database = postgresql.Database


join = os.path.join
rel = lambda *x: os.path.normpath(join(os.path.abspath(os.path.dirname(__file__)), *x))

DOMAINS = ["learnscripture.net"]

PROJECT_NAME = "learnscripture"
PROJECT_PYTHON_MODULE = "learnscripture"
PROJECT_USER = "learnscripture"
PROJECT_LOCALE = "en_US.UTF-8"

DEFAULT_HOST = "learnscripture.net"  # Where to deploy to.
DEFAULT_USER = PROJECT_USER

FULL_PYTHON_VERISON = Path(".python-version").read_text().strip()

# Python version
PYTHON_BIN = "python3.10"
PYTHON_PREFIX = ""  # e.g. /usr/local  Use "" for automatic
PYTHON_FULL_PATH = f"{PYTHON_PREFIX}/bin/{PYTHON_BIN}" if PYTHON_PREFIX else PYTHON_BIN

LOCAL_DB_BACKUPS = rel("..", "db_backups")

DB_LABEL_DEFAULT = "default"
DB_LABEL_WORDSUGGESTIONS = "wordsuggestions"


SECRETS_FILE_REL = "config/secrets.json"
NON_VCS_SOURCES = [
    SECRETS_FILE_REL,
]
SECRETS_FILE = rel(".", SECRETS_FILE_REL)


CURRENT_VERSION = "current"

REQS = [
    # Daemons
    "ufw",
    # Command line tools which are used non interactively
    "debian-goodies",  # checkrestart
    "software-properties-common",
    "unattended-upgrades",
    "rsync",
    "git",
    # Tools for interactive use only
    "htop",
    "mosh",
    "net-tools",
    "nmap",
    "silversearcher-ag",
    "git-core",
    "aptitude",
    "ncdu",
    # Databases/servers
    "postgresql",  # without version numbers, uses the supported version, which is usually fine
    "postgresql-client",
    "postgresql-contrib",
    "memcached",
    # Daemons
    "supervisor",  # For running uwsgi and php-cgi daemons
    "nginx",
    # Python stuff
    "python3",
    "python3-pip",
    "python3-wheel",
    "python3-virtualenv",
    "python3.10",
    "python3.10-dev",
    "python3.10-full",
    "python3.10-venv",
    "pipx",  # use this to install uv, use that for everything else
    "python3-virtualenvwrapper",
    "python3-setuptools",
    # For building Python extensions
    "build-essential",
    "python3-dev",
    "libpq-dev",  # For psycopg2
    "libxml2-dev",  # For lxml/uwsgi
    "libxslt-dev",  # For lxml/uwsgi
    "libffi-dev",  # For cffi
    # Soft PIL + jpegtran-cffi dependencies
    "libturbojpeg",
    "libjpeg8",
    "libjpeg8-dev",
    "libpng-dev",
    "libfreetype6",
    "libfreetype6-dev",
    "zlib1g",
    "zlib1g-dev",
    # Soft uwsgi requirement (for harakiri alerts)
    "libpcre3-dev",
    # Other
    "letsencrypt",
    "joe",
    "goaccess",  # web analytics. Actually we need v1.4 or later
]

os.environ["DJANGO_SETTINGS_MODULE"] = "learnscripture.settings_local"  # noqa

# My decorators
task = managed_connection_task(DEFAULT_USER, DEFAULT_HOST)
root_task = managed_connection_task("root", DEFAULT_HOST)

# -- System level install/provision --


@root_task()
def root_hostname(c):
    c.run("echo $(whoami) @ $(hostname)", echo=True)


@root_task()
def initial_secure(c: Connection):
    """
    Lock down server and secure. Run this after creating new server.
    """
    apt.update_upgrade(c)
    ssh.disable_root_login_with_password(c)
    print("Security steps completed.")


@root_task()
def provision(c: Connection):
    """
    Installs the base system and Python requirements for the entire server.
    """
    locales.install(c, PROJECT_LOCALE)
    _install_system(c)
    _configure_services(c)
    _fix_startup_services(c)


def _install_system(c: Connection):
    # Install system requirements
    apt.update_upgrade(c)
    apt.install(c, REQS)
    # Remove some bloat:
    apt.remove(c, ["snapd"])
    disks.add_swap(c, size="1G", swappiness="10")
    ssl.generate_ssl_dhparams(c)


def _configure_services(c: Connection):
    files.append(
        c,
        "/etc/postgresql/12/main/postgresql.conf",
        [
            "#------- Added for LearnScripture -----",
            "synchronous_commit = off",
        ],
    )
    c.run("service postgresql restart", echo=True)


def _fix_startup_services(c: Connection):
    services.enable(c, "supervisor")
    services.enable(c, "postgresql")
    services.disable(c, "memcached")  # We use our own instance


# Templates

TEMPLATES = [
    Template(
        system=True,
        local_path="config/nginx.conf.template",
        remote_path=f"/etc/nginx/sites-enabled/{PROJECT_NAME}.conf",
        reload_command="service nginx reload",
    ),
    Template(
        system=True,
        local_path="config/supervisor.conf.template",
        remote_path=f"/etc/supervisor/conf.d/{PROJECT_NAME}.conf",
        reload_command="supervisorctl reread; supervisorctl update",
    ),
    Template(
        system=True,
        local_path="config/crontab.template",
        remote_path=f"/etc/cron.d/{PROJECT_NAME}",
        reload_command="service cron reload",
        owner="root",
        mode="600",
    ),
]

TEMPLATE_CONTEXT = {
    "DOMAINS_REGEX": "|".join(re.escape(d) for d in DOMAINS),
    "DOMAINS_NGINX": " ".join(DOMAINS),
    "LOCALE": PROJECT_LOCALE,
    "PROJECT_PYTHON_MODULE": PROJECT_PYTHON_MODULE,
    "PROJECT_USER": PROJECT_USER,
    "PROJECT_NAME": PROJECT_NAME,
}


def get_system_templates() -> list[Template]:
    return [template for template in TEMPLATES if template.system]


def get_project_templates() -> list[Template]:
    return [template for template in TEMPLATES if not template.system]


# -- Project level deployment

# Versions and conf:

# Version class encapsulates the fact that on each deploy we create a new
# directory for virtualenv and sources, and after we are done setting it up, we
# switch the 'current' link to the new version.


class Version:
    PROJECT_ROOT_BASE = f"/home/{PROJECT_USER}/webapps/{PROJECT_NAME}"
    VERSIONS_ROOT = os.path.join(PROJECT_ROOT_BASE, "versions")
    MEDIA_ROOT_SHARED = PROJECT_ROOT_BASE + "/media"
    DATA_ROOT_SHARED = PROJECT_ROOT_BASE + "/data"

    @classmethod
    def current(cls) -> "Version":
        return cls(CURRENT_VERSION)

    def __init__(self, version):
        self.version = version
        self.PROJECT_ROOT = os.path.join(self.VERSIONS_ROOT, version)
        self.SRC_ROOT = os.path.join(self.PROJECT_ROOT, "src")
        self.VENV_ROOT = os.path.join(self.PROJECT_ROOT, "venv")
        # MEDIA_ROOT/STATIC_ROOT/DATA_ROOT -  sync with settings
        self.STATIC_ROOT = os.path.join(self.PROJECT_ROOT, "static")
        self.MEDIA_ROOT = os.path.join(self.PROJECT_ROOT, "usermedia")
        self.DATA_ROOT = os.path.join(self.PROJECT_ROOT, "data")

        CONF = secrets()

        db_user = CONF["PRODUCTION_DB_USER"]
        db_password = CONF["PRODUCTION_DB_PASSWORD"]
        db_port = CONF["PRODUCTION_DB_PORT"]

        self.DBS = {
            DB_LABEL_DEFAULT: Database(
                name=CONF["PRODUCTION_DB_NAME"],
                user=db_user,
                password=db_password,
                port=db_port,
                locale=PROJECT_LOCALE,
            ),
            DB_LABEL_WORDSUGGESTIONS: Database(
                name=CONF["PRODUCTION_DB_NAME_WS"],
                user=db_user,
                password=db_password,
                port=db_port,
                locale=PROJECT_LOCALE,
            ),
        }

    def make_dirs(self, c: Connection):
        for dirname in [
            self.PROJECT_ROOT,
            self.MEDIA_ROOT_SHARED,
            self.DATA_ROOT_SHARED,
        ]:
            files.require_directory(c, dirname)
        links = [
            (self.MEDIA_ROOT, self.MEDIA_ROOT_SHARED),
            (self.DATA_ROOT, self.DATA_ROOT_SHARED),
        ]
        for link, dest in links:
            if not files.exists(c, link):
                c.run(f"ln -s {quote(dest)} {quote(link)}")

    def project_run(self, c: Connection, cmd: str, **kwargs):
        with (
            c.cd(self.SRC_ROOT),
            c.prefix(f"source {self.VENV_ROOT}/bin/activate"),
            c.prefix("PATH=~/.local/bin:$PATH"),
        ):
            env = kwargs.pop("env", {})
            env["UV_PROJECT_ENVIRONMENT"] = self.VENV_ROOT
            kwargs["env"] = env
            return c.run(cmd, **kwargs)


def secrets():
    return json.load(open(rel(".", "config", "secrets.json")))


# -- Project level tasks ---


@task()
def create_project(c: Connection):
    # create_project_user has to come before `deploy_system`
    # because system level config refers to this user
    create_project_user(c)
    deploy_system(c)
    create_databases(c)


@root_task()
def create_project_user(c: Connection):
    if not users.user_exists(c, PROJECT_USER):
        ssh_keys = [os.path.expandvars("$HOME/.ssh/id_rsa.pub")]
        users.create_user(c, PROJECT_USER, ssh_public_keys=ssh_keys)
        files.require_directory(c, f"/home/{PROJECT_USER}/logs", owner=PROJECT_USER, group=PROJECT_USER)


@root_task()
def create_databases(c: Connection):
    target = Version.current()
    # Run create user first, because it deletes user as part of process, and we
    # don't want that happening after a DB has been created.
    for db in target.DBS.values():
        if not postgresql.check_user_exists(c, db, db.user):
            postgresql.create_default_user(c, db)
    for db in target.DBS.values():
        if not postgresql.check_database_exists(c, db):
            postgresql.create_db(c, db)


@root_task()
def deploy_system(c: Connection):
    """
    Deploy system level (root) components.
    """
    target = Version.current()
    for template in get_system_templates():
        context_data = TEMPLATE_CONTEXT | target.__dict__
        upload_template_and_reload(c, template, context_data)


def check_templates():
    target = Version.current()
    for template in TEMPLATES:
        context_data = TEMPLATE_CONTEXT | target.__dict__
        with open(template.local_path) as f:
            local_data = f.read()
            local_data %= context_data


@task()
def deploy(
    c: Connection,
    skip_checks=False,
    test_host=False,
    skip_selenium=False,
    allow_missing_ftl: bool = False,
):
    """
    Deploy project.
    """
    if not test_host:
        check_branch(c)
    check_sentry_auth(c)
    check_templates()

    build_static(c)
    if not skip_checks:
        code_quality_checks(c, skip_selenium=skip_selenium, allow_missing_ftl=allow_missing_ftl)
    if not test_host:
        push_to_central_vcs(c)
    target = create_target(c)
    push_sources(c, target)
    push_static(c, target)
    create_venv(c, target)
    install_requirements(c, target)
    smoke_test(c, target)
    collect_static(c, target)
    upload_project_templates(c, target)
    update_database(c, target)
    make_target_current(c, target)
    if not test_host:
        tag_deploy(c)  # Once 'current' symlink is switched
    deploy_system(c)
    restart_all(c)
    delete_old_versions(c)
    if not test_host:
        push_to_central_vcs(c)  # push tags
        # See also logic in settings.py for creating release name
        release = "learnscripturenet@" + target.version
        create_sentry_release(c, release, target.version)


@local_task()
def code_quality_checks(c: Connection, skip_selenium: bool = False, allow_missing_ftl: bool = False):
    """
    Run code quality checks, including tests.
    """
    # Quicker tests first
    c.run("ruff check .", echo=True)
    check_ftl(c, allow_missing_ftl=allow_missing_ftl)
    run_ftl2elm(c)
    with c.cd("learnscripture/static/elm"):
        c.run("npx elm-test --skip-install", echo=True)
    c.run("pytest -n0" + (" -m 'not selenium'" if skip_selenium else ""), echo=True)


def check_branch(c: Connection):
    if c.local("git rev-parse --abbrev-ref HEAD").stdout.strip() != "master":
        raise AssertionError("Branch must be 'master' for deploying")


def push_to_central_vcs(c: Connection):
    # This task is designed to fail if it would create multiple heads on
    # central VCS i.e. if central has code on the master branch that hasn't been
    # merged locally. This prevents deploys overwriting a previous deploy
    # unknowingly due to failure to merge changes.
    c.local("git push origin master", echo=True)


def create_target(c: Connection):
    commit_ref = get_current_git_ref(c)
    target = Version(commit_ref)
    target.make_dirs(c)
    return target


def push_sources(c: Connection, target: Version):
    """
    Push source code to server
    """
    ensure_src_dir(c, target)

    # For speed, we copy from previous dir
    previous_target = get_target_current_version(target)
    target_src_root = target.SRC_ROOT
    previous_src_root = previous_target.SRC_ROOT

    if not files.exists(c, os.path.join(target_src_root, ".git")):
        previous_target = get_target_current_version(target)
        previous_src_root = previous_target.SRC_ROOT
        if files.exists(c, previous_src_root) and files.exists(c, os.path.join(previous_src_root, ".git")):
            # For speed, clone the 'current' repo which will be very similar to
            # what we are pushing.
            c.run(f"git clone {previous_src_root} {target_src_root}", echo=True)
            with c.cd(target_src_root):
                c.run("git checkout master || git checkout -b master", echo=True)
        else:
            with c.cd(target_src_root):
                c.run("git init", echo=True)
        with c.cd(target_src_root):
            c.run("echo '[receive]' >> .git/config")
            c.run("echo 'denyCurrentBranch = ignore' >> .git/config")

    c.local(f"git push ssh://{c.user}@{c.host}/{target_src_root}", echo=True)
    with c.cd(target_src_root):
        c.run(f"git reset --hard {target.version}", echo=True)
    # NB we also use git at runtime in settings file to set Sentry release,
    # see settings.py

    # Also need to sync files that are not in main sources VCS repo.
    push_non_vcs_sources(c, target)

    # Need settings file
    with c.cd(target_src_root):
        c.run(
            "cp learnscripture/settings_local_example.py learnscripture/settings_local.py",
            echo=True,
        )


def tag_deploy(c: Connection):
    c.local("git tag deploy-production-$(date --utc --iso-8601=seconds | tr ':' '-' | cut -f 1 -d '+')")


def ensure_src_dir(c: Connection, target: Version):
    if not files.exists(c, target.SRC_ROOT):
        c.run(f"mkdir -p {target.SRC_ROOT}")


def push_non_vcs_sources(c, target):
    for src in NON_VCS_SOURCES:
        files.put(c, src, os.path.join(target.SRC_ROOT, src))


@contextmanager
def use_local_bin_PATH(c: Connection):
    with c.prefix("PATH=~/.local/bin:$PATH"):
        yield


def create_venv(c: Connection, target: Version):
    venv_root = target.VENV_ROOT
    if files.exists(c, venv_root):
        return

    with use_local_bin_PATH(c):
        c.run("pipx install uv", echo=True)
        c.run("pipx upgrade uv", echo=True)
        c.run("pipx ensurepath", echo=True)
        c.run(f"uv python install {FULL_PYTHON_VERISON}", echo=True)
        c.run(f"uv venv --seed --python={FULL_PYTHON_VERISON} {venv_root}", echo=True)
    c.run(
        f"echo {target.SRC_ROOT} > {target.VENV_ROOT}/lib/{PYTHON_BIN}/site-packages/projectsource.pth",
        echo=True,
    )


def install_requirements(c: Connection, target: Version):
    target.project_run(c, "uv sync --no-progress", echo=True)


webpack_deploy_files_pattern = "./learnscripture/static/webpack_bundles/*.deploy.*"
webpack_stats_file = "./webpack-stats.deploy.json"


def check_sentry_auth(c: Connection):
    if "SENTRY_AUTH_TOKEN" not in os.environ:
        raise AssertionError("SENTRY_AUTH_TOKEN not found in environment, see notes in development_setup.rst")


@local_task()
def check_ftl(c: Connection, allow_missing_ftl: bool = False):
    import django

    django.setup()
    from django.conf import settings

    from learnscripture.ftl_bundles import main

    print("Checking FTL")
    errors = main.check_all([code for code, _ in settings.LANGUAGES])
    if errors:
        print("Errors in FTL files:")
        print("".join(str(e) for e in errors))
        sys.exit(1)

    missing_ftl_messages = _check_missing_ftl_messages()
    if missing_ftl_messages:
        print(missing_ftl_messages)
        if not allow_missing_ftl:
            sys.exit(1)


def _check_missing_ftl_messages():
    s = subprocess.check_output(["compare-locales", "l10n.toml", ".", "--json", "-"]).decode("utf-8")
    data = json.loads(s)[0]
    details = data["details"]
    output = []
    for path, path_data in details.items():
        # Helpfully, the JSON has a different structure if there is a single
        # FTL with a problem compared to multiple files (!)

        # So we normalise back to the case for multiple here
        if isinstance(path_data, dict):
            base_path = path
            problem_files = path_data
        elif isinstance(path_data, list):
            base_path = os.path.dirname(path)
            problem_files = {os.path.basename(path): path_data}
        else:
            raise NotImplementedError(f"Not expecting {path_data}")

        for filename, problems in sorted(problem_files.items()):
            full_path = base_path + "/" + filename
            output.append(f"- File: {full_path}")
            for item in problems:
                if "missingEntity" in item:
                    output.append(" - Missing: " + item["missingEntity"])
                if "obsoleteEntity" in item:
                    output.append(" - Obsolete: " + item["obsoleteEntity"])

    return "\n".join(output)


@local_task()
def run_ftl2elm(c: Connection, watch=False):
    cmdline = "ftl2elm --locales-dir learnscripture/locales --output-dir learnscripture/static/elm --when-missing=fallback --include='**/learn.ftl'"
    if watch:
        cmdline += " --watch --verbose"
    c.run(cmdline, echo=True)


@local_task()
def build_static(c: Connection):
    run_ftl2elm(c)
    for f in glob.glob(webpack_deploy_files_pattern):
        os.unlink(f)
    if os.path.exists(webpack_stats_file):
        os.unlink(webpack_stats_file)
    c.run("npm run build:deploy", echo=True)
    webpack_data = json.load(open(webpack_stats_file))
    assert webpack_data["status"] == "done"


def push_static(c: Connection, target: Version):
    webpack_data = json.load(open(webpack_stats_file))
    assert webpack_data["status"] == "done"
    deploy_files = [
        os.path.abspath(f) for f in glob.glob(webpack_deploy_files_pattern) if not f.endswith(".LICENCE.txt")
    ]
    deploy_files_2 = [asset["path"] for asset in webpack_data["assets"].values()]
    s1 = set(deploy_files)
    s2 = set(deploy_files_2)
    assert s1 == s2, f"Expected {s1} == {s2}"

    # Now rewrite stats file to use server paths
    for name, asset in webpack_data["assets"].items():
        asset["path"] = os.path.join(target.SRC_ROOT, "learnscripture/static/webpack_bundles", asset["name"])
    with open(webpack_stats_file, "w") as fp:
        json.dump(webpack_data, fp)

    for f in list(s1) + [webpack_stats_file]:
        rel_f = os.path.relpath(f)
        remote_f = os.path.join(target.SRC_ROOT, rel_f)
        d = os.path.dirname(remote_f)
        if not files.exists(c, d):
            c.run(f"mkdir -p {d}", echo=True)

        files.put(c, f, remote_f)


def smoke_test(c: Connection, target: Version):
    target.project_run(c, "./manage.py smoke_test", echo=True)


def collect_static(c: Connection, target: Version):
    assert target.STATIC_ROOT.strip() != "" and target.STATIC_ROOT.strip() != "/"
    target.project_run(c, "./manage.py collectstatic -v 0 --noinput", echo=True)

    # This is needed for certbot/letsencrypt:
    c.run(f"mkdir -p {target.STATIC_ROOT}/root", echo=True)

    # Permissions
    c.run(f"chmod -R ugo+r {target.STATIC_ROOT}", echo=True)


def upload_project_templates(c, target):
    target = Version.current()
    for template in get_project_templates():
        context_data = TEMPLATE_CONTEXT | target.__dict__
        upload_template_and_reload(c, template, context_data)


def update_database(c: Connection, target: Version):
    for db in target.DBS.keys():
        target.project_run(
            c,
            f"./manage.py migrate --database {db} --noinput --fake-initial",
            echo=True,
        )


def get_target_current_version(target: Version) -> Version:
    return target.__class__.current()


def make_target_current(c: Connection, target: Version) -> None:
    # Switches synlink for 'current' to point to 'target.PROJECT_ROOT'
    current_target = get_target_current_version(target)
    c.run(f"ln -snf {target.PROJECT_ROOT} {current_target.PROJECT_ROOT}", echo=True)


def get_current_git_ref(c: Connection) -> str:
    return c.local("git rev-parse HEAD").stdout.strip()


@task()
def delete_old_versions(c: Connection):
    fix_perms(c, Version.VERSIONS_ROOT, PROJECT_USER)
    with c.cd(Version.VERSIONS_ROOT):
        commitref_glob = "?" * 40
        c.run(f"ls -dtr {commitref_glob} | head -n -5 | xargs rm -rf", echo=True)


@root_task()
def fix_perms(c: Connection, path: str, user: str):
    with c.cd(path):
        c.run(f"find . -user root -exec 'chown' '{user}' '{{}}' ';'", echo=True)


@task()
def run_word_suggestions_analyzers(c: Connection) -> None:
    target = Version.current()
    target.project_run(c, "./manage.py run_suggestions_analyzers", echo=True)


# Managing running system


@root_task()
def stop_webserver(c: Connection):
    """
    Stop the webserver that is running the Django instance
    """
    supervisorctl(c, f"stop {PROJECT_NAME}_uwsgi")


@root_task()
def start_webserver(c: Connection):
    """
    Starts the webserver that is running the Django instance
    """
    supervisorctl(c, f"start {PROJECT_NAME}_uwsgi")


@root_task()
def restart_webserver(c: Connection):
    """
    Gracefully restarts the webserver that is running the Django instance
    """
    pidfile = f"/tmp/{PROJECT_NAME}_uwsgi.pid"
    if files.exists(c, pidfile):
        c.run(f"kill -HUP `cat {pidfile}`", echo=True)
    else:
        start_webserver(c)


@root_task()
def stop_task_queue(c: Connection):
    supervisorctl(c, f"stop {PROJECT_NAME}_django_q")


@root_task()
def restart_task_queue(c: Connection):
    """
    Restarts the task queue workers
    """
    supervisorctl(c, f"restart {PROJECT_NAME}_django_q")


@root_task()
def restart_all(c: Connection):
    restart_webserver(c)
    restart_task_queue(c)


@root_task()
def stop_all(c: Connection):
    stop_webserver(c)
    stop_task_queue(c)


def supervisorctl(c: Connection, *commands):
    c.run(f"supervisorctl {' '.join(commands)}", echo=True)


@task()
def manage_py_command(c: Connection, commands):
    target = Version.current()
    target.project_run(c, f"./manage.py {commands}", echo=True)


@task()
def erase_user(c: Connection, username: str):
    """
    Erase/delete user on production site
    """
    target = Version.current()
    target.project_run(c, f"./manage.py erase_user {username}", echo=True)


# DB snapshots


@task()
def get_and_load_production_db(c: Connection):
    """
    Dump current production Django DB and load into dev environment
    """
    filename = get_live_db(c)
    local_restore_from_dump(c, filename)


@task()
def get_live_db(c: Connection):
    filename = dump_db(c, Version.current().DBS[DB_LABEL_DEFAULT])
    c.local(f"mkdir -p {LOCAL_DB_BACKUPS}")
    return files.get(c, filename, LOCAL_DB_BACKUPS + "/" + os.path.basename(filename))


@local_task()
def local_restore_from_dump(c: Connection, filename):
    from django.conf import settings

    db_settings = settings.DATABASES[DB_LABEL_DEFAULT]
    db = Database(
        name=db_settings["NAME"],
        user=db_settings["USER"],
        password=db_settings["PASSWORD"],
        port=db_settings["PORT"],
        locale=PROJECT_LOCALE,
    )

    filename = os.path.abspath(filename)
    # We don't use fabutils postgresql commands because they assume postgres is
    # running as global service, and that doesn't seem to work when running with devbox
    c.run("devbox run create_dev_db", echo=True)
    postgresql.restore_db(c, db, filename)


def make_django_db_filename(db: Database):
    return f"/home/{PROJECT_USER}/db-{db.name}.django.{datetime.now().strftime('%Y-%m-%d_%H.%M.%S')}.pgdump"


def dump_db(c: Connection, db: Database):
    filename = make_django_db_filename(db)
    c.run(f"pg_dump -Fc -U {db.user} -O -f {filename} {db.name}", echo=True)
    return filename


@root_task()
def remote_restore_db_from_dump(c: Connection, db: Database, filename: str):
    """
    Perform database restore on remote system
    """
    if not postgresql.check_user_exists(c, db, db.user):
        postgresql.create_default_user(c, db)
    postgresql.drop_db_if_exists(c, db)
    postgresql.create_db(c, db)
    postgresql.restore_db(c, db, filename)


@task()
def migrate_upload_db(c: Connection, local_filename: str):
    stop_all(c)
    local_filename = os.path.normpath(os.path.abspath(local_filename))
    remote_filename = f"/home/{PROJECT_USER}/{os.path.basename(local_filename)}"
    files.put(c, local_filename, remote_filename)
    target = Version.current()
    remote_restore_db_from_dump(c, target.DBS[DB_LABEL_DEFAULT], remote_filename)


@root_task()
def install_or_renew_ssl_certificate(c: Connection):
    version = Version.current()
    certbot_static_path = version.STATIC_ROOT + "/root"
    files.require_directory(c, certbot_static_path)
    c.run(
        f"letsencrypt certonly --webroot -w {certbot_static_path} -d {DOMAINS[0]}",
        echo=True,
    )
    c.run("service nginx reload", echo=True)


@root_task()
def download_letsencrypt_conf(c):
    c.local(f"rsync -r -l root@{c.host}:/etc/letsencrypt/ config/letsencrypt/", echo=True)


@root_task()
def upload_letsencrypt_conf(c):
    c.local(f"rsync -r -l config/letsencrypt/ root@{c.host}:/etc/letsencrypt/", echo=True)


@local_task()
def create_sentry_release(c: Connection, version: str, last_commit):
    c.run(
        f"sentry-cli releases --org learnscripturenet new -p production {version}",
        echo=True,
    )
    # Commits not currently publically available
    # local('sentry-cli releases --org learnscripturenet set-commits --commit "learnscripture/learnscripture.net@{commit}" {version}'.format(version=version, commit=full_hash))
    c.run(f"sentry-cli releases --org learnscripturenet finalize {version}", echo=True)


@local_task()
def get_goaccess_logs(c: Connection):
    c.run("mkdir -p ../logs/", echo=True)
    c.run(
        "rsync -a --progress root@learnscripture.net:/var/log/goaccess ../logs/",
        echo=True,
    )


# TODO:
#
# We should automate the process of installing and configuring goaccess.
# - installation - https://goaccess.io/ - "Official GoAccess' Debian/Ubuntu Repository" method
# - then the following was done
#
#   mkdir /var/log/goaccess
#   zcat /var/log/nginx/access.log.*.gz | goaccess --restore --persist --log-format=COMBINED -o "/var/log/goaccess/report-$(date '+%Y-%m-%d').html" --keep-last=32 /var/log/nginx/access.log /var/log/nginx/access.log.1 -
#
# - daily reports are now done via crontab
#   - TODO - clean up all daily reports except first of the month

# For terminal display do:
# goaccess --restore --persist --log-format=COMBINED /var/log/nginx/access.log

# Live HTML report:
# goaccess --restore --persist --log-format=COMBINED /var/log/nginx/access.log -o /home/learnscripture/webapps/learnscripture/versions/current/static/_stats.html --real-time-html
