import os, sys

# A bit of a hack, but let's add the current directory where this conftest is to
# sys.path, so that we can run `pytest` directly here without having to make the
# current project editable (`pip install -e`) or without having to invoke it
# with `python -m pytest` (which effectively does the sys.path add).
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import pytest
import types

from flask import Flask, g
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

    return Boto3(app)


def test_populate_application_context(app, ext):
    app.config["BOTO3_SERVICES"] = ["s3", "sqs"]

    with app.app_context():
        assert isinstance(ext.connections, dict)
        assert len(ext.connections) == 2
        assert isinstance(g._boto3, types.SimpleNamespace)
        assert len(g._boto3.connections) == 2


def test_instantiate_resource_connectors(app, ext, mocker):
    app.config["BOTO3_SERVICES"] = ["s3", "sqs", "dynamodb"]
    mocked_resource = mocker.patch("boto3.session.Session.resource", autospec=True)
    with app.app_context():
        ext.connections
        assert mocked_resource.call_count == 3
        assert sorted([i[0][1] for i in mocked_resource.call_args_list]) == sorted(
            app.config["BOTO3_SERVICES"]
        )


def test_pass_optional_params_through_conf_for_resources(app, ext, mocker):
    app.config["BOTO3_SERVICES"] = ["dynamodb"]
    app.config["BOTO3_OPTIONAL_PARAMS"] = {
        "dynamodb": {"args": ("eu-west-1"), "kwargs": {"use_ssl": True}}
    }
    mocked_resource = mocker.patch("boto3.session.Session.resource", autospec=True)
    with app.app_context():
        ext.connections
        mocked_resource.assert_called_once_with(
            mocker.ANY,  # Internal Session object
            "dynamodb",
            "eu-west-1",
            aws_access_key_id=None,
            aws_secret_access_key=None,
            use_ssl=True,
        )


def test_check_boto_clients_are_available(app, ext):
    app.config["BOTO3_SERVICES"] = ["s3", "sqs", "codedeploy", "codebuild"]
    with app.app_context():
        clients = ext.clients
        assert len(clients) == len(app.config["BOTO3_SERVICES"])


def test_populate_resources_application_context(app, ext):
    app.config["BOTO3_SERVICES"] = ["codebuild", "codedeploy"]
    with app.app_context():
        assert isinstance(ext.connections, dict)
        assert len(ext.connections) == 2
        assert isinstance(g._boto3, types.SimpleNamespace)
        assert len(g._boto3.connections) == 2


def test_instantiate_client_connectors(app, ext, mocker):
    app.config["BOTO3_SERVICES"] = ["codebuild", "codedeploy"]
    mocked_client = mocker.patch("boto3.session.Session.client")
    with app.app_context():
        ext.connections
        assert mocked_client.call_count == 2
        assert sorted([i[0][0] for i in mocked_client.call_args_list]) == sorted(
            app.config["BOTO3_SERVICES"]
        )


def test_pass_optional_params_through_conf_for_clients(app, ext, mocker):
    app.config["BOTO3_SERVICES"] = ["codepipeline"]
    app.config["BOTO3_OPTIONAL_PARAMS"] = {
        "codepipeline": {
            "args": ("eu-west-1"),
            "kwargs": {"use_ssl": True},
        }
    }
    mocked_client = mocker.patch("boto3.session.Session.client")
    with app.app_context():
        ext.connections
        mocked_client.assert_called_once_with(
            "codepipeline",
            "eu-west-1",
            aws_access_key_id=None,
            aws_secret_access_key=None,
            use_ssl=True,
        )


def test_check_boto_resources_are_available(app, ext):
    """Ensure that clients/resources are split correctly.

    SQS has a client, but codedeploy/codebuild are resource-only (but they still
    have clients).
    """

    app.config["BOTO3_SERVICES"] = ["sqs", "codedeploy", "codebuild"]
    with app.app_context():
        resources = ext.resources
        clients = ext.clients
        assert len(resources) == 1
        assert len(clients) == len(app.config["BOTO3_SERVICES"])
