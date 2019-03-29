import os
import pprint
import random
from flask import Flask, request, jsonify
from .mailuser import MailUser


def create_app(config):
    app = Flask("testrun-account-server")

    @app.route('/newtmpuser', methods=["POST"])
    def newtmpuser():
        json_data = request.get_json()
        token = json_data['token_create_user']
        if token == config["token_create_user"]:
            mu = MailUser("testrun.org", dryrun=False,
                          path_dovecot_users=config["path_dovecot_users"],
                          path_virtual_mailboxes=config["path_virtual_mailboxes"],
            )
            tmpname = get_random_tmpname()
            tmp_email = "{}@testrun.org".format(tmpname)
            d = mu.add_email_account(tmp_email)
            return jsonify(d)
        else:
            return "token {} is invalid".format(config["token_create_user"]), 403

    return app


def get_random_tmpname():
    num = random.randint(0, 10000000000000000)
    return "tmp_{}".format(num)
