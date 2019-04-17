import contextlib


class Differencing:
	"""
	Mix-in for a MutableMapping to capture the differences
	applied to it.

	>>> dd = type('DifferencingDict', (Differencing, dict), {})
	>>> doc = dd(num=5, removed='delete me')
	>>> doc['num'] += 1
	>>> doc['new'] = 'new_value'
	>>> del doc['removed']
	>>> doc.distill() == {'$set': {'num': 6, 'new': 'new_value'}, \
'$unset': {'removed': 1}}
	True
	"""

	def __init__(self, *args, **kwargs):
		super(Differencing, self).__init__(*args, **kwargs)
		self.__deleted = set()
		self.__set = set()

	def __setitem__(self, key, value):
		super(Differencing, self).__setitem__(key, value)
		self.__set.add(key)
		self.__deleted.discard(key)

	def __delitem__(self, key):
		super(Differencing, self).__delitem__(key)
		self.__deleted.add(key)
		self.__set.discard(key)

	def _sets(self):
		for key in self.__set:
			yield key, self[key]
		children = (
			key
			for key in self
			if key not in self.__set and key not in self.__deleted
		)
		for key in children:
			with contextlib.suppress(AttributeError):
				for child_key, value in self[key]._sets():
					yield '.'.join((key, child_key)), value

	def _deletes(self):
		for key in self.__deleted:
			yield key, 1
		children = (
			key
			for key in self
			if key not in self.__set and key not in self.__deleted
		)
		for key in children:
			with contextlib.suppress(AttributeError):
				for child_key, value in self[key]._deletes():
					yield '.'.join((key, child_key)), value

	def distill(self):
		"""
		Distill this object (and its children)
		into a MongoDB update operation.
		"""
		spec = {
			'$set': dict(self._sets()),
			'$unset': dict(self._deletes()),
		}
		# MongoDB is bad at honoring degenerate forms, so remove them
		return {
			key: value
			for key, value in spec.items()
			if value
		}

	def finalize(self):
		"""
		Because MongoDB performs many __setitem__ calls
		when constructing the document from BSON, it's
		necessary to clear self.__set after the document
		is loaded.
		"""
		self.__set.clear()
		for child in self:
			with contextlib.suppress(AttributeError):
				self[child].finalize()
