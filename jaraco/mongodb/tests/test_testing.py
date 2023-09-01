import functools

import pytest

from jaraco.mongodb import testing


@pytest.fixture
def indexed_collection(request, mongodb_instance):
    _name = request.function.__name__
    db = mongodb_instance.get_connection()[_name]
    dropper = functools.partial(db.client.drop_database, _name)
    request.addfinalizer(dropper)
    coll = db[_name]
    coll.create_index('foo')
    return coll


def test_assert_covered_passes(indexed_collection):
    indexed_collection.insert_one({'foo': 'bar'})
    proj = {'_id': False, 'foo': True}
    cur = indexed_collection.find({'foo': 'bar'}, proj)
    testing.assert_covered(cur)


def test_assert_covered_empty(indexed_collection):
    """
    assert_covered should raise an error it's trivially
    covered (returns no results)
    """
    cur = indexed_collection.find()
    with pytest.raises(AssertionError):
        testing.assert_covered(cur)


def test_assert_covered_null(indexed_collection):
    """
    assert_covered should raise an error it's trivially
    covered (returns no results)
    """
    indexed_collection.insert_one({"foo": "bar"})
    proj = {'_id': False, 'foo': True}
    cur = indexed_collection.find({"foo": "baz"}, proj)
    with pytest.raises(AssertionError):
        testing.assert_covered(cur)


def test_assert_index_used_passes(indexed_collection):
    """
    assert_index_used should pass when the index is used,
    even if the documents had to be hit.
    """
    indexed_collection.insert_one({'foo': 'bar', 'bing': 'baz'})
    cur = indexed_collection.find({'foo': 'bar'})
    testing.assert_index_used(cur)


def test_assert_index_used_fails(indexed_collection):
    """
    assert_index_used should fail when no index is used.
    """
    indexed_collection.insert_one({'foo': 'bar', 'bing': 'baz'})
    cur = indexed_collection.find({'bing': 'baz'})
    with pytest.raises(AssertionError):
        testing.assert_index_used(cur)
