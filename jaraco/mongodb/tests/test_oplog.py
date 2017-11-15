import functools

import bson
import pytest
import jaraco.itertools

from jaraco.mongodb import oplog
from jaraco.mongodb import service


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

	def test_collection_rename_on_create_cmd(self):
		"""
		Starting in MongoDB 3.2, a create collection is required
		before insert operations (apparently). Ensure that a renamed
		command in a create collection is renamed.
		"""
		op = {
			'h': -4317026186822365585,
			't': 1,
			'ns': 'newdb.$cmd',
			'v': 2,
			'o': {'create': 'coll_1'},
			'ts': bson.Timestamp(1470940276, 1),
			'op': 'c',
		}

		ren = oplog.Renamer.from_specs("newdb.coll_1=newdb.coll_2")
		ren(op)

		assert op['o']['create'] == 'coll_2'


def make_replicaset(request):
	try:
		r_set = service.MongoDBReplicaSet()
		r_set.log_root = ''
		r_set.start()
		r_set.get_connection()
		request.addfinalizer(r_set.stop)
	except Exception as err:
		pytest.skip("MongoDB not available ({err})".format(**locals()))
	return r_set


@pytest.fixture
def replicaset_factory(request):
	"""
	Return a factory that can generate MongoDB replica sets
	"""
	maker = functools.partial(make_replicaset, request)
	return jaraco.itertools.infinite_call(maker)


class TestOplogReplication:
	def test_index_deletion(self, replicaset_factory):
		"""
		A delete index operation should be able to be applied to a replica
		"""
		source = next(replicaset_factory).get_connection()
		dest = next(replicaset_factory).get_connection()
		source_oplog = oplog.Oplog(source.local.oplog.rs)
		before_ts = source_oplog.get_latest_ts()
		source.index_deletion_test.stuff.create_index("foo")
		for op in source_oplog.since(before_ts):
			oplog.apply(dest, op)

		id_index, foo_index = dest.index_deletion_test.stuff.list_indexes()

		after_ts = source_oplog.get_latest_ts()
		source.index_deletion_test.stuff.drop_index("foo_1")
		delete_index_op, = source_oplog.since(after_ts)
		print("attempting", delete_index_op)
		oplog.apply(dest, delete_index_op)
		only_index, = dest.index_deletion_test.stuff.list_indexes()
		assert only_index['name'] == '_id_'
