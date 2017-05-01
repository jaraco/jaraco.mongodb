import pytest

from jaraco.mongodb import compat


@pytest.fixture(scope='function')
def database(request, mongodb_instance):
	"""
	Return a clean MongoDB database suitable for testing.
	"""
	db_name = request.node.name
	database = mongodb_instance.get_connection()[db_name]
	yield database
	database.client.drop_database(db_name)


def test_save_no_id(database):
	doc = dict(foo='bar')
	compat.save(database.test_coll, doc)
	assert database.test_coll.find_one()['foo'] == 'bar'


def test_save_new_with_id(database):
	doc = dict(foo='bar', _id=1)
	compat.save(database.test_coll, doc)
	assert database.test_coll.find_one() == doc


def test_save_replace_by_id(database):
	compat.save(database.test_coll, dict(foo='bar', _id=1))

	doc = dict(foo='baz', _id=1)
	compat.save(database.test_coll, doc)
	assert database.test_coll.count() == 1
	assert database.test_coll.find_one() == doc


def test_save_no_id_extant_docs(database):
	"""
	When no id is supplied, a new document should be created.
	"""
	doc = dict(foo='bar')
	compat.save(database.test_coll, dict(doc))
	assert database.test_coll.count() == 1
	compat.save(database.test_coll, doc)
	assert database.test_coll.count() == 2
