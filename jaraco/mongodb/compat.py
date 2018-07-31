import functools

import pymongo.collection
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


class Collection(pymongo.collection.Collection):
	"""
	Subclass of default Collection that provides a non-deprecated
	save method. Don't use without first reading the cautions at
	https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#q--a

	>> db = getfixture('database')
	>> coll = Collection(db, 'mycoll')
	>> coll.save({'foo': 'bar'})
	<pymongo.results.InsertOneResult object at ...>
	>> ob = coll.find_one()
	>> ob['foo'] = 'baz'
	>> coll.save(ob)
	<pymongo.results.UpdateResult object at ...>
	"""
	save = save


def query_or_command(op):
	"""
	Given an operation from currentOp, return the query or command
	field as it changed in MongoDB 3.2 for indexing operations:

	https://docs.mongodb.com/manual/reference/method/db.currentOp/#active-indexing-operations
	"""
	return op.get('command') or op.get('query')
