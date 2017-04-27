from jaraco.collections import Projection


def save(coll, to_save):
	"""
	Pymongo has deprecated the save logic, even though
	MongoDB still advertizes that logic in the core API:
	https://docs.mongodb.com/manual/reference/method/db.collection.save/

	This function provides a compatible interface.
	"""
	filter = Projection(['_id'], to_save)
	return coll.replace_one(filter, to_save, upsert=True)
