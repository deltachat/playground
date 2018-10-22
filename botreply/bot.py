from __future__ import print_function
import os
import time
import click
import deltachat

@click.command(cls=click.Group, context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--basedir", type=click.Path(),
              default=click.get_app_dir("deltabot"),
              envvar="DELTABOT_BASEDIR",
              help="directory where deltabot state is stored")
@click.version_option()
@click.pass_context
def bot_main(context, basedir):
    """access and manage Autocrypt keys, options, headers."""
    basedir = os.path.abspath(os.path.expanduser(basedir))
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    context.basedir = basedir


@click.command()
@click.argument("emailadr", type=str, required=True)
@click.argument("password", type=str, required=True)
@click.option("--overwrite", default=False, is_flag=True,
              help="overwrite existing configuration and account state")
@click.pass_context
def init(ctx, emailadr, password, overwrite):
    """initialize account info. """
    if "@" not in emailadr:
        fail(ctx, "invalid email address: {}".format(msg))

    acc = get_account(ctx.parent.basedir, remove=overwrite)
    if acc.is_configured():
        fail(ctx, "account already configured, use --overwrite")

    acc.configure(addr=emailadr, mail_pw=password)
    acc.start_threads()
    wait_configuration_progress(acc, 1000)
    acc.stop_threads()


@click.command()
@click.pass_context
def serve(ctx):
    """serve and react to incoming messages"""
    acc = get_account(ctx.parent.basedir)

    if not acc.is_configured():
        fail(ctx, "account not configured: {}".format(dbpath))

    acc.start_threads()
    try:
        Runner(acc).serve()
    finally:
        acc.stop_threads()


class Runner:
    def __init__(self, acc):
        self.acc = acc
        self.contacts = [acc.create_contact(email, name) for email, name in [
            ("holger@deltachat.de", None),
        ]]

    def check_message_subscriptions(self, msgid):
        msg = self.acc.get_message_by_id(msgid)
        print ("** creating chat with incoming msg", msg)
        chat = self.acc.create_chat_by_message(msg)
        chat.send_text_message("hi!")

    def dump_chats(self):
        print("*" * 80)
        chatlist = [self.acc.get_deaddrop_chat()] + self.acc.get_chats()
        for chat in chatlist:
            print ("chat id={}, name={}".format(chat.id, chat.get_name()))
            for sub in chat.get_contacts():
                print("  member:", sub.addr)
            for msg in chat.get_messages():
                print("  msg:", msg)

    def serve(self):
        print("start serve")
        while 1:
            self.dump_chats()
            ev = self.acc._evlogger.get_matching("DC_EVENT_MSGS_CHANGED")
            self.check_message_subscriptions(msgid=ev[2])


def wait_configuration_progress(account, target):
    while 1:
        evt_name, data1, data2 = \
            account._evlogger.get_matching("DC_EVENT_CONFIGURE_PROGRESS")
        if data1 >= target:
            print("** CONFIG PROGRESS {}".format(target), account)
            return data1


def fail(ctx, msg):
    click.secho(msg, fg="red")
    ctx.exit(1)


def get_account(basedir, remove=False):
    dbpath = os.path.join(basedir, "account.db")
    if remove and os.path.exists(dbpath):
        os.remove(dbpath)
    return deltachat.Account(dbpath)




bot_main.add_command(init)
bot_main.add_command(serve)


if __name__ == "__main__":
    bot_main()
