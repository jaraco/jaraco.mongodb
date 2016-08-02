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
	return jaraco.itertools.infiniteCall(make_replicaset, request)


class TestOplogReplication:
	def test_index_deletion(self, replicaset_factory):
		"""
		A delete index operation should be able to be applied to a replica
		"""
		source = next(replicaset_factory).get_connection()
		dest = next(replicaset_factory).get_connection()
		source.index_deletion_test.stuff.ensure_index("foo")
		dest.index_deletion_test.stuff.ensure_index("foo")
		source_oplog = oplog.Oplog(source.local.oplog.rs)
		begin_ts = source_oplog.get_latest_ts()
		source.index_deletion_test.stuff.drop_index("foo_1")
		delete_index_op, = source_oplog.since(oplog.increment_ts(begin_ts))
		print("attempting", delete_index_op)
		oplog.apply(dest, delete_index_op)
		only_index, = dest.index_deletion_test.stuff.list_indexes()
		assert only_index['name'] == '_id_'
