import six

import pytest


collect_ignore = [
	'jaraco/mongodb/pmxbot.py',
	# disable move-gridfs check, as it causes output capturing
	# to be disabled. See pytest-dev/pytest#3752.
	'jaraco/mongodb/move-gridfs.py',
]


if six.PY2:
	collect_ignore.append('jaraco/mongodb/monitor-index-creation.py')


@pytest.fixture(scope='function')
def database(request, mongodb_instance):
	"""
	Return a clean MongoDB database suitable for testing.
	"""
	db_name = request.node.name.replace('.', '_')
	database = mongodb_instance.get_connection()[db_name]
	yield database
	database.client.drop_database(db_name)
