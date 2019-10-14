Delta Chat & rPGP
=============================

OpenPGP Summit 2019, Berlin

holger @merlinux.eu @deltachat.de

.. image:: img/delta-cloud.png


----

E-mail based chatting
=====================

- Message relay over SMTP/IMAP only

- MIME mail format for interop

- DSNs for "sent/read" ticks

- Autocrypt/OpenPGP for E2E-encryption

**works suprisingly well :)**

.. image:: img/2019-01-chatlist.png
   :width: 120px

.. image:: img/2019-01-chat.png
   :width: 120px

.. image:: img/desktop-screenshot.png
   :width: 280 px

.. image:: img/ios_screenshot_chat_view.png
   :width: 110


-----

Privacy
==============

- No Delta servers, no address book upload

- E2E encryption implementing Autocrypt

- On top: "Verified groups" against MITM

----

Platform support
=====================

- Android mature & functional (Gplay/F-Droid)

- Desktop (Windows/Linux/macOS), maturing

- iOS in TestFlight, advancing quickly

----

Delta Chat Core in pure Rust
================================

- Interop C-API: https://c.delta.chat

- Stable JS/Python/Swift/Java bindings

- SMTP/IMAP/PGP/MIME not exposed to UIs


----

rPGP: Full-Rust OpenPGP
===================================

- Supports Autocrypt 1.1 OpenPGP primitives

- Runs well on Win/Lin/Mac/iOS/Android

- Apache/MIT dual-license

https://github.com/rpgp/rpgp

----

rPGP minimal code/API
===================================

- Provides primitives-API only, 12K Loc

- API design driven by Delta Chat/Autocrypt

- No trust or key management or storage

----

rPGP security status
===================================

- No critical issues found in rPGP or RSA

- Some issues found (and fixed, some pending)

- 26 page report

.. image:: img/security-review.png
   :width: 600

----

Delta Chat and active attacks
==================================

- "Setup-contact protocol"

- "Verified group-join protocol"

*"Don't talk with users about keys!"*

Section 2 of https://countermitm.readthedocs.io/

----

Setup-contact protocol
==================================

**QR-code based establishment of 1:1 chat**

- Introduce e-mail addresses with each other

- Verify keys in both directions

- Compatible to OpenPGP4FPR QR codes

----

Verified group-join (Protocol)
==================================

**QR-code based join into verified group**

- Executes Setup-contact protocol

- Then announces invited/scanning device to group

- i.e. Inviter signs and announces verified keys

----

Verified Group (UX)
==================================

- Messages are always E2E-encrypted

- Safe against MITM/provider attacks

- Key-verification chain between all members

**Avoids talking with users about keys!**

-----

Security of Desktop/Electron
==================================

- Only Rust-core parses incoming network packets

- Incoming html simplified to Plain etc.

- but: incoming message pipeline libetpan/C2Rust


----

Delta Chat 2019/2020
====================

- UX: Burner Accounts, WebRTC, Chat bots, Sticker, ...

- Rebase E2E-UX on EDD25519 + new sec review

- Launching a Chat bot ecosystem

- Safe mime-parser + sec review

- rPGP improvements & multi-language bindings

- Collaborations with non- and for-profit partners

Funding by OpenTechFund and NLnet

-----

Compare to Whatsapp/TG/...
===============================================

- No own servers, no tracking

- Decentralized and standards based

- Full-Rust core allows
  quick & safe x-platform developments.

- Open & Collaborative: >100 PRs merged per month

-----

PGPSummit Verified Group :)
====================================

.. image:: img/delta-cloud.png

.. image:: img/summit-invite.png
   :width: 300

contact:
holger@merlinux.eu
https://delta.chat

