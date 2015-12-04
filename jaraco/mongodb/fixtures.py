import pytest
try:
	import pymongo
except ImportError:
	pass

from . import service

@pytest.yield_fixture(scope='session')
def mongodb_instance():
	if 'pymongo' not in globals():
		pytest.skip("pymongo not available")
	try:
		instance = service.MongoDBInstance()
		instance.log_root = ''
		instance.start()
		pymongo.MongoClient(instance.get_connect_hosts())
		yield instance
	except Exception as err:
		pytest.skip("MongoDB not available ({err})".format(**locals()))
	instance.stop()

@pytest.fixture(scope='session')
def mongodb_uri(mongodb_instance):
	return mongodb_instance.get_uri()
