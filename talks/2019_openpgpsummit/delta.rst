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

- No critical issues found in rPGP or RSA

- Two high risk, one medium risk issues fixed

- Some low-level ones pending

- More reviews upcoming

----

Delta Chat key verification
==================================

- "Setup-contact protocol"

- "Verified group-join protocol"

See section two of https://countermitm.readthedocs.io/

----

Setup-contact protocol
==================================

- QR-code based establishment of 1:1 chat

- Introduce e-mail addresses with each other

- Verifies keys in both directions

- Compatible to OpenPGP4FPR QR-codes

----

Verified group-join (Protocol)
==================================

Invite the scanning device to join chat group:

- Build on Setup-contact protocol

- Add invited/scanning device to group

- Gossip all verified keys

----

Verified Group (UX)
==================================

- Messages are always E2E-encrypted

- Safe against MITM/provider attacks

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

- Funding by OpenTechFund and NLnet

-----

Differences to Whatsapp/Telegram/...
===============================================

- No own servers, no tracking

- Decentralized, standards based

- Full-Rust based core allowing for
  quick & safe cross-platform developments.

- Open & Collaborative: >100 PRs merged per month

