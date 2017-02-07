def safe_upsert_27707(coll, query, op):
	"""
	In SERVER-27707,
	https://jira.mongodb.org/browse/SERVER-27707,
	we learn that upsert operations fail in
	MongoDB 3.4.0 and 3.4.1 if they filter on
	items in an array and invoke $addToSet.
	This routine invokes the operation in a multi-phase
	way to avoid the bug.
	"""
	item = op.pop('$addToSet')
	exists = bool(coll.find_one(query))
	if not exists:
		# create an initial object
		init = {field: [value] for field, value in item.items()}
		coll.insert(init)
	coll.update(query, op)
