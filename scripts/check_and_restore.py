#!/usr/bin/env python

# There was been a rare problem, almost certainly with pgbouncer, that caused
# the whole site to hang. Since pgbouncer was hanging, not crashing, supervisord
# didn't know, and didn't restart it.
#
# So this script tests for the general symptom of an unresponsive site, and
# tries to fix things.
#
# Logging is done in crontab. The script prints nothing if all is OK

from datetime import datetime
from httplib import HTTPConnection
import os
import signal
import socket
import sys
import time

import psutil

TIMEOUT = 20

ATTEMPTS = 3
SLEEP_BETWEEN_ATTEMPTS = 20
USER = os.environ['USER']

TARGETS = {
    'development': {'APPNAME': 'learnscripture',
                    'DOMAIN': 'learnscripture.local',
                    'PORT': '8000',
                    },
    'staging': {'APPNAME': 'learnscripture_staging',
                'DOMAIN': 'staging.learnscripture.net',
                'PORT': '80',
                },
    'production': {'APPNAME': 'learnscripture',
                   'DOMAIN': 'learnscripture.net',
                   'PORT': '80',
                   },
    }
TARGET = None

SUPERVISORCTL = "/home/cciw/webapps/learnscripture_django/venv/bin/supervisorctl"
SUPERVISORD_STARTER = "/home/cciw/webapps/learnscripture_django/venv/bin/start_supervisor.sh"

def print_message(msg):
    sys.stdout.write(datetime.now().isoformat() + "  " + str(msg) + "\n")

def site_is_up():
    # we assume good, so that a bug in this code doesn't misdiagnose and cause
    # this script to do restarts unnecessarily. We only decide the site is down
    # for specific known errors.

    try:
        connection = HTTPConnection(TARGET['DOMAIN'], TARGET['PORT'], False, TIMEOUT)
        # We choose a URL that definitely needs the DB, to check the database is
        # working. We add a query param so that we can filter out in analytics,
        # and check this script is running
        connection.request("GET", "/about/?health_check=1", headers={'Host': TARGET['DOMAIN']})
        response = connection.getresponse()
        if response.status in [500, 502, 408]:
            print_message("Bad status: %d" % response.status)
            return False
        page = response.read()
    except socket.error as e:
        print_message("Socket error")
        print_message(e)
        return False
    except socket.timeout as e:
        print_message("Socket timeout")
        print_message(e)
        return False
    finally:
        try:
            connection.close()
        except:
            pass

    return True


def check(attempts=ATTEMPTS):
    for i in range(0, attempts):
        up = site_is_up()
        if up:
            return True
        print_message("Site not up, attempt %d of %d" % (i + 1, attempts))
        if i < attempts - 1:
            print_message("Sleeping for %d seconds" % SLEEP_BETWEEN_ATTEMPTS)
            time.sleep(SLEEP_BETWEEN_ATTEMPTS)
    return False


def start_supervisor():
    os.system("%s start" % SUPERVISORD_STARTER)

def stop_supervisor():
    os.system("%s stop" % SUPERVISORD_STARTER)


def restore():
    if TARGET['APPNAME'] == 'learnscripture_staging':
        # staging and production share a supervisord instance.  (Ideally they
        # would have separate supervisord, memcached and pgbouncer, but the
        # memory adds up).  We don't want testing of staging to take down
        # production, so we use an alternative strategy, and exit early
        print_message("Restarting using supervisorctl")
        os.system("%s restart rabbitmq_staging celeryd_staging apache_staging" % SUPERVISORCTL)
        return

    # Sometimes supervisord itself can get in a 'bad state' of some kind, so we
    # first shut it down, rather than assume it is in a good state.
    try:
        print_message("Stopping supervisord")
        stop_supervisor()
    except (Exception,), e:
        print_message(str(e))

    # Sometimes the problem is or could be a deadlocked cronjob, or some process
    # that is triggering WebFaction's process killer due to high memory usage.
    # Let's first kill everything that could be causing a problem.
    try:
        kill_cronjob_processes()
    except (Exception,), e:
        print_message(str(e))
    # (This comes after stop_supervisor(), because some processes under
    # supervisor's control could be misclassified as cronjob processes).

    # Now restart
    try:
        print_message("Starting supervisord")
        start_supervisor()
    except (Exception,), e:
        print_message(str(e))

    print_message("Doing: supervisorctl start all")
    os.system("%s start all" % SUPERVISORCTL)

    # There is also the apache process, which currently is not under the control
    # of supervisord. It has its own cronjob to restart it, so we leave it
    # alone.

    # If still not up, the next time this script is called may fix things,
    # otherwise we're out of options.


def kill_cronjob_processes():
    for ps in get_learnscripture_cronjob_processes():
        print_message("Terminating process %d %s" % (ps.pid, ' '.join(ps.cmdline)))
        ps.terminate()

    # In case any didn't die
    time.sleep(5)
    for ps in get_learnscripture_cronjob_processes():
        print_message("Killing process %d %s" % (ps.pid, ' '.join(ps.cmdline)))
        ps.send_signal(signal.SIGKILL)

def get_learnscripture_cronjob_processes():
    # We only target ones that have 'manage.py' in cmdline. Importantly, that
    # excludes this script!
    return [ps for ps in get_controllable_processes()
            if (TARGET['APPNAME'] in ps.getcwd() or TARGET['APPNAME'] in ' '.join(ps.cmdline))
            and ('manage.py' in ' '.join(ps.cmdline))]

def get_controllable_processes():
    l = []
    for ps in psutil.process_iter():
        if ps.username == USER:
            # Check we can get CWD, because we need that.
            try:
                cwd = ps.getcwd()
            except psutil.AccessDenied:
                continue
            l.append(ps)
    return l

if __name__ == '__main__':
    TARGET = TARGETS[sys.argv[1]]

    if not check():
        print_message("Attempting restore")
        restore()
