from __future__ import annotations
import typing as t

if t.TYPE_CHECKING:
    from flask import Flask

from types import SimpleNamespace

import boto3
from flask import current_app, g


class Boto3(object):
    """
    Stores boto3 conectors inside Flask's application context for threadsafe
    usage.

    All connectors are stored inside the SimpleNamespace `_boto3` where the keys are
    the name of the services and the values their associated boto3 client.
    """

    def __init__(self, app: t.Optional[Flask] = None):
        """Create the extension object"""

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """
        Register teardown function

        Ensures that the extension cleans up after itself on app teardown.

        Parameters:

            app: The ``Flask`` application object that we are initializing
                 this extension against.
        """
        app.teardown_appcontext(self.teardown)

    def connect(self) -> dict:
        """
        Iterate through the application configuration and instantiate the
        services.

        Returns:
            A ``dict`` of all the connections, indexed by their name, e.g. ``s3``.
        """
        requested_services = set(
            service.lower() for service in current_app.config.get("BOTOX_SERVICES", [])
        )

        sess_params = {
            "aws_access_key_id": current_app.config.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": current_app.config.get("AWS_SECRET_ACCESS_KEY"),
            "profile_name": current_app.config.get("AWS_PROFILE"),
            "region_name": current_app.config.get("AWS_DEFAULT_REGION"),
        }
        sess = boto3.session.Session(**sess_params)
        cns = {}

        for service in requested_services:
            # Check for optional parameters provided in configuration
            # dictionary for each service we are connecting.
            params = current_app.config.get("BOTOX_OPTIONAL_PARAMS", {}).get(
                service, {}
            )

            # Get session params and override them with kwargs.
            # `profile_name` cannot be passed to clients and resources.
            kwargs = sess_params.copy()
            kwargs.update(params.get("kwargs", {}))
            del kwargs["profile_name"]

            # Override the region if one is defined as an argument
            args = params.get("args", [])
            if len(args) >= 1:
                del kwargs["region_name"]

            if not (isinstance(args, list) or isinstance(args, tuple)):
                args = [args]

            # Create resource or client
            # This may raise a boto3 ``UnknownServiceError`` if a service name
            # doesn't actually correspond to an available resource/client.
            if service in sess.get_available_resources():
                cns.update({service: sess.resource(service, *args, **kwargs)})
            else:
                cns.update({service: sess.client(service, *args, **kwargs)})

        return cns

    def teardown(self, _):
        """
        Clean up extensions by closing connections and removing namespace.
        """
        if hasattr(g, "_boto3"):
            for name, conn in g._boto3.connections.items():
                if hasattr(conn, "close") and callable(conn.close):
                    g._boto3.connections[name].close()

    @property
    def resources(self):
        """Return all resource-type boto3 connections"""
        c = self.connections
        return {k: v for k, v in c.items() if hasattr(c[k].meta, "client")}

    @property
    def clients(self):
        """Get all clients, with and without associated resources.
        """
        clients = {}
        for k, v in self.connections.items():
            if hasattr(v.meta, "client"):  # has boto3 resource
                clients[k] = v.meta.client
            else:  # no boto3 resource
                clients[k] = v
        return clients

    @property
    def connections(self):
        """Lazily initialize all defined connections on first property access"""
        if not hasattr(g, "_boto3"):
            g._boto3 = SimpleNamespace(connections=self.connect())
        return g._boto3.connections
