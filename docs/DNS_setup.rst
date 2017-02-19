===========
 DNS setup
===========

The following DNS records are set up in DigitalOcean's DNS using
https://cloud.digitalocean.com/networking/domains


Domain learnscripture.net  -> learnscripture droplet

Additionally, email records are set up for sending and receiving email via mailgun.com

Resulting records:

===== ================================== =================================
Type  Name/col1                          Value/col2
===== ================================== =================================
A     @                                  46.101.26.30
CNAME email.learnscripture.net           mailgun.org.
MX    10                                 mxa.mailgun.org.
MX    10                                 mxb.mailgun.org.
TXT   learnscripture.net                 v=spf1 include:mailgun.org ~all
TXT   pic._domainkey.learnscripture.net  ... (see mailgun)
NS                                       ns1.digitalocean.com.
NS                                       ns2.digitalocean.com.
NS                                       ns3.digitalocean.com.
===== ================================== =================================


Zone file below::

    $ORIGIN learnscripture.net.
    $TTL 1800
    learnscripture.net. IN SOA ns1.digitalocean.com. hostmaster.learnscripture.net. 1480522351 10800 3600 604800 1800
    learnscripture.net. 1800 IN NS ns1.digitalocean.com.
    learnscripture.net. 1800 IN NS ns2.digitalocean.com.
    learnscripture.net. 1800 IN NS ns3.digitalocean.com.
    learnscripture.net. 1800 IN A 104.236.55.8
    learnscripture.net. 3600 IN TXT v=spf1 include:mailgun.org ~all
    pic._domainkey.learnscripture.net. 3600 IN TXT k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+pwGZ41+8s2Fi+JAVorLYzKDLkYsmMqrE/tr4CUTSdgr50qUanokvEtv62iybA7MqBrkvuERmPkWBCyk880rn+jpFIhxThDpDObO0/86tEvMBCaNIpAWiDJ7qLLBiTGgeTuZSrE87hQ2cllsmnend18Tp6anZxjoG3lZ2Gm6K3QIDAQAB
    email.learnscripture.net. 43200 IN CNAME mailgun.org.
    learnscripture.net. 1800 IN MX 10 mxa.mailgun.org.
    learnscripture.net. 1800 IN MX 10 mxb.mailgun.org.


Mailgun instructions are here:

https://mailgun.com/app/domains/learnscripture.net

