import pytest
from jaraco.test import services

@pytest.fixture(scope='session')
def mongodb(request):
	try:
		import pymongo
		instance = services.MongoDBInstance()
		instance.log_root = ''
		instance.start()
		pymongo.Connection(instance.get_connect_hosts())
	except Exception:
		return None
	request.addfinalizer(instance.stop)
	return instance

@pytest.fixture(scope='session')
def mongodb_uri(mongodb):
	return 'mongodb://' + ','.join(mongodb.get_connect_hosts())
