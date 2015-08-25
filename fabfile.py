"""
Starter fabfile for deploying a Django project.

Designed for Webfaction, but should work on any similar hosting system.

Change all the things marked CHANGEME. Other things can be left at their
defaults if you are happy with the default layout.
"""

from datetime import datetime
import os
import posixpath
import json

from fabric.api import run, local, env, task, runs_once, lcd
from fabric.contrib.files import exists, upload_template
from fabric.context_managers import cd, settings
from fabric.operations import get

join = os.path.join
rel = lambda *x: join(os.path.abspath(os.path.dirname(__file__)), *x)

USER = 'cciw'
HOST = 'learnscripture.net'

# Host and login username:
env.hosts = ['%s@%s' % (USER, HOST)]

# Subdirectory of DJANGO_APP_ROOT in which project sources will be stored
SRC_SUBDIR = 'src'

# Subdirectory of DJANGO_APP_ROOT in which virtualenv will be stored
VENV_SUBDIR = 'venv'

# Python version
PYTHON_BIN = "python2.7"
PYTHON_PREFIX = ""  # e.g. /usr/local  Use "" for automatic
PYTHON_FULL_PATH = "%s/bin/%s" % (PYTHON_PREFIX, PYTHON_BIN) if PYTHON_PREFIX else PYTHON_BIN

LOCAL_DB_BACKUPS = rel("..", "db_backups")


def secrets():
    thisdir = os.path.dirname(os.path.abspath(__file__))
    retval = json.load(open(os.path.join(thisdir, "config", "secrets.json")))
    # At least some passwords need to be bytes, not unicode objects
    retval = dict([(k, s if not isinstance(s, unicode) else s.encode('ascii')) for k, s in retval.items()])
    return retval


