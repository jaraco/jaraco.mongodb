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

	def distill(self):
		"""
		Distill this object (and its children)
		into a MongoDB update operation.
		"""
		return {
			'$set': {
				key: self[key]
				for key in self.__set
			},
			'$unset': {
				key: 1
				for key in self.__deleted
			},
		}
