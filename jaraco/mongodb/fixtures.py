import shlex
import os

import pytest

try:
    import pymongo
except ImportError:
    pass

from . import service


def pytest_addoption(parser):
    parser.addoption(
        '--mongod-args',
        help="Arbitrary arguments to mongod",
    )
    parser.addoption(
        '--mongodb-uri',
        help="URI to an extant MongoDB instance (supersedes ephemeral)",
    )


@pytest.fixture(scope='session')
def mongodb_instance(request):
    if 'pymongo' not in globals():
        pytest.skip("pymongo not available")

    yield from _extant_instance(request.config)
    yield from _ephemeral_instance(request.config)


def _extant_instance(config):
    uri = config.getoption('mongodb_uri') or os.environ.get('MONGODB_URL')
    if not uri:
        return
    yield service.ExtantInstance(uri)


def _ephemeral_instance(config):
    params_raw = config.getoption('mongod_args') or ''
    params = shlex.split(params_raw)
    try:
        instance = service.MongoDBInstance()
        with instance.ensure():
            instance.merge_mongod_args(params)
            instance.start()
            pymongo.MongoClient(instance.get_connect_hosts())
            yield instance
    except Exception as err:
        pytest.skip(f"MongoDB not available ({err})")
    instance.stop()


@pytest.fixture(scope='session')
def mongodb_uri(mongodb_instance):
    return mongodb_instance.get_uri()
