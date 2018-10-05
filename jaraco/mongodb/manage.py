import re


def all_databases(client, exclude=['local']):
	"""
	Yield all databases except excluded (default
	excludes 'local').
	"""
	return (
		client[db_name]
		for db_name in client.list_database_names()
		if db_name not in exclude
	)


def all_collections(db):
	"""
	Yield all non-sytem collections in db.
	"""
	include_pattern = r'(?!system\.)'
	return (
		db[name]
		for name in db.list_collection_names()
		if re.match(include_pattern, name)
	)


def purge_collection(coll):
	coll.delete_all({})


def safe_purge_collection(coll):
	"""
	Cannot remove documents from capped collections
	in later versions of MongoDB, so drop the
	collection instead.
	"""
	op = (
		drop_collection
		if coll.options().get('capped', False)
		else purge_collection
	)
	return op(coll)


def drop_collection(coll):
	coll.database.drop_collection(coll.name)


def purge_all_databases(client, op=drop_collection):
	collections = (
		coll
		for db in all_databases(client)
		for coll in all_collections(db)
	)

	for coll in collections:
		op(coll)
