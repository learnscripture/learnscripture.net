==============
 Server setup
==============

Most of the server setup was automated. Full steps used to set up the current
DigitalOcean machine are below:

(Completed 2016-11-30)


* Created account on DigitalOcean for webmaster@learnscripture.net

* Created droplet

  On: https://cloud.digitalocean.com/droplets
  Created droplet:

  Ubuntu 16.04.1 x64
  $5/month (512 Gb mem, 20 bB SSD, 1000 Gb transfer)

  Additional option: backups
  Location: New York

  Added my id_rsa.pub under name "luke@calvin"

  Droplet name: learnscripture

* Tested::

  $ ssh root@[ip address]

* Added the following entry to my /etc/hosts::

    104.236.55.8 learnscripture.digitalocean.com

* In fabfile.py, set env.hosts ['learnscripture.digitalocean.com']

* Ran initial deployment::

    $ fab secure
    $ fab provision
    $ fab create_project
    $ fab deploy


* Ran a few tweaks manually to make working on the box a bit easier::

    root@learnscripture> apt-get install joe
    root@learnscripture> chsh -s /bin/bash learnscripture

  Plus tweaks to ~/.inputrc

* Copied DB from old system.

  There are two databases - learnscripture and learnscripture_wordsuggestions.
  The first contains all the user data, and the bible texts etc.
  The second contains a large amount of generated data for supplying
  alternative words that users have to pick between when being tested.

  This second database was rebuilt, rather than being copied from the previous
  machine.

  Copied database to dev machine::

    $ fab get_db_dump_from_webfaction

  Noted filename, then::

    $ fab migrate_upload_db:../db_backups/[filename]

* Populated the word suggestion DB.

  This was done in a screen session to allow it to continue if SSH connection
  dropped::

    $ ssh learnscripture@learnscripture.digitalocean.com
    learnscripture@learnscripture> screen
    learnscripture@learnscripture> cd ~/webapps/learnscripture/versions/current/src/; . ../venv/bin/activate
    learnscripture@learnscripture> ./manage.py setup_bibleverse_suggestions

  Use Ctrl-a Ctrl-d to detach from screen, ``screen -r -d`` to reattach.

  (This took about a day to complete).

* Got the site working. Easiest way to test is to put an entry for
  'learnscripture.net' in /etc/hosts pointing to the new machine.

* Got previous hosts to change TTL to a few minutes, for a fast domain switch.

* After 48 hours, did the move for real:

  * stopped the old site, putting up "down for maintenance" sign
  * got a database dump with most recent data and uploaded to new machine, as above.
  * checked everything working on the new box.
  * got old provider to point DNS to new machine.
  * set up DNS records on DigitalOcean
  * switched DNS nameservers to DigitalOcean (previously WebFaction)

See also DNS_setup.rst

