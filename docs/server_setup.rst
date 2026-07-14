Server provisioning/upgrade
---------------------------

In the future we might automate more of this, or move to containers for
deployment, but for now we are using a somewhat manual process. It only needs to
be done once every few years (basically depending on `Ubuntu LTS schedule
<https://ubuntu.com/about/release-cycle>`_).

To upgrade to a major new version of the OS, it is usually better to start a new
VM, test it is all working, then transfer. Here is the process, assuming that we
are staying with the same provider (DigitalOcean). If moving to a new hosts some
steps will need to be changed.


1. Change the TTL on all learnscripture.net A record (which points to the
   droplet) down to 1 hour (3600 seconds), so that the downtime caused by a new
   IP later on will be much quicker. This needs to be done at least X seconds
   before the actual switch over is planned, where X is the previous TTL, to
   give time for DNS propagation. So, if previous TTL is 86400 (1 day), this
   step needs to be done at least 1 day before go live of new server.

   Later on, at least 1 hour before switch over, we'll reduce it further to 5
   minutes.

2. Fetch old SSL certificates::

     fab download-letscencrypt-config

3. Create new VM:

   On DigitalOcean, last time (2026-07-12) this process was:

   From https://cloud.digitalocean.com/

   Create new droplet.

   Choose:

   - Latest Ubuntu LTS (last time - 26.04 (LTS) x64)
   - Starter plan
   - Smallest box (last time - Basic, 1 Gb mem, 25 Gb disk, 1000 Gb transfer,
     CPU: Premium AMD, $7/month)
   - Any US datacenter (most users are in US)
   - Public IPv6 address (in addition to IPv4)
   - SSH authentication
     - luke@calvin SSH key selected (will need to upload one if there isn't one configured)

   - 1 droplet
   - Hostname: 'learnscripture' plus an incrementing number (last time: learnscripture3)

     Use incrementing numbers for each new VM, to ensure you don't confuse with
     previous one. This is not the same as the public domain name. Substitute
     this name wherever ``learnscripture3`` appears below.

   - Enable backups

4. Add new VM to /etc/hosts so that it can be accessed easily, using the IP address given
   e.g.::

   178.62.115.97 learnscripture3.digitalocean.com

   Check you can login with ``ssh root@learnscripture3.digitalocean.com``

5. Change ``DEFAULT_HOST`` in ``fabfile.py`` to point to the new VPS. Remember that
   from now on it will use the new VPS by default, unless ``-H`` flag is passed.

   Check this has worked by doing ``fab root-hostname``

6. Upgrade versions of things, preferably to defaults for new distribution

   * Python version - see ``PYTHON_BIN`` in fabfile.py
   * Postgresql version:
     - fabfile.py - search for postgres references
     - devbox.json


6. Provision VM::

    $ fab initial_secure
    $ fab provision

  If this fails update any dependencies, searching for new packages using
  ``apt search``.

  Then::

    $ fab upload-letsencrypt-conf
    $ fab create-project

  Check you can login with ``learnscripture@…``

    $ fab deploy --test-host


The next steps are a 'dry-run', that we will do before the real thing, to check
the process works.


7. Download DB from old server. Note use of ``-H`` flag to point to old
   server temporarily::

     fab -H learnscripture2.digitalocean.com get-live-db

   Note that this downloads only the primary database ``learnscripture``. In
   addition, there is ``learnscripture_wordsuggestions`` which consists of
   essentially static data. It is several Gb, so it can often be easier to
   rebuild this on the new server than to upload, and this ensures rebuilding is
   still working - see below.

8. Upload DB to new server - make sure -H is correct, and change
   ``[filename]`` to the path to the file downloaded in step 7 (in ../db/backups)::

     fab -H learnscripture3.digitalocean.com migrate-upload-db [filename]

   This may return some errors, while still being successful. Restart webserver::

     fab -H learnscripture3.digitalocean.com start-webserver

9. Copy wordsuggestions DB from old to new server

   This is basically static data. There may be a lot of it, so can be
   transferred directly to avoid bandwidth issues:

   On old server::

     $ pg_dump -Fc -U learnscripture -O -f wordsuggestions.db learnscripture_wordsuggestions -v

   Then transfer to new. The easiest is to upload the required ``id_rsa`` SSH key
   to the old server::

     rsync ~/.ssh/id_rsa* learnscripture@learnscripture2.digitalocean.com:/home/learnscripture/

   On learnscripture2.digitalocean.com, after checking ``~/.ssh/`` for other
   clashes, copy these files to ``~/.ssh``.

   Then copy::

     $ rsync wordsuggestions.db learnscripture@<new_server_ip_address>:/home/learnscripture/wordsuggestions.db

   Also, the related analysis data in ~/webapps/learnscripture/data should be copied over
   in case it needs to be used::

     $ rsync -v --progress -r /home/learnscripture/webapps/learnscripture/data/ learnscripture@<new_server_ip_address>:/home/learnscripture/webapps/learnscripture/data/

   On the new server::

     $ pg_restore -O -U learnscripture -c -d learnscripture_wordsuggestions wordsuggestions.db

   ALTERNATIVE:

   Alternatively we can rebuild the wordsuggestions DB from source data.

   This can be done in a screen session to allow it to continue if SSH connection
   dropped::

     $ ssh learnscripture@learnscripture3.digitalocean.com
     learnscripture3> screen
     learnscripture3> cd ~/webapps/learnscripture/versions/current/src/; . ../venv/bin/activate
     learnscripture3> ./manage.py run_suggestions_analyzers
     learnscripture3> ./manage.py setup_bibleverse_suggestions

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

    - add a site notice about the downtime, preferably one in each language,
      but English is most important:

      https://learnscripture.net/admin/learnscripture/sitenotice/

Now we'll repeat some steps, with changes:

12. Stop the old server::

      fab -H learnscripture2.digitalocean.com stop-webserver

    (This deliberately leaves the site returning an error, which is important
    for API calls - the /learn/ page will store up failed calls to later.)

13. Repeat step 7 - download DB from old server

14. Repeat step 8 - upload DB to new server.
    (step 9 does not need to be repeated, it is static data)

15. Repeat step 10 - check everything works

16. Switch DNS to the new server in the DigitalOcean control panel. Put DNS TTL
    back up to 86400

17. Optionally, to make the old server proxy requests to the new, adjust the nginx
    config on the old server with this block replacing all ``location`` blocks::

      location / {
          proxy_pass https://NEW_SERVER_IP;

          # Preserve the original hostname
          proxy_set_header Host $host;

          # Preserve client information
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto https;
          proxy_set_header X-Forwarded-Host $host;

          # HTTP/1.1 for keepalive/WebSockets
          proxy_http_version 1.1;
          proxy_set_header Connection "";

          # If proxying directly to an IP with a certificate for the hostname,
          # use SNI and verify against the hostname.
          proxy_ssl_server_name on;
          proxy_ssl_name $host;

          # Optional timeouts
          proxy_connect_timeout 10s;
          proxy_send_timeout 60s;
          proxy_read_timeout 60s;
      }

    This will reduce downtime while DNS propagates.

    TODO automate this.

Done!

Ensure you remove entries from your local /etc/hosts so that you are seeing what
everyone else sees.

Post-migrate steps:

* Make sure letsencrypt is working::

      fab install-or-renew-ssl-certificate

* Change ``DEAFULT_HOST`` in fabfile.py back to ``learnscripture.net``
