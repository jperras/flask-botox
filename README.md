# flask-botox

Flask extension that ties [boto3](https://github.com/boto/boto3) connectors to the application context.
To be used with Python 3.7+.

## Install

* Via `pip`:
    ```bash
    $ pip install flask-botox
    ```

* Locally with [Poetry](https://python-poetry.org) for development purposes:
    ```bash
    $ git clone https://github.com/jperras/flask-botox.git
    $ cd flask-botox
    $ poetry install
    ```

## How-to

The main class `flask_botox.Boto3` takes a Flask application as its contructor's parameter:

```python
from flask import Flask
from flask_botox import Boto3
app = Flask(__name__)
app.config["BOTOX_SERVICES"] = ["s3", "ses", "sqs"]

botox = Boto3(app)
```

The application factory pattern for extensions is also valid:

```python
from flask import Flask
from flask_botox import Boto3

botox = Boto3()

app = Flask(__name__)
app.config["BOTOX_SERVICES"] = ["s3", "ses", "sqs"]

botox.init_app(app)

```


Then `boto3`'s clients and resources will be available as properties within the application context:

```python
>>> with app.app_context():
        print(botox.clients)
        print(botox.resources)
{'s3': <botocore.client.S3 object at 0x..>}
{'s3': s3.ServiceResource()}
```

## Configuration

Flask-botox uses several keys from a Flask configuration objects to customize its behaviour. Any of the `AWS_*` keys are _not_ required; if they are not specified, then the usual `boto3` configuration parameter rules will apply.

- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` : The AWS credentials. Note that it's not a good idea to put your secret access key in a configuration file, but it can be useful for e.g. testing purposes.
- `AWS_DEFAULT_REGION` : The region, e.g. `us-east-1`, for the `boto3` AWS services.
- `AWS_PROFILE` : The AWS nanmed profile to use, if one is desired.
- `BOTOX_SERVICES` : The name of the AWS resources you want to use, e.g. `['sqs', 's3', 'ses']`.
- `BOTOX_OPTIONAL_PARAMS` : Useful if you need to pass additional parameters to the client/resource connections, e.g. a custom `endpoint_url` for a particular service. The format is a `dict` where the top-level keys are the name of the services you're using and for each the value is a `dict` containing to keys `args` (contains the parameters as `tuple`) and `kwargs` (contains the parameters as a `dict` when they should be passed as keyword arguments).
