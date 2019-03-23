import base64
import hashlib
import pytest
import json
from testrun.app import create_app


@pytest.fixture
def app(tmpdir):
    config = {"token_create_user": 42}
    app = create_app(config)
    app.debug = True
    return app.test_client()


def test_newuser(app):
    r = app.post('/newtmpuser', json={"token_create_user": 10})
    assert r.status_code == 403
    r = app.post('/newtmpuser', json={"token_create_user": 42})
    assert r.status_code == 200
