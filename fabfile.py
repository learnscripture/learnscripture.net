"""
Starter fabfile for deploying a Django project.

Designed for Webfaction, but should work on any similar hosting system.

Change all the things marked CHANGEME. Other things can be left at their
defaults if you are happy with the default layout.
"""

import posixpath

from fabric.api import run, local, abort, env, put, settings, cd, task
from fabric.decorators import runs_once
from fabric.contrib.files import exists
from fabric.context_managers import cd, lcd, settings, hide
from fabric.operations import get

# Host and login username:
env.hosts = ['cciw@cciw.co.uk']

# Directory where everything to do with this app will be stored on the server.
DJANGO_APP_ROOT = '/home/cciw/webapps/learnscripture_django'

# Directory where static sources should be collected.  This must equal the value
# of STATIC_ROOT in the settings.py that is used on the server.
STATIC_ROOT = '/home/cciw/webapps/learnscripture_static'

# Subdirectory of DJANGO_APP_ROOT in which project sources will be stored
SRC_SUBDIR = 'src'

# Subdirectory of DJANGO_APP_ROOT in which virtualenv will be stored
VENV_SUBDIR = 'venv'

# Python version
PYTHON_BIN = "python2.7"
PYTHON_PREFIX = "" # e.g. /usr/local  Use "" for automatic
PYTHON_FULL_PATH = "%s/bin/%s" % (PYTHON_PREFIX, PYTHON_BIN) if PYTHON_PREFIX else PYTHON_BIN


# Commands to stop and start the webserver that is serving the Django app.
# CHANGEME!  These defaults work for Webfaction
DJANGO_SERVER_STOP = posixpath.join(DJANGO_APP_ROOT, 'apache2', 'bin', 'stop')
DJANGO_SERVER_START = posixpath.join(DJANGO_APP_ROOT, 'apache2', 'bin', 'start')
DJANGO_SERVER_RESTART = None

src_dir = posixpath.join(DJANGO_APP_ROOT, SRC_SUBDIR)
venv_dir = posixpath.join(DJANGO_APP_ROOT, VENV_SUBDIR)

DB_USER, DB_NAME = "cciw_learnscripture", "cciw_learnscripture"


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
    with virtualenv(venv_dir):
        with cd(src_dir):
            run_venv("pip install -r requirements.txt")


def ensure_virtualenv():
    if exists(venv_dir):
        return

    with cd(DJANGO_APP_ROOT):
        run("virtualenv --no-site-packages --python=%s %s" %
            (PYTHON_BIN, VENV_SUBDIR))
        run("echo %s > %s/lib/%s/site-packages/projectsource.pth" %
            (src_dir, VENV_SUBDIR, PYTHON_BIN))


def ensure_src_dir():
    if not exists(src_dir):
        run("mkdir -p %s" % src_dir)
    with cd(src_dir):
        if not exists(posixpath.join(src_dir, '.hg')):
            run("hg init")


@task
def push_rev(rev):
    env.push_rev = rev


def push_sources():
    """
    Push source code to server
    """
    ensure_src_dir()
    push_rev = getattr(env, 'push_rev', None)
    if push_rev is None:
        push_rev = local("hg parents --template '{node}'", capture=True)
    local("hg push -f -r %(rev)s ssh://%(user)s@%(host)s/%(path)s" %
          dict(host=env.host,
               user=env.user,
               path=src_dir,
               rev=push_rev,
               ))
    with cd(src_dir):
        run("hg update %s" % push_rev)
    # Also need to sync files that are not in main sources VCS repo.
    local("rsync learnscripture/settings_priv.py cciw@cciw.co.uk:%s/learnscripture/settings_priv.py" % src_dir)


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
def webserver_stop():
    """
    Stop the webserver that is running the Django instance
    """
    run(DJANGO_SERVER_STOP)


@task
def webserver_start():
    """
    Startsp the webserver that is running the Django instance
    """
    run(DJANGO_SERVER_START)


@task
def webserver_restart():
    """
    Restarts the webserver that is running the Django instance
    """
    if DJANGO_SERVER_RESTART:
        run(DJANGO_SERVER_RESTART)
    else:
        with settings(warn_only=True):
            webserver_stop()
        webserver_start()


def build_static():
    assert STATIC_ROOT.strip() != '' and STATIC_ROOT.strip() != '/'
    # Before Django 1.4 we don't have the --clear option to collectstatic
    run("rm -rf %s/*" % STATIC_ROOT)

    with virtualenv(venv_dir):
        with cd(src_dir):
            run_venv("./manage.py collectstatic -v 0 --noinput")

    run("chmod -R ugo+r %s" % STATIC_ROOT)


@task
def first_deployment_mode():
    """
    Use before first deployment to switch on fake south migrations.
    """
    env.initial_deploy = True


def update_database():
    if getattr(env, 'no_db', False):
        return
    with virtualenv(venv_dir):
        with cd(src_dir):
            if getattr(env, 'initial_deploy', False):
                run_venv("./manage.py syncdb --all")
                run_venv("./manage.py migrate --fake --noinput")
            else:
                run_venv("./manage.py syncdb --noinput")
                run_venv("./manage.py migrate --noinput")


@task
def deploy():
    """
    Deploy project.
    """
    push_sources()
    install_dependencies()
    update_database()
    build_static()

    if not getattr(env, 'no_restarts', False):
        with settings(warn_only=True):
            webserver_stop()
        webserver_start()


@task
def manage_py_command(*commands):
    with virtualenv(venv_dir):
        with cd(src_dir):
            run_venv("./manage.py %s" % ' '.join(commands))


@task
def get_live_db():
    filename = "dump_%s.db" % DB_NAME
    run("pg_dump -Fc -U %s -O -o -f ~/%s %s" % (DB_USER, filename, DB_NAME))
    get("~/%s" % filename)


@task
def local_restore_from_dump(filename):
    local("sudo -u postgres pg_restore -O -U learnscripture -c -d learnscripture < %s" % filename)

