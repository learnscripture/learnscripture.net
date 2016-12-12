#!/usr/bin/env python

import sys

if __name__ == '__main__':
    message = sys.argv[1]

    from fabfile import virtualenv, cd, run_venv, USER, HOST, env
    env.host_string = "%s@%s" % (USER, HOST)

    import pipes
    from fabfile import target
    with virtualenv(target.VENV_DIR):
        with cd(target.SRC_ROOT):
            run_venv("./manage.py send_notice_to_users " + pipes.quote(message))
