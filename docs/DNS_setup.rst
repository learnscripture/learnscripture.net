===========
 DNS setup
===========

The following DNS records are set up in DigitalOcean's DNS using
https://cloud.digitalocean.com/networking/domains


Domain learnscripture.net  -> learnscripture droplet

Additionally, email records are set up for sending and receiving email via
fastmail.com

Resulting zone file below::

    $ORIGIN learnscripture.net.
    $TTL 1800
    learnscripture.net. IN SOA ns1.digitalocean.com. hostmaster.learnscripture.net. 1657912340 10800 3600 604800 1800
    learnscripture.net. 86400 IN A 159.89.148.23
    www.learnscripture.net. 86400 IN CNAME learnscripture.net.
    fm1._domainkey.learnscripture.net. 43200 IN CNAME fm1.learnscripture.net.dkim.fmhosted.com.
    fm2._domainkey.learnscripture.net. 43200 IN CNAME fm2.learnscripture.net.dkim.fmhosted.com.
    fm3._domainkey.learnscripture.net. 43200 IN CNAME fm3.learnscripture.net.dkim.fmhosted.com.
    learnscripture.net. 86400 IN MX 10 in1-smtp.messagingengine.com.
    learnscripture.net. 86400 IN MX 20 in2-smtp.messagingengine.com.
    learnscripture.net. 86400 IN NS ns1.digitalocean.com.
    learnscripture.net. 86400 IN NS ns2.digitalocean.com.
    learnscripture.net. 86400 IN NS ns3.digitalocean.com.
    learnscripture.net. 3600 IN TXT v=spf1 include:spf.messagingengine.com ?all
