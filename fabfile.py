
"""
fabfile for deploying and managing LearnScripture.net
"""
import glob
import json
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime

import fabtools
from fabric.api import env, hide, local, run, task
from fabric.context_managers import cd, lcd, prefix, shell_env
from fabric.contrib.files import append, exists, upload_template
from fabric.decorators import with_settings
from fabric.operations import get, put

join = os.path.join
rel = lambda *x: os.path.normpath(join(os.path.abspath(os.path.dirname(__file__)), *x))

env.user = 'learnscripture'
env.hosts = ['learnscripture.net']

env.proj_name = "learnscripture"
env.proj_app = "learnscripture"  # Python module for project
env.proj_user = env.user

env.domains = ["learnscripture.net"]
env.domains_regex = "|".join(re.escape(d) for d in env.domains)
env.domains_nginx = " ".join(env.domains)

env.locale = "en_US.UTF-8"
env.num_workers = "3"

# Python version
PYTHON_BIN = "python3.5"
PYTHON_PREFIX = ""  # e.g. /usr/local  Use "" for automatic
PYTHON_FULL_PATH = "%s/bin/%s" % (PYTHON_PREFIX, PYTHON_BIN) if PYTHON_PREFIX else PYTHON_BIN

LOCAL_DB_BACKUPS = rel("..", "db_backups")

DB_LABEL_DEFAULT = 'default'
DB_LABEL_WORDSUGGESTIONS = 'wordsuggestions'


CURRENT_VERSION = 'current'

REQS = [
    # Daemons
    'ufw',

    # Command line tools which are used non interactively
    'debian-goodies',  # checkrestart
    'python-software-properties',  # apt-add-repository
    'software-properties-common',  # "
    'unattended-upgrades',
    'cron-apt',

    'rsync',
    'git',
    'mercurial',

    # Tools for interactive use only
    'htop',
    'mosh',
    'net-tools',
    'nmap',
    'silversearcher-ag',
    'git-core',
    'wajig',
    'ncdu',

    # Databases/servers
    'postgresql-9.5',
    'postgresql-contrib-9.5',
    'memcached',
    'rabbitmq-server',

    # Daemons
    'supervisor',  # For running uwsgi and php-cgi daemons
    'pgbouncer',  # For pooling and providing a central point of control of db connections
    'nginx',
    'postfix',  # to receive error messages from cron jobs, 'Local only' setup

    # Non-Python stuff
    'postgresql-client-9.5',

    # Python stuff
    'python',
    'python-pip',
    'python-virtualenv',
    'python-setuptools',

    # For building Python extensions
    'build-essential',
    'python-dev',
    'python3',
    'python3-dev',
    'libpq-dev',  # For psycopg2
    'libxml2-dev',  # For lxml/uwsgi
    'libxslt-dev',  # For lxml/uwsgi
    'libffi-dev',  # For cffi

    # Soft PIL + jpegtran-cffi dependencies
    'libturbojpeg',
    'libjpeg8',
    'libjpeg8-dev',
    'libpng12-0',
    'libpng12-dev',
    'libfreetype6',
    'libfreetype6-dev',
    'zlib1g',
    'zlib1g-dev',

    # Soft uwsgi requirement (for harakiri alerts)
    'libpcre3-dev',

]

os.environ['DJANGO_SETTINGS_MODULE'] = 'learnscripture.settings'  # noqa


# Utilities

as_rootuser = with_settings(user='root')


def virtualenv(venv):
    return prefix('source %s/bin/activate' % venv)


@contextmanager
def django_project(target):
    with virtualenv(target.VENV_ROOT):
        with cd(target.SRC_ROOT):
            yield


# Versions and conf:

# Version class encapsulates the fact that on each deploy we create a new
# directory for virtualenv and sources, and after we are done setting it up, we
# switch the 'current' link to the new version.

