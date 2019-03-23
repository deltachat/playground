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

from .mailuser import MailUser

import click


@click.command(cls=click.Group, context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--basedir", type=click.Path(),
              default=click.get_app_dir("testrun"),
              envvar="TESTRUN_BASEDIR",
              help="directory where testrun tool state is stored")
@click.version_option()
@click.pass_context
def testrun_main(context, basedir):
    """testrun management command line interface. """
    basedir = os.path.abspath(os.path.expanduser(basedir))
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    context.basedir = basedir


@click.command()
@click.argument("emailadr", type=str, required=True)
@click.option("--domain", type=str, default="testrun.org",
              help="domain to be used")
@click.option("--password", type=str, default=None,
              help="if not specified, generate a random password")
@click.option("-n", "--dryrun", type=str,
              help="don't change any files, only show what would be changed.")
@click.pass_context
def adduser(ctx, emailadr, password, domain, dryrun):
    """add a e-mail user to postfix and dovecot configurations
    """
    if "@" not in emailadr:
        fail(ctx, "invalid email address: {}".format(msg))

    mu = MailUser(domain=domain, dryrun=dryrun)
    mu.add_user(emailadr=emailadr, password=password)


@click.command()
@click.pass_context
def info(ctx):
    """show information about configured account. """
    acc = get_account(ctx.parent.basedir)
    if not acc.is_configured():
        fail(ctx, "account not configured, use 'deltabot init'")

    info = acc.get_infostring()
    print(info)


@click.command()
@click.pass_context
def serve(ctx):
    """serve http account creation stuff """
    from .app import create_app
    config = {"token_create_user": "1773"}
    app = create_app(config)
    app.run()



testrun_main.add_command(adduser)
#bot_main.add_command(info)
testrun_main.add_command(serve)


if __name__ == "__main__":
    bot_main()

