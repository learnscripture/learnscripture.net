"""
Starter fabfile for deploying a Django project.

Designed for Webfaction, but should work on any similar hosting system.

Change all the things marked CHANGEME. Other things can be left at their
defaults if you are happy with the default layout.
"""

import os
import posixpath
import simplejson

from fabric.api import run, local, abort, env, put, settings, cd, task
from fabric.decorators import runs_once
from fabric.contrib.files import exists, upload_template
from fabric.context_managers import cd, lcd, settings, hide
from fabric.operations import get

# Host and login username:
env.hosts = ['cciw@cciw.co.uk']


# Subdirectory of DJANGO_APP_ROOT in which project sources will be stored
SRC_SUBDIR = 'src'

# Subdirectory of DJANGO_APP_ROOT in which virtualenv will be stored
VENV_SUBDIR = 'venv'

# Python version
PYTHON_BIN = "python2.7"
PYTHON_PREFIX = "" # e.g. /usr/local  Use "" for automatic
PYTHON_FULL_PATH = "%s/bin/%s" % (PYTHON_PREFIX, PYTHON_BIN) if PYTHON_PREFIX else PYTHON_BIN

RABBITMQ_SRC = "http://www.rabbitmq.com/releases/rabbitmq-server/v2.8.1/rabbitmq-server-generic-unix-2.8.1.tar.gz"
RABBITMQ_DIR = "rabbitmq_server-2.8.1"
ERLANG_SRC = "http://www.erlang.org/download/otp_src_R15B01.tar.gz"


class Target(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        # Directory where everything to do with this app will be stored on the server.
        self.DJANGO_APP_ROOT = '/home/cciw/webapps/%s_django' % self.APP_BASE_NAME
        # Directory where static sources should be collected.  This must equal the value
        # of STATIC_ROOT in the settings.py that is used on the server.
        self.STATIC_ROOT = '/home/cciw/webapps/%s_static' % self.APP_BASE_NAME

        self.src_dir = posixpath.join(self.DJANGO_APP_ROOT, SRC_SUBDIR)
        self.venv_dir = posixpath.join(self.DJANGO_APP_ROOT, VENV_SUBDIR)
        self.conf_dir = posixpath.join(self.src_dir, self.CONF_SUBDIR)


PRODUCTION = Target(
    NAME = "PRODUCTION",
    APP_BASE_NAME = "learnscripture",
    DB_USER = "cciw_learnscripture",
    DB_NAME = "cciw_learnscripture",
    CONF_SUBDIR = "config/production",
)

STAGING = Target(
    NAME = "STAGING",
    APP_BASE_NAME = "learnscripture_staging",
    DB_USER = "cciw_learnscripture_staging",
    DB_NAME = "cciw_learnscripture_staging",
    CONF_SUBDIR = "config/staging",
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


def _download(src):
    run("wget --progress=dot -c %s" % src)


def _tarball_stem_name(fname):
    for s in ('.tar', '.bz2', '.gz', '.tgz'):
        fname = fname.replace(s, '')
    return fname


def _download_and_unpack(tarball_src):
    """
    Downloads and unpacks a tarball, and returns the directory name it was
    unpacked into.
    """
    _download(tarball_src)
    fname = tarball_src.split('/')[-1]
    run("tar -xzf %s" % fname)
    # Big assumption here, but holds for all our sources:
    dirname = _tarball_stem_name(fname)
    return dirname


@task
def install_erlang():
    # install into $HOME/.local, since we only need it once.
    with cd('/home/cciw/tmpstore/build'):
        dirname = _download_and_unpack(ERLANG_SRC)
        with cd(dirname):
            run("./configure --prefix=/home/cciw/.local"
                "&& make"
                "&& make install")


@task
def full_rabbitmq_setup():
    install_rabbitmq()
    setup_rabbitmq_conf()
    supervisorctl("restart rabbitmq_%s" % target.NAME.lower())
    setup_rabbitmq_users()

@task
def install_rabbitmq():
    # install into venv dir, different instance for STAGING and PRODUCTION
    rabbitmq_base = "%s/lib/" % target.venv_dir
    with cd(rabbitmq_base):
        _download_and_unpack(RABBITMQ_SRC)

@task
def setup_rabbitmq_conf():
    rabbitmq_full = "%s/lib/%s" % (target.venv_dir, RABBITMQ_DIR)
    # Need to fix as per these instructions:
    # http://community.webfaction.com/questions/2366/can-i-use-rabbit-mq-on-the-shared-servers
    local("rsync config/erl_inetrc cciw@cciw.co.uk:/home/cciw/.erl_inetrc")
    run("mkdir -p /home/cciw/.local/etc")
    local("rsync config/hosts cciw@cciw.co.uk:/home/cciw/.local/etc/")

    # Custom rabbitmq-env file
    local("rsync config/%s/rabbitmq-env cciw@cciw.co.uk:%s/sbin" % (target.NAME.lower(), rabbitmq_full))


@task
def setup_rabbitmq_users():
    rabbitmq_full = "%s/lib/%s" % (target.venv_dir, RABBITMQ_DIR)

    rabbitmq_user = target.APP_BASE_NAME
    rabbitmq_vhost = rabbitmq_user
    run("%s/sbin/rabbitmqctl add_user %s %s" % (
            rabbitmq_full,
            rabbitmq_user,
            secrets()["%s_RABBITMQ_PASSWORD" % target.NAME]
            )
        )
    run("%s/sbin/rabbitmqctl add_vhost %s" % (
            rabbitmq_full,
            rabbitmq_vhost,
            )
        )
    run("%s/sbin/rabbitmqctl set_permissions -p %s %s '.*' '.*' '.*'" % (
            rabbitmq_full,
            rabbitmq_vhost,
            rabbitmq_user,
            )
        )


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
    with virtualenv(target.venv_dir):
        with cd(target.src_dir):
            run_venv("pip install -r requirements.txt")


def ensure_virtualenv():
    if exists(target.venv_dir):
        return

    with cd(target.DJANGO_APP_ROOT):
        run("virtualenv --no-site-packages --python=%s %s" %
            (PYTHON_BIN, VENV_SUBDIR))
        run("echo %s > %s/lib/%s/site-packages/projectsource.pth" %
            (target.src_dir, VENV_SUBDIR, PYTHON_BIN))


def ensure_src_dir():
    if not exists(target.src_dir):
        run("mkdir -p %s" % target.src_dir)
    with cd(target.src_dir):
        if not exists(posixpath.join(target.src_dir, '.hg')):
            run("hg init")


@task
def push_rev(rev):
    env.push_rev = rev


def secrets():
    thisdir = os.path.dirname(os.path.abspath(__file__))
    return simplejson.load(open(os.path.join(thisdir, "config", "secrets.json")))


@task
def push_secrets():
    local("rsync config/secrets.json cciw@cciw.co.uk:%s/config/secrets.json" % target.src_dir)


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
               path=target.src_dir,
               rev=push_rev,
               ))
    with cd(target.src_dir):
        run("hg update %s" % push_rev)

        assert run("hg parents --template '{node}'").strip() == push_rev

    # Also need to sync files that are not in main sources VCS repo.
    push_secrets()

    # This config is shared, and rarely updates, so we push to
    # PRODUCTION.
    run("mkdir -p %s/etc" % PRODUCTION.venv_dir)
    upload_template("config/pgbouncer_users.txt", "%s/etc/pgbouncer_users.txt" % PRODUCTION.venv_dir, context=secrets())