class Version(object):
    PROJECT_ROOT_BASE = "/home/%s/webapps/%s" % (env.proj_user, env.proj_name)
    VERSIONS_ROOT = os.path.join(PROJECT_ROOT_BASE, 'versions')
    MEDIA_ROOT_SHARED = PROJECT_ROOT_BASE + "/media"
    DATA_ROOT_SHARED = PROJECT_ROOT_BASE + "/data"

    @classmethod
    def current(cls):
        return cls(CURRENT_VERSION)

    def __init__(self, version):
        self.version = version
        self.PROJECT_ROOT = os.path.join(self.VERSIONS_ROOT, version)
        self.SRC_ROOT = os.path.join(self.PROJECT_ROOT, 'src')
        self.VENV_ROOT = os.path.join(self.PROJECT_ROOT, 'venv')
        # MEDIA_ROOT/STATIC_ROOT/DATA_ROOT -  sync with settings
        self.STATIC_ROOT = os.path.join(self.PROJECT_ROOT, 'static')
        self.MEDIA_ROOT = os.path.join(self.PROJECT_ROOT, 'usermedia')
        self.DATA_ROOT = os.path.join(self.PROJECT_ROOT, 'data')

        CONF = secrets()

        db_user = CONF["PRODUCTION_DB_USER"]
        db_password = CONF["PRODUCTION_DB_PASSWORD"]
        db_port = CONF["PRODUCTION_DB_PORT"]

        self.DBS = {
            DB_LABEL_DEFAULT: {
                'NAME': CONF["PRODUCTION_DB_NAME"],
                'USER': db_user,
                'PASSWORD': db_password,
                'PORT': db_port,
            },
            DB_LABEL_WORDSUGGESTIONS: {
                'NAME': CONF["PRODUCTION_DB_NAME_WS"],
                'USER': db_user,
                'PASSWORD': db_password,
                'PORT': db_port,
            }
        }

    def make_dirs(self):
        for d in [self.PROJECT_ROOT,
                  self.MEDIA_ROOT_SHARED,
                  self.DATA_ROOT_SHARED]:
            if not exists(d):
                run("mkdir -p %s" % d)
        links = [(self.MEDIA_ROOT, self.MEDIA_ROOT_SHARED),
                 (self.DATA_ROOT, self.DATA_ROOT_SHARED)]
        for l, dest in links:
            if not exists(l):
                run("ln -s %s %s" % (dest, l))


def secrets():
    return json.load(open(rel(".", "config", "secrets.json")))


# System level install
@task
@as_rootuser
def secure(new_user=env.user):
    """
    Minimal security steps for brand new servers.
    Installs system updates, creates new user for future
    usage, and disables password root login via SSH.
    """
    run("apt-get update -q")
    run("apt-get upgrade -y -q")
    if not fabtools.user.exists(new_user):
        ssh_keys = [os.path.expandvars("$HOME/.ssh/id_rsa.pub")]
        ssh_keys = list(filter(os.path.exists, ssh_keys))
        fabtools.user.create(new_user, group=new_user, ssh_public_keys=ssh_keys)
    run("sed -i 's:RootLogin yes:RootLogin without-password:' /etc/ssh/sshd_config")
    run("service ssh restart")
    print("Security steps completed. Log in to the server as '%s' from "
          "now on." % new_user)


@task
def provision():
    """
    Installs the base system and Python requirements for the entire server.
    """
    _install_system()
    _install_locales()
    _configure_services()
    _fix_startup_services()
    run("mkdir -p /home/%s/logs" % env.proj_user)


@as_rootuser
def _install_system():
    # Install system requirements
    update_upgrade()
    apt(" ".join(REQS))
    _add_swap()
    _install_python_minimum()
    _ssl_dhparam()


@as_rootuser
def _add_swap():
    # Needed to compile some things, and for some occassional processes that
    # need a lot of memory.
    if not exists("/swapfile"):
        run("fallocate -l 1G /swapfile")
        run("chmod 600 /swapfile")
        run("mkswap /swapfile")
        run("swapon /swapfile")
        append("/etc/fstab",
               "/swapfile   none    swap    sw    0   0\n")

    # Change swappiness
    run("sysctl vm.swappiness=10")
    append("/etc/sysctl.conf",
           "vm.swappiness=10\n")


@as_rootuser
def _ssl_dhparam():
    dhparams = "/etc/nginx/ssl/dhparams.pem"
    if not exists(dhparams):
        d = os.path.dirname(dhparams)
        if not exists(d):
            run("mkdir -p {0}".format(d))
        run("openssl dhparam -out {0} 2048".format(dhparams))


def _install_python_minimum():
    run("pip install --progress-bar off -U pip virtualenv wheel virtualenvwrapper mercurial")