class Target(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        # Directory where everything to do with this app will be stored on the server.
        self.DJANGO_APP_ROOT = '/home/%s/webapps/%s_django' % (USER, self.APP_BASE_NAME)
        # Directory where static sources should be collected.  This must equal the value
        # of STATIC_ROOT in the settings.py that is used on the server.
        self.STATIC_ROOT = '/home/%s/webapps/%s_static' % (USER, self.APP_BASE_NAME)

        self.SRC_DIR = posixpath.join(self.DJANGO_APP_ROOT, SRC_SUBDIR)
        self.VENV_DIR = posixpath.join(self.DJANGO_APP_ROOT, VENV_SUBDIR)

        s = secrets()
        self.DB = {}
        self.DB['USER'] = s["%s_DB_USER" % self.NAME]
        self.DB['NAME'] = s["%s_DB_NAME" % self.NAME]
        self.DB['PASSWORD'] = s["%s_DB_PASSWORD" % self.NAME]
        self.OPBEAT_APP_ID = s['%s_OPBEAT' % self.NAME]['APP_ID']


PRODUCTION = Target(
    NAME="PRODUCTION",
    APP_BASE_NAME="learnscripture",
)

STAGING = Target(
    NAME="STAGING",
    APP_BASE_NAME="learnscripture_staging",
)

target = None


@task
def production():
    global target
    target = PRODUCTION


@task
def staging():
    global target
    target = STAGING


def virtualenv(venv_dir):
    """
    Context manager that establishes a virtualenv to use.
    """
    return settings(venv=venv_dir)


def run_venv(command, **kwargs):
    """
    Runs a command in a virtualenv (which has been specified using
    the virtualenv context manager
    """
    run("source %s/bin/activate" % env.venv + " && " + command, **kwargs)


def install_dependencies():
    if getattr(env, 'no_installs', False):
        return
    ensure_virtualenv()
    with virtualenv(target.VENV_DIR):
        with cd(target.SRC_DIR):
            run_venv("pip install -r requirements.txt")


def ensure_virtualenv():
    if exists(target.VENV_DIR):
        return

    with cd(target.DJANGO_APP_ROOT):
        run("virtualenv --no-site-packages --python=%s %s" %
            (PYTHON_BIN, VENV_SUBDIR))
        run("echo %s > %s/lib/%s/site-packages/projectsource.pth" %
            (target.SRC_DIR, VENV_SUBDIR, PYTHON_BIN))


def ensure_src_dir():
    if not exists(target.SRC_DIR):
        run("mkdir -p %s" % target.SRC_DIR)
    with cd(target.SRC_DIR):
        if not exists(posixpath.join(target.SRC_DIR, '.hg')):
            run("hg init")


@task
def push_rev(rev):
    env.push_rev = rev


@task
def push_secrets():
    local("rsync config/secrets.json %s@%s:%s/config/secrets.json" % (USER, HOST, target.SRC_DIR))


@task
def push_sources():
    """
    Push source code to server
    """
    ensure_src_dir()
    push_rev = getattr(env, 'push_rev', None)
    if push_rev is None:
        push_rev = local("hg id", capture=True).split(" ")[0].strip().strip("+")
    # if hg finds no changes it returns an error, which we want to ignore
    local("hg push -f -r %(rev)s ssh://%(user)s@%(host)s/%(path)s || true" %
          dict(host=env.host,
               user=env.user,
               path=target.SRC_DIR,
               rev=push_rev,
               ))
    with cd(target.SRC_DIR):
        run("hg update -r %s" % push_rev)

        assert run("hg id").split(" ")[0].strip().strip("+") == push_rev

    local("hg tag -f -r %s deploy-%s-$(date --iso-8601=seconds | tr ':' '-' | cut -f 1 -d '+')" %
          (push_rev, target.NAME.lower()))
    # Also need to sync files that are not in main sources VCS repo.
    push_secrets()

    # This config is shared, and rarely updates, so we push to
    # PRODUCTION.
    run("mkdir -p %s/etc" % PRODUCTION.VENV_DIR)


@task
def setup_supervisor():
    # One instance of supervisor, shared
    local("rsync config/start_supervisor.sh %s@%s:%s/bin" % (USER, HOST, PRODUCTION.VENV_DIR))
    run("chmod +x %s/bin/start_supervisor.sh" % PRODUCTION.VENV_DIR)
    run("mkdir -p %s/etc" % PRODUCTION.VENV_DIR)
    upload_template("config/supervisord.conf", "%s/etc/supervisord.conf" % PRODUCTION.VENV_DIR,
                    context=secrets())
    reload_supervisor()


@task
def reload_supervisor():
    supervisorctl("reread")
    supervisorctl("update")


@task
def restart_supervisor():
    """Normally use 'reload_supervisor' instead of this!"""
    if getattr(env, 'no_restarts', False):
        return

    run("%s/bin/start_supervisor.sh restart" % PRODUCTION.VENV_DIR)


@task
def no_restarts():
    """
    Call this first to ensure that no services are restarted by
    the following deploy actions.
    """
    env.no_restarts = True


@task
def no_installs():
    """
    Call first to skip installing anything.
    """
    env.no_installs = True


@task
def no_db():
    """
    Call first to skip upgrading DB
    """
    env.no_db = True


@task
def fake_migrations():
    env.fake_migrations = True


@task
def quick():
    no_restarts()
    no_installs()
    no_db()


@task
def stop_webserver():
    """
    Stop the webserver that is running the Django instance
    """
    supervisorctl("stop gunicorn_%s" % target.NAME.lower())


@task
def start_webserver():
    """
    Starts the webserver that is running the Django instance
    """
    supervisorctl("start gunicorn_%s" % target.NAME.lower())


@task
def restart_webserver():
    """
    Restarts the webserver that is running the Django instance
    """
    supervisorctl("restart gunicorn_%s" % target.NAME.lower())


@task
def build_static():
    assert target.STATIC_ROOT.strip() != '' and target.STATIC_ROOT.strip() != '/'
    with virtualenv(target.VENV_DIR):
        with cd(target.SRC_DIR):
            # django-compressor doesn't always find changes if we don't do this:
            run("touch learnscripture/static/css/learnscripture.less")

            # django-compressor doesn't always find
            run_venv("./manage.py collectstatic -v 0 --noinput")

    run("chmod -R ugo+r %s" % target.STATIC_ROOT)


def update_database():
    if getattr(env, 'no_db', False):
        return
    with virtualenv(target.VENV_DIR):
        with cd(target.SRC_DIR):
            if getattr(env, 'fake_migrations', False):
                run_venv("./manage.py migrate --noinput --fake")
            else:
                run_venv("./manage.py migrate --noinput")


def _assert_target():
    assert target is not None, "Use 'production' or 'staging' to set target"


@task
def deploy():
    """
    Deploy project.
    """
    _assert_target()
    push_sources()
    install_dependencies()
    update_database()
    build_static()

    if not getattr(env, 'no_restarts', False):
        restart_webserver()
        # Need to restart celeryd, as it will have old code.
        restart_celeryd()

    push_to_git_repo()
    register_deployment(".")


def push_to_git_repo():
    local("hg push git+ssh://git@bitbucket.org:spookylukey/learnscripture.net-git.git")


@task
def restart_celeryd():
    supervisorctl("restart celeryd_%s" % target.NAME.lower())


@task
def supervisorctl(*commands):
    with virtualenv(PRODUCTION.VENV_DIR):
        run_venv("supervisorctl %s" % " ".join(commands))


@task
def run_migrations():
    push_sources()
    update_database()


@task
def manage_py_command(*commands):
    with virtualenv(target.VENV_DIR):
        with cd(target.SRC_DIR):
            run_venv("./manage.py %s" % ' '.join(commands))


def make_django_db_filename(target):
    return "/home/cciw/db-%s.django.%s.pgdump" % (target.DB['NAME'], datetime.now().strftime("%Y-%m-%d_%H.%M.%S"))


def dump_db(target):
    filename = make_django_db_filename(target)
    run("pg_dump -Fc -U %s -O -o -f %s %s" % (target.DB['USER'], filename, target.DB['NAME']))
    return filename


@task
def get_live_db():
    filename = dump_db(PRODUCTION)
    local("mkdir -p %s" % LOCAL_DB_BACKUPS)
    return list(get(filename, local_path=LOCAL_DB_BACKUPS + "/%(basename)s"))[0]


def pg_restore_cmds(db, filename, clean=False):
    return [
        "pg_restore -O -U %s %s -d %s %s" %
        (db['USER'], " -c " if clean else "", db['NAME'], filename),
    ]


def db_restore_commands(db, filename):
    return [
        # DB might not exist, allow error
        """sudo -u postgres psql -U postgres -d template1 -c "DROP DATABASE %s;" | true """
        % db['NAME'],

        """sudo -u postgres psql -U postgres -d template1 -c "CREATE DATABASE %s;" """
        % db['NAME'],

        # User might already exist, allow error
        """sudo -u postgres psql -U postgres -d template1 -c "CREATE USER %s WITH PASSWORD '%s';" | true """
        % (db['USER'], db['PASSWORD']),

        """sudo -u postgres psql -U postgres -d template1 -c "GRANT ALL ON DATABASE %s TO %s;" """
        % (db['NAME'], db['USER']),

        """sudo -u postgres psql -U postgres -d template1 -c "ALTER USER %s CREATEDB;" """ %
        db['USER'],

    ] + pg_restore_cmds(db, filename)


@task
def local_restore_from_dump(filename):
    db = PRODUCTION.DB.copy()
    db['NAME'] = 'learnscripture'
    db['USER'] = 'learnscripture'
    db['PASSWORD'] = 'foo'

    for cmd in db_restore_commands(db, filename):
        local(cmd)


@task
def get_and_load_production_db():
    """
    Dump current production Django DB and load into dev environment
    """
    filename = get_live_db()
    local_restore_from_dump(filename)


@task
@runs_once
def register_deployment(src_path):
    with(lcd(src_path)):
        local("curl https://intake.opbeat.com/api/v1/organizations/ebb5516391a94a679eddcd11669d572b/apps/{0}/releases/".format(target.OPBEAT_APP_ID) +
              " -H 'Authorization: Bearer 1ee1a5ed2bbaee5e7c8e5bd5c43b7787d1f71327'"
              " -d rev=`hg log -l 1 -T '{gitnode}'`"
              " -d branch=`hg branch`"
              " -d status=completed")
