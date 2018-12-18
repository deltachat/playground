import click
import smtplib
import time
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("smtphost", type=str, required=True)
@click.argument("login-user", type=str, required=True)
@click.argument("login-password", type=str, required=True)
@click.argument("target-email-addr", type=str, required=True)
def main(smtphost, login_user, login_password, target_email_addr):
    smtp = smtplib.SMTP_SSL(smtphost)
    smtp.login(login_user, login_password)

    msg1 = gen_mail_msg(From=login_user, To=[target_email_addr],
                        Subject="msg1")
    msg2 = gen_mail_msg(From=login_user, To=[target_email_addr], Subject="msg2",
                        replying=msg1["Message-Id"])
    msg3 = gen_mail_msg(From=login_user, To=[target_email_addr], Subject="msg3",
                        replying=msg1["Message-Id"])

    # BCC self
    recipients = [target_email_addr]
    if login_user not in recipients:
        recipients.append(login_user)

    def send_msg(m, recipients):
        res = smtp.send_message(m, to_addrs=recipients)
        print("message sent", m["Message-ID"], m.get("In-Reply-To"))
        return res

    send_msg(msg2, recipients)
    send_msg(msg3, recipients)
    input("type any word to send the thread-start message")
    send_msg(msg1, recipients)


def gen_mail_msg(From, To, Subject, replying=None, Date=0, dc=True):
    assert isinstance(To, (list, tuple))
    assert isinstance(Subject, str)

    msg = MIMEText("Hello i am the body of %r" % (Subject,))
    msg['From'] = From
    msg['To'] = ",".join(To)
    msg['Message-ID'] = make_msgid()
    msg['Subject'] = Subject
    if replying:
        msg["In-Reply-To"] = replying
    if dc:
        msg["Chat-Version"] = "1.0"
    Date = 0 if not Date else Date
    if isinstance(Date, int):
        Date = formatdate(time.time() + Date)
    msg['Date'] = Date
    return msg


if __name__ == "__main__":
    main()