@as_rootuser
def _install_locales():
    # Generate project locale
    locale = env.locale.replace("UTF-8", "utf8")
    with hide("stdout"):
        if locale not in run("locale -a"):
            run("locale-gen %s" % env.locale)
            run("update-locale %s" % env.locale)
            run("service postgresql restart")


@as_rootuser
def _configure_services():
    for l in ["#------- Added for LearnScripture -----",
              "synchronous_commit = off"]:
        append("/etc/postgresql/9.5/main/postgresql.conf", l)
    run("service postgresql restart")

    _configure_rabbitmq()


def _configure_rabbitmq():
    s = secrets()
    rabbitmq_username = s['RABBITMQ_USERNAME']
    rabbitmq_password = s['RABBITMQ_PASSWORD']
    users = run("rabbitmqctl list_users")
    users = [u.split('\t')[0] for u in users.split("\n")]
    if rabbitmq_username not in users:
        run("rabbitmqctl add_user {rabbitmq_username} {rabbitmq_password}".format(**locals()))
        run("rabbitmqctl add_vhost learnscripture")
        run("rabbitmqctl set_user_tags {rabbitmq_username} mytag".format(**locals()))
        run('rabbitmqctl set_permissions -p learnscripture {rabbitmq_username} ".*" ".*" ".*"'.format(**locals()))


@as_rootuser
def _fix_startup_services():
    for service in ["supervisor",
                    "postgresql",
                    ]:
        run("update-rc.d %s defaults" % service)
        run("service %s start" % service)

    for service in ['memcached',  # We use our own instance
                    ]:
        run("update-rc.d %s disable" % service)
        run("service %s stop" % service)


@as_rootuser
def apt(packages):
    """
    Installs one or more system packages via apt.
    """
    return run("apt-get install -y -q " + packages)


# Templates

TEMPLATES = {
    "nginx": {
        "system": True,
        "local_path": "config/nginx.conf.template",
        "remote_path": "/etc/nginx/sites-enabled/%(proj_name)s.conf",
        "reload_command": "service nginx reload",
    },
    "supervisor": {
        "system": True,
        "local_path": "config/supervisor.conf.template",
        "remote_path": "/etc/supervisor/conf.d/%(proj_name)s.conf",
        "reload_command": "supervisorctl reread; supervisorctl update",
    },
    "cron": {
        "system": True,
        "local_path": "config/crontab.template",
        "remote_path": "/etc/cron.d/%(proj_name)s",
        "owner": "root",
        "mode": "600",
    },
}


def inject_template(data):
    return dict([(k, v % env if isinstance(v, str) else v)
                 for k, v in data.items()])


def get_templates(filter_func=None):
    """
    Returns each of the templates with env vars injected.
    """
    injected = {}
    for name, data in TEMPLATES.items():
        if filter_func is None or filter_func(data):
            injected[name] = inject_template(data)
    return injected


def get_system_templates():
    return get_templates(lambda data: data['system'])


def get_project_templates():
    return get_templates(lambda data: not data['system'])


def upload_template_and_reload(name, target):
    """
    Uploads a template only if it has changed, and if so, reload the
    related service.
    """
    template = get_templates()[name]
    local_path = template["local_path"]
    if not os.path.exists(local_path):
        project_root = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(project_root, local_path)
    remote_path = template["remote_path"]
    reload_command = template.get("reload_command")
    owner = template.get("owner")
    mode = template.get("mode")
    remote_data = ""
    if exists(remote_path):
        with hide("stdout"):
            remote_data = run("cat %s" % remote_path)
    env_data = env.copy()
    env_data.update(target.__dict__)
    with open(local_path, "r") as f:
        local_data = f.read()
        local_data %= env_data
    clean = lambda s: s.replace("\n", "").replace("\r", "").strip()
    if clean(remote_data) == clean(local_data):
        return
    upload_template(local_path, remote_path, env_data, backup=False)
    if owner:
        run("chown %s %s" % (owner, remote_path))
    if mode:
        run("chmod %s %s" % (mode, remote_path))
    if reload_command:
        run(reload_command)


# Deploying project - user level

@task
def create_project():
    deploy_system()
    create_databases()


