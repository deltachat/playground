"""
User object for modifying virtual_mailbox and dovecot-users
"""

from __future__ import print_function

import os
import base64
import sys
import subprocess
import contextlib


class MailUser:

    def __init__(self, domain, opts,
                 path_virtual_mailboxes="/etc/postfix/virtual_mailboxes",
                 path_dovecot_users="/etc/dovecot/users"):
        self.domain = domain
        self.opts = opts
        self.path_virtual_mailboxes = path_virtual_mailboxes
        self.path_dovecot_users = path_dovecot_users

    def log(self, *args):
        print(*args)

    @contextlib.contextmanager
    def modify_lines(self, path, pm=False):
        self.log("reading", path)
        with open(path) as f:
            content = f.read().rstrip()
        lines = content.split("\n")
        old_lines = lines[:]
        yield lines
        if old_lines == lines:
            self.log("no changes", path)
            return
        content = "\n".join(lines)
        self.write_fn(path, content)
        if pm:
            self.postmap(path)

    def write_fn(self, path, content):
        if self.opts.dryrun:
            self.log("would write", path)
            return
        tmp_path = path + "_tmp"
        with open(tmp_path, "w") as f:
            f.write(content)
        self.log("writing", path)
        os.rename(tmp_path, path)

    def add_email(self, email):
        if not email.endswith(self.domain):
            raise ValueError("email {!r} is not on domain {!r}")
        with self.modify_lines(self.path_virtual_mailboxes, pm=True) as lines:
            for line in lines:
                assert not line.startswith(email), line
            # lines.append("# test account")
            lines.append("{} TMP".format(email))
        self.log("added {!r} to {}".format(lines[-1], self.path_virtual_mailboxes))

        clear_password, hash_pw = self.get_doveadm_pw()
        with self.modify_lines(self.path_dovecot_users) as lines:
            for line in lines:
                assert not line.startswith(email), line
            line = "{}:{}::::::".format(email, hash_pw)
            self.log("adding line to users")
            self.log(line)
            lines.append(line)
        self.log("email:", email)
        self.log("password:", clear_password)
        self.log(email, clear_password)

    def get_doveadm_pw(self):
        password = self.opts.password
        if not password:
            password = self.gen_password()
        hash_pw = subprocess.check_output(
            ["doveadm", "pw", "-s", "SHA512-CRYPT", "-p", password])
        return password, hash_pw.decode("ascii").strip()

    def gen_password(self):
        with open("/dev/urandom", "rb") as f:
            s = f.read(21)
        return base64.b64encode(s).decode("ascii")[:12]

    def postmap(self, path):
        print("postmap", path)
        if not self.opts.dryrun:
            subprocess.check_call(["postmap", path])

    def reload_services(self):
        if self.opts.dryrun:
            print("would reload services")
        else:
            subprocess.check_call(["service", "postfix", "reload"])
            subprocess.check_call(["service", "dovecot", "reload"])
