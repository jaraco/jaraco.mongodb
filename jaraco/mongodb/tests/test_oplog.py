import bson

from jaraco.mongodb import oplog

class TestReplacer:
	def test_rename_index_op_ns(self):
		"""
		As an index operation references namespaces,
		when performing a rename operation, it's also important
		to rename the ns in the op itself.
		"""
		op = {
			'ts': bson.Timestamp(1446495808, 3),
			'ns': 'airportlocker.system.indexes',
			'op': 'i',
			'o': {
				'ns': 'airportlocker.luggage.chunks',
				'key': {'files_id': 1, 'n': 1},
				'name': 'files_id_1_n_1', 'unique': True
			},
		}

		ren = oplog.Renamer.from_specs("airportlocker=airportlocker-us")
		ren(op)

		assert op['ns'] == 'airportlocker-us.system.indexes'
		assert op['o']['ns'] == 'airportlocker-us.luggage.chunks'