@as_rootuser
def create_databases():
    target = Version.current()
    # Run create user first, because it deletes user as part of process, and we
    # don't want that happening after a DB has been created.
    for db in target.DBS.values():
        with shell_env(**pg_environ(db)):
            if not db_check_user_exists_remote(db):
                for run_as_postgres, cmd in db_create_user_commands(db):
                    pg_run(cmd, run_as_postgres)

    for db in target.DBS.values():
        with shell_env(**pg_environ(db)):
            for run_as_postgres, cmd in db_create_commands(db):
                pg_run(cmd, run_as_postgres)


def pg_run(cmd, run_as_postgres):
    with cd("/"):  # suppress "could not change directory" warnings
        if run_as_postgres:
            return run("sudo -u postgres %s" % cmd)
        else:
            return run(cmd)


def pg_local(cmd, run_as_postgres, capture=False):
    with lcd("/"):  # suppress "could not change directory" warnings
        if run_as_postgres:
            retval = local("sudo -u postgres %s" % cmd, capture=capture)
        else:
            retval = local(cmd, capture=capture)
    if capture:
        print(retval)
        print(retval.stderr)
    return retval


@task
@as_rootuser
def deploy_system():
    """
    Deploy system level (root) components.
    """
    target = Version.current()
    for name in get_system_templates():
        upload_template_and_reload(name, target)


@task
def deploy():
    """
    Deploy project.
    """
    check_branch()
    build_static()
    code_quality_checks()
    push_to_central_vcs()
    target = create_target()
    push_sources(target)
    push_static(target)
    create_venv(target)
    install_requirements(target)
    collect_static(target)
    update_database(target)
    make_target_current(target)
    tag_deploy()  # Once 'current' symlink is switched
    deploy_system()
    restart_all()
    delete_old_versions()
    push_to_central_vcs()  # push tags


@task
def code_quality_checks():
    """
    Run code quality checks, including tests.
    """
    if getattr(env, 'skip_code_quality_checks', False):
        return
    local("flake8 .")
    local("isort -c")
    check_ftl()
    run_ftl2elm()
    with lcd("learnscripture/static/elm"):
        local("elm-test --skip-install")
    local("./runtests.py -f --nokeepdb")


def check_branch():
    if local("hg id -b", capture=True) != "default":
        raise AssertionError("Branch must be 'default' for deploying")
    if "master" not in local("hg id -B", capture=True).split(" "):
        raise AssertionError("Bookmark must be 'master' for deploying")


def push_to_central_vcs():
    # This task is designed to fail if it would create multiple heads on
    # BitBucket i.e. if BitBucket has code on the master branch that hasn't been
    # merged locally. This prevents deploys overwriting a previous deploy
    # unknowingly due to failure to merge changes.
    local("hg push -B master bitbucket; test $? -ne 255")


@task
def no_tag():
    """
    Don't tag deployment in VCS"
    """
    env.no_tag = True


def create_target():
    commit_ref = get_current_hg_ref()
    target = Version(commit_ref)
    target.make_dirs()
    return target


def push_sources(target):
    """
    Push source code to server
    """
    ensure_src_dir(target)

    # For speed, we copy from previous dir
    previous_target = get_target_current_version(target)
    target_src_root = target.SRC_ROOT
    previous_src_root = previous_target.SRC_ROOT

    if not exists(os.path.join(target_src_root, '.hg')):
        previous_target = get_target_current_version(target)
        previous_src_root = previous_target.SRC_ROOT
        if exists(previous_src_root) and exists(os.path.join(previous_src_root, '.hg')):
            # For speed, clone the 'current' repo which will be very similar to
            # what we are pushing. This will also be fast due to 'hg clone'
            # using hard links
            run("hg clone %s %s" % (previous_src_root,
                                    target_src_root))
        else:
            with cd(target_src_root):
                run("hg init")

    local("hg push -B . -f ssh://%(user)s@%(host)s/%(path)s || true" %
          dict(host=env.host,
               user=env.user,
               path=target_src_root,
               ))
    with cd(target_src_root):
        run("hg update -r %s" % target.version)

    # Also need to sync files that are not in main sources VCS repo.
    push_secrets(target)


def tag_deploy():
    if getattr(env, 'no_tag', False):
        return
    local("hg tag -f deploy-production-$(date --utc --iso-8601=seconds | tr ':' '-' | cut -f 1 -d '+')")


def ensure_src_dir(target):
    if not exists(target.SRC_ROOT):
        run("mkdir -p %s" % target.SRC_ROOT)


