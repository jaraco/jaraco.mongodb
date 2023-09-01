from jaraco.mongodb import manage


def test_purge_all_databases(mongodb_instance):
    client = mongodb_instance.get_connection()
    client.test_db.test_coll.insert_one({'a': 1})
    client.test_db2.test_coll.insert_one({'b': 2})
    manage.purge_all_databases(client)
    indexes = {'system.indexes'}
    assert set(client.test_db.list_collection_names()) <= indexes
    assert set(client.test_db2.list_collection_names()) <= indexes
