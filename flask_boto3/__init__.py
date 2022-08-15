from types import SimpleNamespace
import boto3
from botocore.exceptions import UnknownServiceError
from flask import current_app, g


class Boto3(object):
    """
    Stores boto3 conectors inside Flask's application context for threadsafe
    usage.

    All connectors are stored inside the SimpleNamespace `_boto3` where the keys are
    the name of the services and the values their associated boto3 client.
    """

    def __init__(self, app=None):
        self.app = app
        if self.app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize the extension namespace & register teardown function.

        Parameters:

            app: The ``Flask`` application object that we are initializing
                 this extension against.
        """
        app.teardown_appcontext(self.teardown)

    def connect(self) -> dict:
        """
        Iterate through the application configuration and instantiate the
        services.
        """
        requested_services = set(
            svc.lower() for svc in current_app.config.get('BOTO3_SERVICES', [])
        )

        region = current_app.config.get('BOTO3_REGION')
        sess_params = {
            'aws_access_key_id': current_app.config.get('BOTO3_ACCESS_KEY'),
            'aws_secret_access_key': current_app.config.get('BOTO3_SECRET_KEY'),
            'profile_name': current_app.config.get('BOTO3_PROFILE'),
            'region_name': region
        }
        sess = boto3.session.Session(**sess_params)

        try:
            cns = {}
            for svc in requested_services:
                # Check for optional parameters
                params = current_app.config.get(
                    'BOTO3_OPTIONAL_PARAMS', {}
                ).get(svc, {})

                # Get session params and override them with kwargs
                # `profile_name` cannot be passed to clients and resources
                kwargs = sess_params.copy()
                kwargs.update(params.get('kwargs', {}))
                del kwargs['profile_name']

                # Override the region if one is defined as an argument
                args = params.get('args', [])
                if len(args) >= 1:
                    del kwargs['region_name']

                if not(isinstance(args, list) or isinstance(args, tuple)):
                    args = [args]

                # Create resource or client
                if svc in sess.get_available_resources():
                    cns.update({svc: sess.resource(svc, *args, **kwargs)})
                else:
                    cns.update({svc: sess.client(svc, *args, **kwargs)})
        except UnknownServiceError:
            raise
        return cns

    def teardown(self, exception):
        """
        Clean up extensions by closing connections and removing namespace.
        """
        if hasattr(g, '_boto3'):
            for name, conn in g._boto3.connections.items():
                if hasattr(conn, 'close') and callable(conn.close):
                    g._boto3.connections[name].close()

    @property
    def resources(self):
        c = self.connections
        return {k: v for k, v in c.items() if hasattr(c[k].meta, 'client')}

    @property
    def clients(self):
        """
        Get all clients (with and without associated resources)
        """
        clients = {}
        for k, v in self.connections.items():
            if hasattr(v.meta, 'client'):       # has boto3 resource
                clients[k] = v.meta.client
            else:                               # no boto3 resource
                clients[k] = v
        return clients

    @property
    def connections(self):
        if not hasattr(g, '_boto3'):
            g._boto3 = SimpleNamespace(connections=self.connect())
        return g._boto3.connections