def push_secrets(target):
    put(rel(".", "config", "secrets.json"),
        os.path.join(target.SRC_ROOT, "config/secrets.json"))


def create_venv(target):
    venv_root = target.VENV_ROOT
    if exists(venv_root):
        return

    run("virtualenv --no-site-packages --python=%s %s" % (PYTHON_BIN, venv_root))
    run("echo %s > %s/lib/%s/site-packages/projectsource.pth" %
        (target.SRC_ROOT, target.VENV_ROOT, PYTHON_BIN))


def install_requirements(target):
    if getattr(env, 'no_installs', False):
        return

    # For speed and to avoid over-dependence on the network, we copy 'src'
    # directory from previous virtualenv. This does not install those packages
    # (no .egg-link files), but it makes VCS checkout installs much faster.
    # Other installs are kept fast due to the pip wheel cache.
    previous_target = get_target_current_version(target)
    target_venv_vcs_root = os.path.join(target.VENV_ROOT, 'src')
    previous_venv_vcs_root = os.path.join(previous_target.VENV_ROOT, 'src')
    if exists(previous_venv_vcs_root):
        run("rsync -a '--exclude=*.pyc' %s/ %s" %
            (previous_venv_vcs_root,
             target_venv_vcs_root))

    with django_project(target):
        run("pip install --progress-bar off --upgrade setuptools pip wheel six")
        run("pip install --progress-bar off -r requirements.txt --exists-action w")


webpack_deploy_files_pattern = "./learnscripture/static/webpack_bundles/*.deploy.*"
webpack_stats_file = "./webpack-stats.deploy.json"


@task
def check_ftl():
    import django
    django.setup()
    # Disbled for now until released version of django-ftl has this feature
    # from django.conf import settings
    # from learnscripture.ftl_bundles import main
    # errors = main.check_all([code for code, _ in settings.LANGUAGES])
    errors = []
    if errors:
        print("Errors in FTL files:")
        print(''.join(str(e) for e in errors))
        sys.exit(1)


@task
def run_ftl2elm(watch=False):
    cmdline = "ftl2elm --locales-dir learnscripture/locales --output-dir learnscripture/static/elm --when-missing=fallback --include='**/learn.ftl'"
    if watch:
        cmdline += " --watch --verbose"
    local(cmdline)


def build_static():
    run_ftl2elm()
    for f in glob.glob(webpack_deploy_files_pattern):
        os.unlink(f)
    if os.path.exists(webpack_stats_file):
        os.unlink(webpack_stats_file)
    local("./node_modules/.bin/webpack --config webpack.config.deploy.js")
    webpack_data = json.load(open(webpack_stats_file))
    assert webpack_data['status'] == 'done'


def push_static(target):
    webpack_data = json.load(open(webpack_stats_file))
    assert webpack_data['status'] == 'done'
    deploy_files = [os.path.abspath(f) for f in glob.glob(webpack_deploy_files_pattern)]
    deploy_files_2 = [part['path']
                      for chunk in webpack_data['chunks'].values()
                      for part in chunk]
    s1 = set(deploy_files)
    s2 = set(deploy_files_2)
    assert s1 == s2, "Expected {0} == {1}".format(s1, s2)

    # Now rewrite stats file to use server paths
    for name, chunk in webpack_data['chunks'].items():
        for part in chunk:
            part['path'] = os.path.join(target.SRC_ROOT,
                                        "learnscripture/static/webpack_bundles",
                                        part['name'])
    with open(webpack_stats_file, "w") as f:
        json.dump(webpack_data, f)

    for f in list(s1) + [webpack_stats_file]:
        rel_f = os.path.relpath(f)
        remote_f = os.path.join(target.SRC_ROOT, rel_f)
        d = os.path.dirname(remote_f)
        if not exists(d):
            run("mkdir -p %s" % d)

        put(f, remote_f)


def collect_static(target):
    assert target.STATIC_ROOT.strip() != '' and target.STATIC_ROOT.strip() != '/'
    with django_project(target):
        run("./manage.py collectstatic -v 0 --noinput")

    # This is needed for certbot/letsencrypt:
    run("mkdir {0}/root".format(target.STATIC_ROOT))

    # Permissions
    run("chmod -R ugo+r %s" % target.STATIC_ROOT)


