#!/usr/bin/env python

# There was been a rare problem, almost certainly with pgbouncer, that caused
# the whole site to hang. Since pgbouncer was hanging, not crashing, supervisord
# didn't know, and didn't restart it.
#
# So this script tests for the general symptom of an unresponsive site, and
# tries to fix things.
#
# Logging is done in crontab. The script prints nothing if all is OK
#
# We use only stdlib imports

from datetime import datetime
from httplib import HTTPConnection
import os
import socket
import sys
import time

TIMEOUT = 20

ATTEMPTS = 3
SLEEP_BETWEEN_ATTEMPTS = 20

def print_message(msg):
    sys.stdout.write(datetime.now().isoformat() + "  " + str(msg) + "\n")

def site_is_up():
    # we assume good, so that a bug in this code doesn't misdiagnose and cause
    # this script to do restarts unnecessarily. We only decide the site is down
    # for specific known errors.

    try:
        #connection = HTTPConnection('localhost', 8000, False, TIMEOUT)
        connection = HTTPConnection('learnscripture.net', 80, False, TIMEOUT)
        # We choose a URL that definitely needs the DB, to check the database is
        # working. We add a query param so that we can filter out in analytics,
        # and check this script is running
        connection.request("GET", "/about/?health_check=1", headers={'Host':'learnscripture.net'})
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


SUPERVISORCTL = "/home/cciw/webapps/learnscripture_django/venv/bin/supervisorctl"
SUPERVISORD = "/home/cciw/webapps/learnscripture_django/venv/bin/supervisorctl"
SUPERVISORD_STARTER = "/home/cciw/webapps/learnscripture_django/venv/bin/start_supervisor.sh"


def start_supervisor():
    os.system("%s start" % SUPERVISORD_STARTER)


def restore():
    # First, try to start supervisor
    try:
        print_message("Starting supervisord")
        start_supervisord()
    except:
        pass

    time.sleep(10) # 10 seconds should be more than enough to get services up
    if not check(attempts=1):
        print_message("Site still not up")
        # supervisord was probably running already.
        # Try shutting down and restarting all services
        print_message("Doing: supervisorctl restart all")
        os.system("%s restart all" % SUPERVISORCTL)

        # If still not up, the next time this script is called may fix things,
        # otherwise we're out of options.


if __name__ == '__main__':
    if not check():
        print_message("Attempting restore")
        restore()


