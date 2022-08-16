"""Basic extension functional tests
"""

import types

from flask import g
from flask_botox import Boto3


def test_application_factory(app):
    """Ensure the extension can be used in the app factory pattern."""

    app.config["BOTOX_SERVICES"] = ["s3", "sqs"]
    botox = Boto3()
    botox.init_app(app)

    with app.app_context():
        assert len(botox.connections) == 2


def test_populate_application_context(app, ext):
    app.config["BOTOX_SERVICES"] = ["s3", "sqs"]

    with app.app_context():
        assert isinstance(ext.connections, dict)
        assert len(ext.connections) == 2
        assert isinstance(g._boto3, types.SimpleNamespace)
        assert len(g._boto3.connections) == 2


def test_instantiate_resource_connectors(app, ext, mocker):
    app.config["BOTOX_SERVICES"] = ["s3", "sqs", "dynamodb"]
    mocked_resource = mocker.patch("boto3.session.Session.resource", autospec=True)
    with app.app_context():
        ext.connections
        assert mocked_resource.call_count == 3
        assert sorted([i[0][1] for i in mocked_resource.call_args_list]) == sorted(
            app.config["BOTOX_SERVICES"]
        )


def test_pass_optional_params_through_conf_for_resources(app, ext, mocker):
    app.config["BOTOX_SERVICES"] = ["dynamodb"]
    app.config["BOTOX_OPTIONAL_PARAMS"] = {
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
    app.config["BOTOX_SERVICES"] = ["s3", "sqs", "codedeploy", "codebuild"]
    with app.app_context():
        clients = ext.clients
        assert len(clients) == len(app.config["BOTOX_SERVICES"])


def test_populate_resources_application_context(app, ext):
    app.config["BOTOX_SERVICES"] = ["codebuild", "codedeploy"]
    with app.app_context():
        assert isinstance(ext.connections, dict)
        assert len(ext.connections) == 2
        assert isinstance(g._boto3, types.SimpleNamespace)
        assert len(g._boto3.connections) == 2


def test_instantiate_client_connectors(app, ext, mocker):
    app.config["BOTOX_SERVICES"] = ["codebuild", "codedeploy"]
    mocked_client = mocker.patch("boto3.session.Session.client")
    with app.app_context():
        ext.connections
        assert mocked_client.call_count == 2
        assert sorted([i[0][0] for i in mocked_client.call_args_list]) == sorted(
            app.config["BOTOX_SERVICES"]
        )


def test_pass_optional_params_through_conf_for_clients(app, ext, mocker):
    app.config["BOTOX_SERVICES"] = ["codepipeline"]
    app.config["BOTOX_OPTIONAL_PARAMS"] = {
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

    app.config["BOTOX_SERVICES"] = ["sqs", "codedeploy", "codebuild"]
    with app.app_context():
        resources = ext.resources
        clients = ext.clients
        assert len(resources) == 1
        assert len(clients) == len(app.config["BOTOX_SERVICES"])
