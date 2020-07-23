Server provisioning/upgrade
---------------------------

To upgrade to a major new version of the OS, it is usually better to start a new
VM, test it is all working, then transfer. Here is the process, assuming that we
are staying with the same provider (DigitalOcean). If moving to a new hosts some
steps will need to be changed.


1. Change the TTL on all learnscripture.net domains down to 1 hour (3600 seconds), so
   that the downtime caused by a new IP later on will be much quicker. This
   needs to be done at least X seconds before the actual switch over is planned,
   where X is the previous TTL, to give time for DNS propagation. So, if
   previous TTL is 86400 (1 day), this step needs to be done at least 1 day
   before go live of new server.

   Later on, at least 1 hour before switch over, we'll reduce it further to 5
   minutes.

2. Fetch old SSL certificates::

     fab download_letscencrypt_config

3. Create new VM:

   On DigitalOcean, last time (2020-05-09) this process was:

   From https://cloud.digitalocean.com/

   Create new droplet.

   Choose:

   - Latest Ubuntu LTS (last time - 20.04 (LTS) x64)
   - Starter plan
   - Smallest box (last time - $5/month, 1 Gb mem, 25 Gb disk, 1000 Gb transfer)
   - Any US datacenter (most users are in US)
   - IPv6 enabled
   - SSH authentication
     - luke@calvin SSH key selected (will need to upload one if there isn't one configured)

   - 1 droplet
   - Hostname: 'learnscripture' plus an incrementing number (last time: learnscripture2)

     Use incrementing numbers for each new VM, to ensure you don't confuse with
     previous one. This is not the same as the public domain name. Substitute
     this name wherever ``learnscripture2`` appears below.

   - Enable backups

4. Add new VM to /etc/hosts so that it can be accessed easily, using the IP address given
   e.g.::

   178.62.115.97 learnscripture2.digitalocean.com

   Check you can login with ``ssh root@learnscripture2.digitalocean.com``

5. Change ``env.hosts`` in fabfile to point to new VM. Remember that from now
   on it will use the new VM by default, unless ``-H`` flag is passed.

6. Upgrade versions of things, preferably to defaults for new distribution

   * Python version - see ``PYTHON_BIN`` in fabfile.py
   * Postgresql version - fabfile.py

6. Provision VM::

    $ fab secure
    $ fab provision

  If this fails update any dependencies, searching for new packages using
  ``apt search``.

  Then::

    $ fab upload_letsencrypt_conf
    $ fab create_project
    $ fab deploy


The next steps are a 'dry-run', that we will do before the real thing, to check
the process works.


7. Download DB from old server. Note use of ``-H`` flag to point to old
   server temporarily::

     fab -H learnscripture1.digitalocean.com get_live_db

   Note that this downloads only the primary database ``learnscripture``. In
   addition, there is ``learnscripture_wordsuggestions`` which consists of
   essentially static data. It is several Gb, so it can often be easier to
   rebuild this on the new server than to upload, and this ensures rebuilding is
   still working.

8. Upload DB to new server - make sure -H is correct, and change
   ``[filename]`` to the file downloaded in step 7::

     fab -H learnscripture2.digitalocean.com migrate_upload_db:[filename]

   This may return some errors, while still being successful. Restart webserver::

     fab -H learnscripture2.digitalocean.com start_webserver

9. Copy wordsuggestions DB from old to new server

   This is basically static data. There may be a lot of it, so can be
   transferred directly to avoid bandwidth issues:

   On old server::

     $ pg_dump -Fc -U learnscripture -O -f wordsuggestions.db learnscripture_wordsuggestions -v

   Then transfer to new - easiest it to upload the required ``id_rsa`` SSH key
   to the old server, then copy::

     $ rsync wordsuggestions.db learnscripture@<new_server_ip_address>

   Also, the related analysis data in ~/webapps/learnscripture/data should be copied over
   in case it needs to be used.

   On the new server::

     $ pg_restore -O -U learnscripture -c -d learnscripture_wordsuggestions wordsuggestions.db

   ALTERNATIVE:

   Alternatively we can rebuild the wordsuggestions DB from source data.

   This can be done in a screen session to allow it to continue if SSH connection
   dropped::

     $ ssh learnscripture@learnscripture2.digitalocean.com
     learnscripture2> screen
     learnscripture2> cd ~/webapps/learnscripture/versions/current/src/; . ../venv/bin/activate
     learnscripture2> ./manage.py run_suggestions_analyzers
     learnscripture2> ./manage.py setup_bibleverse_suggestions

   Use Ctrl-a Ctrl-d to detach from screen, ``screen -r -d`` to reattach.

   To avoid doing ``run_suggestions_analyzers``, files from
   /home/learnscripture/webapps/learnscripture/data on old machine can be copied
   over.

   HOWEVER: this process is currently problematic for some Bible versions for
   which we are not allowed to have the whole Bible text stored in our DB (ESV),
   and will fail for those.


# TODO copy usermedia from old to new. This is for CMS images

10. Use your local /etc/hosts to point learnscripture.net to the new server, and test
    the new site works as expected.

11. If everything works, prepare to do it for real

    - set the TTL to 5 minutes
    - wait for an hour for DNS to propagate

    - add a site notice

Now we'll repeat some steps, with changes:

12. Stop the old server::

      fab -H learnscripture1.digitalocean.com stop_webserver

    (This deliberately leaves the site returning an error, which is important
    for API calls - the /learn/ page will store up failed calls to later.)

13. Repeat step 7 - download DB from old server

14. Repeat step 8 - upload DB to new server.
    (step 9 does not need to be repeated, it is static data)

15. Repeat step 10 - check everything works

16. Switch DNS to the new server in the DigitalOcean control panel. Put DNS TTL
    back up to 86400


Done!

Ensure you remove entries from your local /etc/hosts so that you are seeing what
everyone else sees.

Post-migrate steps:

* Make sure letsencrypt is working::

      fab install_or_renew_ssl_certificate

* Upload the Mercurial VCS server to the new box::

    ssh learnscripture@learnscripture2.digitalocean.com
    mkdir ~/repos/learnscripture.net
    hg init ~/repos/learnscripture.net

  On dev box::

    hg push central

 
