import pytest
from bson.codec_options import CodecOptions

from jaraco.mongodb import diff


@pytest.fixture
def coll(request, mongodb_instance):
	return mongodb_instance.get_connection().diff_tests[request.node.name]


class DD(diff.Differencing, dict):
	@classmethod
	def wrap(cls, collection):
		return collection.with_options(CodecOptions(document_class=cls))


class TestSimpleDocs:
	def test_apply_diff_basic(self, coll):
		coll.insert_one(dict(num=5, removed='delete me'))
		doc = DD.wrap(coll).find_one({})
		doc['num'] += 1
		doc['new'] = 'new_value'
		del doc['removed']
		coll.update_one(dict(_id=doc['_id']), doc.distill())
		expected = dict(num=6, new='new_value')
		assert coll.find_one({}, projection=dict(_id=0)) == expected

	def test_no_update(self, coll):
		orig = dict(zip('ab', range(2)))
		coll.insert_one(dict(orig))
		doc = DD.wrap(coll).find_one({})
		doc.finalize()
		assert doc.distill() == doc.null_update
		coll.update_one(dict(_id=doc['_id']), doc.distill())
		assert coll.find_one({}, projection=dict(_id=0)) == orig


class TestNestedDocs:
	def test_distill_subkeys(self):
		doc = DD(a=3, b=DD(foo='bar'))
		doc['b']['foo'] = 'baz'
		assert doc.distill() == {'$set': {'b.foo': 'baz'}}

	def test_diff_on_nested_key(self, coll):
		coll.insert_one(dict(a=3, b=dict(foo='bar')))
		doc = DD.wrap(coll).find_one({})
		doc.finalize()
		doc['b']['foo'] = 'baz'
		assert doc.distill() == {'$set': {'b.foo': 'baz'}}
		coll.update_one(dict(_id=doc['_id']), doc.distill())
		expected = dict(a=3, b=dict(foo='baz'))
		assert coll.find_one({}, projection=dict(_id=0)) == expected
