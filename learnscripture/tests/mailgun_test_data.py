# This POST request body was created using the Mailgun dashboard "Test Webhook"
# feature, captured using ngrok and then modified

MAILGUN_EXAMPLE_POST_DATA_FOR_BOUNCE_ENDPOINT = """--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="Message-Id"

<20130503182626.18666.16540@learnscripture.net>
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="X-Mailgun-Sid"

WyIwNzI5MCIsICJhbGljZUBleGFtcGxlLmNvbSIsICI2Il0=
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="attachment-count"

1
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="body-plain"


--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="code"

550
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="domain"

learnscripture.net
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="error"

5.1.1 The email account that you tried to reach does not exist. Please try
5.1.1 double-checking the recipient's email address for typos or
5.1.1 unnecessary spaces. Learn more at
5.1.1 http://support.example.com/mail/bin/answer.py
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="event"

bounced
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="message-headers"

[["Received", "by luna.mailgun.net with SMTP mgrt 8734663311733; Fri, 03 May 2013 18:26:27 +0000"], ["Content-Type", ["multipart/alternative", {"boundary": "eb663d73ae0a4d6c9153cc0aec8b7520"}]], ["Mime-Version", "1.0"], ["Subject", "Test bounces webhook"], ["From", "Bob <bob@learnscripture.net>"], ["To", "Alice <someone@gmail.com>"], ["Message-Id", "<20130503182626.18666.16540@learnscripture.net>"], ["List-Unsubscribe", "<mailto:u+na6tmy3ege4tgnldmyytqojqmfsdembyme3tmy3cha4wcndbgaydqyrgoi6wszdpovrhi5dinfzw63tfmv4gs43uomstimdhnvqws3bomnxw2jtuhusteqjgmq6tm@learnscripture.net>"], ["X-Mailgun-Sid", "WyIwNzI5MCIsICJhbGljZUBleGFtcGxlLmNvbSIsICI2Il0="], ["X-Mailgun-Variables", "{\"my_var_1\": \"Mailgun Variable #1\", \"my-var-2\": \"awesome\"}"], ["Date", "Fri, 03 May 2013 18:26:27 +0000"], ["Sender", "bob@learnscripture.net"]]
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="my-var-2"

awesome
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="my_var_1"

Mailgun Variable #1
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="recipient"

someone@gmail.com
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="signature"

1b9129d28ace9c78a3c90107008c6eb9a3d86e2d95a6a6351d80d81564efd315
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="timestamp"

1470097959
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="token"

e148497145dfec9664cf2855f2c6983205c15eee7bb6d49ab0
--f723ccea-a5e9-497a-806e-7088c837e9e0
Content-Disposition: form-data; name="attachment-1"; filename="message.mime"
Content-Type: application/octet-stream
Content-Length: 1195

Received: by luna.mailgun.net with SMTP mgrt 8734663311733; Fri, 03 May 2013
 18:26:27 +0000
Content-Type: multipart/alternative; boundary="eb663d73ae0a4d6c9153cc0aec8b7520"
Mime-Version: 1.0
Subject: Test bounces webhook
From: Bob <bob@learnscripture.net>
To: Alice <someone@gmail.com>
Message-Id: <20130503182626.18666.16540@learnscripture.net>
List-Unsubscribe: <mailto:u+na6tmy3ege4tgnldmyytqojqmfsdembyme3tmy3cha4wcndbgaydqyrgoi6wszdpovrhi5dinfzw63tfmv4gs43uomstimdhnvqws3bomnxw2jtuhusteqjgmq6tm@learnscripture.net>
X-Mailgun-Sid: WyIwNzI5MCIsICJhbGljZUBleGFtcGxlLmNvbSIsICI2Il0=
X-Mailgun-Variables: {"my_var_1": "Mailgun Variable #1", "my-var-2": "awesome"}
Date: Fri, 03 May 2013 18:26:27 +0000
Sender: bob@learnscripture.net

--eb663d73ae0a4d6c9153cc0aec8b7520
Mime-Version: 1.0
Content-Type: text/plain; charset="ascii"
Content-Transfer-Encoding: 7bit

Hi Alice, Do you exist on this domain?

--eb663d73ae0a4d6c9153cc0aec8b7520
Mime-Version: 1.0
Content-Type: text/html; charset="ascii"
Content-Transfer-Encoding: 7bit

<html>
                            <body>Hi Alice, Do you exist on this domain?
                            <br>
</body></html>
--eb663d73ae0a4d6c9153cc0aec8b7520--

--f723ccea-a5e9-497a-806e-7088c837e9e0--
""".replace(
    "\n", "\r\n"
)

MAILGUN_EXAMPLE_POST_DATA_FOR_BOUNCE_ENDPOINT_CONTENT_TYPE = (
    "multipart/form-data; boundary=f723ccea-a5e9-497a-806e-7088c837e9e0"
)
