Delta Chat & rPGP
=============================

OpenPGP Summit 2019, Berlin

holger @merlinux.eu @deltachat.de

.. image:: img/delta-logo.png


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

- no Delta servers, no address book upload

- e2e encryption implementing Autocrypt

- on top: "Verified groups" against MITM

----

Platform support
=====================

- Android mature & functional (Gplay/F-Droid)

- Desktop (Windows/Linux/macOS), maturing

- iOS in TestFlight, advancing quickly

----

Core lib in pure Rust
==========================

- Interop C-API: https://c.delta.chat

- Stable JS/Python/Swift/Java bindings

- SMTP/IMAP/PGP *not exposed*


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

- No trust, key management or storage

----

rPGP security status
===================================

Independent security review mid 2019:

- no critical issues found in rPGP or RSA

- two high risk, one medium risk issues fixed

- some low-level ones pending

- more reviews upcoming

----

Delta Chat key verification
==================================

- "setup contact protocol"

- "verified group-join protocol"

See section two of https://countermitm.readthedocs.io/

----

Setup-Contact protocol
==================================

- QR-code based establishment of 1:1 chat

- Introduce e-mail addresses with each other

- Verifies keys in both directions

- compatible to OpenPGP4FPR QR codes

----

Verified Groups (Protocol)
==================================

Invite the scanning device to join Chat group:

- Build on Setup-Contact protocol

- Add invited/scanning device to group

- Gossip all verified keys

----

Verified Group (UX)
==================================

- Messages are always E2E-encrypted

- safe against MITM/provider attacks

- Key-verification chain between all members!

**No talking with users about keys!**

-----

Delta Chat 2019/2020
====================

- UX: Burner Accounts, WebRTC, Chat bots, Sticker, ...

- Rebase E2E-UX on key-change history

- Safe mime-parser, security review

- rPGP completion & multi-language bindings

- Collaborations with non- and for-profit partners

- Funding by OpenTechFund and NLNET

-----

Differences to Whatsapp/Telegram/...
===============================================

- No own servers, no tracking

- Decentralized, standards based

- Full-Rust based core allowing for
  quick & safe cross-platform developments.

- Open & Collaborative: >100 PRs merged per month

