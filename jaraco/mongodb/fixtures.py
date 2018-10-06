import shlex

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


@pytest.yield_fixture(scope='session')
def mongodb_instance():
	if 'pymongo' not in globals():
		pytest.skip("pymongo not available")

	params_raw = pytest.config.getoption('mongod_args') or ''
	params = shlex.split(params_raw)
	try:
		instance = service.MongoDBInstance()
		instance.merge_mongod_args(params)
		instance.start()
		pymongo.MongoClient(instance.get_connect_hosts())
		yield instance
	except Exception as err:
		pytest.skip("MongoDB not available ({err})".format(**locals()))
	instance.stop()


@pytest.fixture(scope='session')
def mongodb_uri(mongodb_instance):
	return mongodb_instance.get_uri()
