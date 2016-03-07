from jaraco.mongodb import manage

def test_purge_all_databases(mongodb_instance):
	client = mongodb_instance.get_connection()
	client.test_db.test_coll.insert({'a': 1})
	client.test_db2.test_coll.insert({'b': 2})
	manage.purge_all_databases(client)
	assert client.database_names() == ['local']