def update_database(target):
    if getattr(env, 'no_db', False):
        return
    with django_project(target):
        if getattr(env, 'fake_migrations', False):
            args = "--fake"
        else:
            args = "--fake-initial"
        for db in [DB_LABEL_DEFAULT, DB_LABEL_WORDSUGGESTIONS]:
            run("./manage.py migrate --database %s --noinput %s" %
                (db, args))


def get_target_current_version(target):
    return target.__class__.current()


def make_target_current(target):
    # Switches synlink for 'current' to point to 'target.PROJECT_ROOT'
    current_target = get_target_current_version(target)
    run("ln -snf %s %s" %
        (target.PROJECT_ROOT,
         current_target.PROJECT_ROOT))


def get_current_hg_ref():
    ref = local("hg id -i", capture=True).strip()
    # assert not ref.endswith('+'), "Uncommitted changes in working dir"
    # Or - add extra timestamp for this case
    ref = ref.rstrip('+')
    return ref


@task
def fake_migrations():
    env.fake_migrations = True


@task
def delete_old_versions():
    fix_perms(Version.VERSIONS_ROOT, env.proj_user)
    with cd(Version.VERSIONS_ROOT):
        commitref_glob = "?" * 12
        run("ls -dtr %s | head -n -3 | xargs rm -rf" % commitref_glob)


@as_rootuser
def fix_perms(path, user):
    with cd(path):
        run("find . -user root -exec 'chown' '%s' '{}' ';'" % user)


@task
def run_word_suggestions_analyzers():
    target = Version.current()
    with django_project(target):
        run("./manage.py run_suggestions_analyzers")

# Managing running system


@task
def stop_webserver():
    """
    Stop the webserver that is running the Django instance
    """
    supervisorctl("stop %s_uwsgi" % env.proj_name)


@task
def start_webserver():
    """
    Starts the webserver that is running the Django instance
    """
    supervisorctl("start %s_uwsgi" % env.proj_name)


@task
@as_rootuser
def restart_webserver():
    """
    Gracefully restarts the webserver that is running the Django instance
    """
    run("kill -HUP `cat /tmp/%s_uwsgi.pid`" % (env.proj_name))


@task
def stop_celeryd():
    supervisorctl("stop %s_celeryd" % env.proj_name)


@task
def restart_celeryd():
    """
    Restarts the Celery workers
    """
    supervisorctl("restart %s_celeryd" % env.proj_name)


@task
def restart_all():
    restart_webserver()
    restart_celeryd()


@task
def stop_all():
    stop_webserver()
    stop_celeryd()


@task
@as_rootuser
def supervisorctl(*commands):
    run("supervisorctl %s" % " ".join(commands))


@task
def manage_py_command(*commands):
    target = Version.current()
    with django_project(target):
        run("./manage.py %s" % ' '.join(commands))


@as_rootuser
def update_upgrade():
    fabtools.deb.update_index(quiet=False)
    fabtools.deb.upgrade(safe=True)


# DB snapshots


@task
def get_and_load_production_db():
    """
    Dump current production Django DB and load into dev environment
    """
    filename = get_live_db()
    local_restore_from_dump(filename)


@task
def get_live_db():
    filename = dump_db(Version.current())
    local("mkdir -p %s" % LOCAL_DB_BACKUPS)
    return list(get(filename, local_path=LOCAL_DB_BACKUPS + "/%(basename)s"))[0]


@task
def local_restore_from_dump(filename):
    db = {}
    db['NAME'] = 'learnscripture'
    db['USER'] = 'learnscripture'
    db['PASSWORD'] = 'foo'
    db['HOST'] = '127.0.0.1'
    db['PORT'] = '5432'

    filename = os.path.abspath(filename)
    with shell_env(**pg_environ(db)):
        if not db_check_user_exists_local(db):
            for run_as_postgres, cmd in db_create_user_commands(db):
                pg_local(cmd, run_as_postgres)

        for run_as_postgres, cmd in (db_drop_database_commands(db) +
                                     db_create_commands(db) +
                                     pg_restore_cmds(db, filename)):
            pg_local(cmd, run_as_postgres)


def make_django_db_filename(target):
    return "/home/%s/db-%s.django.%s.pgdump" % (env.user, target.DBS[DB_LABEL_DEFAULT]['NAME'], datetime.now().strftime("%Y-%m-%d_%H.%M.%S"))


