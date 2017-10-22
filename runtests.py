#!/usr/bin/env python
import argparse
import os
import random
import signal
import subprocess
import sys

parser = argparse.ArgumentParser(description="Run the test suite, or some tests")
parser.add_argument('--coverage', "-c", action='store_true',
                    help="Use coverage")
parser.add_argument('--coverage-append', action='store_true',
                    help="Use 'append' with coverage run")
parser.add_argument('--skip-selenium', "-s", action='store_true',
                    help="Skip any Selenium tests")
parser.add_argument("--fast", "-f", action='store_true',
                    help="Fast test run - implies --skip-selenium")
parser.add_argument("--nokeepdb", action='store_true',
                    help="Don't preserve the test DB between runs.")
parser.add_argument('--parallel', dest='parallel', action='store_true',
                    help='Run tests using parallel processes.')
parser.add_argument("--hashseed", action='store',
                    help="Specify the PYTHONHASHSEED to use, otherwise a random one is chosen")
parser.add_argument("--verbosity", "-v", action='store', type=int,
                    help="Specify the verbosity to pass on to manage.py, 0 to 3. Pass 2 to print test names being run.")
parser.add_argument("--show-browser", action='store_true',
                    help="Display the browser window")
parser.add_argument("--firefox-binary", action='store',
                    help="Specify the path to the Firefox binary to use, otherwise default Firefox will be found")
parser.add_argument("--traceback-pages", action='store_true',
                    help="Display traceback pages when running tests (like when DEBUG=True)")


known_args, remaining_args = parser.parse_known_args()

remaining_options = [a for a in remaining_args if a.startswith('-')]
test_args = [a for a in remaining_args if not a.startswith('-')]


if known_args.fast:
    known_args.skip_selenium = True

if len(test_args) == 0:
    test_args = ["learnscripture.tests"]

if known_args.coverage:
    cmd = []
else:
    cmd = ["python"]
cmd += ["./manage.py", "test", "--noinput"]


if known_args.verbosity is not None:
    cmd += ['-v', str(known_args.verbosity)]

if known_args.parallel:
    cmd += ['--parallel']

if not known_args.nokeepdb:
    cmd += ['--keepdb']

if known_args.show_browser:
    os.environ['TESTS_SHOW_BROWSER'] = 'TRUE'

if known_args.firefox_binary:
    os.environ['TEST_SELENIUM_FIREFOX_BINARY'] = known_args.firefox_binary

if known_args.traceback_pages:
    os.environ['TEST_TRACEBACK_PAGES'] = 'TRUE'

cmd += remaining_options + test_args

if known_args.coverage:
    coverage_bin = subprocess.check_output(["which", "coverage"]).strip().decode('utf-8')
    cmd_prefix = [coverage_bin, "run"]
    if known_args.coverage_append:
        cmd_prefix.append("--append")
    cmd = cmd_prefix + cmd
else:
    if known_args.coverage_append:
        print("--coverage-append can only be used with --coverage")
        sys.exit(1)


sys.stdout.write(" ".join(cmd) + "\n")

if known_args.skip_selenium:
    os.environ['SKIP_SELENIUM_TESTS'] = "TRUE"

if known_args.hashseed:
    hashseed = known_args.hashseed
else:
    hashseed = os.environ.get('PYTHONHASHSEED', 'random')
    if hashseed == 'random':
        # Want PYTHONHASHSEED='random' to mimic production environment as much as
        # possible. However, this results in random failures which are difficult
        # to reproduce.

        # Therefore, we mimic the behaviour of PYTHONHASHSEED=random by setting a value
        # ourselves so that we can print that value (and set it later if needed)
        # Copied logic from here: https://bitbucket.org/hpk42/tox/src/f6cca79ba7f6522893ab720e1a5d09ab38fd3543/tox/config.py?at=default&fileviewer=file-view-default#config.py-579
        max_seed = 4294967295
        hashseed = str(random.randint(1, max_seed))

os.environ['PYTHONHASHSEED'] = hashseed
print("PYTHONHASHSEED=%s" % hashseed)


# Constraints:
# - we want Ctrl-C to work just the way
#   it does if we run manage.py directly, namely that
#   it exits cleanly.
#
# - if another process calls this one (e.g. fabric)
#   and user presses Ctrl-C, we want the same to happen.
#   Using os.exec results in fab script stopping,
#   but manage.py continuing somehow.
#
# - if user pressed Ctrl-C, we must return non-zero status code,
#   which is not what manage.py does

SIGINT_RECEIVED = False


def signal_handler(sig, f):
    global SIGINT_RECEIVED
    SIGINT_RECEIVED = True
    # No other action, just allow child to exit.


signal.signal(signal.SIGINT, signal_handler)

retcode = subprocess.call(cmd)
if SIGINT_RECEIVED:
    sys.exit(1)
else:
    sys.exit(retcode)
