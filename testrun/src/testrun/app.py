import os
import pprint
from flask import Flask, request, jsonify


def create_app(config):
    app = Flask("testrun-account-server")

    @app.route('/newmailuser', methods=["POST"])
    def newuser():
        json_data = request.get_json()
        token = json_data['token_create_user']
        if token == config["token_create_user"]:
            return jsonify(resp="ok")
        else:
            return "token {} is invalid", 403

    return app

