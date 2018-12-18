

To get started
--------------

at best you are running inside an virtualenv, beware of SUDO!::

    pip install imapclient click
    python3 move_imap.py IMAPHOST LOGINUSER LOGINPASSWORD

this will start watching both INBOX and DeltaChat folder
and perform message moves from INBOX to DeltaChat:

- if the top level message is determined to have come from Delta
- if a parent message was already moved
- if no top level message could be determined but the last 4 messages
  up (along the in-reply-to-chain) were from Delta

You can specify --pendingtimeout=SECS.  Messages which were fetched
longer than "seconds" ago but who have no parent message will
be left in the INBOX and not considered for moving after the timeout.


Sending test messages (out of order)
------------------------------------

type::

    python3 send_unordered_message.py SMTPHOST LOGINUSER LOGINPASSWORD TARGETEMAIL

this does:

- create msg1
- create msg2 with in-reply-to msg1
- smtp-send msg2, waits for key
- smtp-send msg1




