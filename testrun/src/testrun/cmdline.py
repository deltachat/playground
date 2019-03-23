"""
script implementation of https://github.com/codespeaknet/sysadmin/blob/master/docs/postfix-virtual-domains.rst#add-a-virtual-mailbox

"""

from __future__ import print_function

DOMAIN = "testrun.org"

import os
import base64
import sys
import subprocess
import contextlib

from .user import User

from optparse import OptionParser

def main():
    parser = OptionParser(usage="%prog [options] FULL-EMAIL-ADDRESS")
    parser.add_option("-n", "--dry-run", action="store_true",
                      dest="dryrun", default=False,
                      help="don't write or change any files")
    parser.add_option("-p", "--password", dest="password", default=None,
                      help="password to set (cleartext)")
    options, args = parser.parse_args()
    if len(args) != 1:
        print("need email-address")
        sys.exit(1)
    adm = MailUser(DOMAIN, options)
    adm.add_email(args[0])
    adm.reload_services()

if __name__ == "__main__":
    main()

