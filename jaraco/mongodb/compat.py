import functools

from jaraco.collections import Projection


def save(coll, to_save):
	"""
	Pymongo has deprecated the save logic, even though
	MongoDB still advertizes that logic in the core API:
	https://docs.mongodb.com/manual/reference/method/db.collection.save/

	This function provides a compatible interface.
	"""
	filter = Projection(['_id'], to_save)
	upsert_replace = functools.partial(coll.replace_one, filter, upsert=True)
	op = upsert_replace if filter else coll.insert_one
	return op(to_save)


def query_or_command(op):
	"""
	Given an operation from currentOp, return the query or command
	field as it changed in MongoDB 3.2 for indexing operations:

	https://docs.mongodb.com/manual/reference/method/db.currentOp/#active-indexing-operations
	"""
	return op.get('command') or op.get('query')