@task
def setup_supervisor():
    # One instance of supervisor, shared
    local("rsync config/start_supervisor.sh cciw@cciw.co.uk:%s/bin" % PRODUCTION.venv_dir)
    run("chmod +x %s/bin/start_supervisor.sh" % PRODUCTION.venv_dir)
    run("mkdir -p %s/etc" % PRODUCTION.venv_dir)
    upload_template("config/supervisord.conf", "%s/etc/supervisord.conf" % PRODUCTION.venv_dir,
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

    run("%s/bin/start_supervisor.sh restart" % PRODUCTION.venv_dir)


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
    with virtualenv(target.venv_dir):
        with cd(target.src_dir):
            run_venv("./manage.py collectstatic -v 0 --noinput")

    run("chmod -R ugo+r %s" % target.STATIC_ROOT)


@task
def first_deployment_mode():
    """
    Use before first deployment to switch on fake south migrations.
    """
    env.initial_deploy = True


def update_database():
    if getattr(env, 'no_db', False):
        return
    with virtualenv(target.venv_dir):
        with cd(target.src_dir):
            if getattr(env, 'initial_deploy', False):
                run_venv("./manage.py syncdb --all")
                run_venv("./manage.py migrate --fake --noinput")
            else:
                run_venv("./manage.py syncdb --noinput")
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

@task
def restart_celeryd():
    supervisorctl("restart celeryd_%s" % target.NAME.lower())

@task
def supervisorctl(*commands):
    with virtualenv(PRODUCTION.venv_dir):
        run_venv("supervisorctl %s" % " ".join(commands))


@task
def run_migrations():
    push_sources()
    update_database()


@task
def manage_py_command(*commands):
    with virtualenv(target.venv_dir):
        with cd(target.src_dir):
            run_venv("./manage.py %s" % ' '.join(commands))


@task
def get_live_db():
    filename = "dump_%s.db" % PRODUCTION.DB_NAME
    run("pg_dump -Fc -U %s -O -o -f ~/%s %s" % (PRODUCTION.DB_USER, filename, PRODUCTION.DB_NAME))
    get("~/%s" % filename)


@task
def local_restore_from_dump(filename):
    # DB might not exist, allow error
    local("""sudo -u postgres psql -U postgres -d template1 -c "DROP DATABASE learnscripture;" | true """)
    local("""sudo -u postgres psql -U postgres -d template1 -c "CREATE DATABASE learnscripture;" """)
    # User might already exist, allow error
    local("""sudo -u postgres psql -U postgres -d template1 -c "CREATE USER learnscripture WITH PASSWORD 'foo';" | true """,)
    local("""sudo -u postgres psql -U postgres -d template1 -c "GRANT ALL ON DATABASE learnscripture TO learnscripture;" """)
    local("""sudo -u postgres psql -U postgres -d template1 -c "ALTER USER learnscripture CREATEDB;" """)

    local("pg_restore -O -U learnscripture -d learnscripture %s" % filename)

