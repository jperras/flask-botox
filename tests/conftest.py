import os, sys

# A bit of a hack, but let's add the current directory where this conftest is to
# sys.path, so that we can run `pytest` directly here without having to make the
# current project editable (`pip install -e`) or without having to invoke it
# with `python -m pytest` (which effectively does the sys.path add).
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import pytest

from flask import Flask
from flask_boto3 import Boto3


@pytest.fixture(scope="function")
def app():
    """Flask application object."""

    application = Flask("testing")
    application.config["BOTO3_REGION"] = "us-east-1"
    return application


@pytest.fixture(scope="function")
def ext(app):
    """Extension under test."""

    with app.app_context():
        yield Boto3(app)