def dump_db(target):
    filename = make_django_db_filename(target)
    db = target.DBS[DB_LABEL_DEFAULT]
    run("pg_dump -Fc -U %s -O -o -f %s %s" % (db['USER'], filename, db['NAME']))
    return filename


def pg_restore_cmds(db, filename, clean=False):
    return [
        (False,
         "pg_restore -h localhost -O -U %s %s -d %s %s" % (db['USER'], " -c " if clean else "", db['NAME'], filename)),
    ]


def db_create_user_commands(db):
    return [
        (True,
         """psql -U postgres -d template1 -c "CREATE USER %s WITH PASSWORD '%s';" """ % (db['USER'], db['PASSWORD'])),
    ]


def db_check_user_exists_command(db):
    return ("""psql -U postgres -d postgres -t -c "SELECT COUNT(*) FROM pg_user WHERE usename='%s';" """
            % db['USER'])


def db_check_user_exists_local(db):
    output = pg_local(db_check_user_exists_command(db), True, capture=True).strip()
    return output == "1"


def db_check_user_exists_remote(db):
    output = pg_run(db_check_user_exists_command(db), True).strip()
    return output == "1"


def db_create_commands(db):
    return [
        (True,
         """ psql -U postgres -d template1 -c " """
         """ CREATE DATABASE %s """
         """ TEMPLATE = template0 ENCODING = 'UTF8' LC_CTYPE = '%s' LC_COLLATE = '%s';"""
         """ " """ % (db['NAME'], env.locale, env.locale)),

        (True,
         """psql -U postgres -d template1 -c "GRANT ALL ON DATABASE %s TO %s;" """ % (db['NAME'], db['USER'])),

        (True,
         """psql -U postgres -d template1 -c "ALTER USER %s CREATEDB;" """ % db['USER']),

    ]


def db_drop_database_commands(db):
    return [
        (True,
         """psql -U postgres -d template1 -c "DROP DATABASE IF EXISTS %s;" """ % db['NAME']),

    ]


def db_restore_commands(db, filename):
    return (db_drop_database_commands(db) +
            db_create_user_commands(db) +
            db_create_commands(db) +
            pg_restore_cmds(db, filename))


PG_ENVIRON_MAP = {
    'NAME': 'PGDATABASE',
    'HOST': 'PGHOST',
    'PORT': 'PGPORT',
    'USER': 'PGUSER',
    'PASSWORD': 'PGPASSWORD',
}


def pg_environ(db):
    """
    Returns the environment variables postgres command line tools like psql
    and pg_dump use as a dict, ready for use with Fabric's shell_env.
    """
    return {PG_ENVIRON_MAP[name]: str(val) for name, val in db.items() if name in PG_ENVIRON_MAP}


@as_rootuser
def db_restore(db, filename):
    with shell_env(**pg_environ(db)):
        for run_as_postgres, cmd in db_restore_commands(db, filename):
            pg_run(cmd, run_as_postgres)


@task
def migrate_upload_db(local_filename):
    stop_all()
    local_filename = os.path.normpath(os.path.abspath(local_filename))
    remote_filename = "/home/%s/%s" % (env.proj_user, os.path.basename(local_filename))
    put(local_filename, remote_filename)
    target = Version.current()
    db_restore(target.DBS[DB_LABEL_DEFAULT],
               remote_filename)


@task
def skip_code_quality_checks():
    env.skip_code_quality_checks = True


# This is for Ubuntu 16.04 with nginx
@task
@as_rootuser
def setup_certbot():
    run("apt-get install letsencrypt")


@task
@as_rootuser
def install_or_renew_ssl_certificate():
    version = Version.current()
    certbot_static_path = version.STATIC_ROOT + "/root"
    run("test -d {certbot_static_path} || mkdir {certbot_static_path}".format(
        certbot_static_path=certbot_static_path))

    run("letsencrypt certonly --webroot"
        " -w {certbot_static_path}"
        " -d {domain}".format(
            certbot_static_path=certbot_static_path,
            domain=env.domains[0],
        ))
    run("service nginx restart")
    # Cleanup letsencrypt
    run("rmdir {certbot_static_path}/.well-known/".format(
        certbot_static_path=certbot_static_path))
