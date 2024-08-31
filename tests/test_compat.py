from jaraco.mongodb import compat


def test_save_no_id(database):
    doc = dict(foo='bar')
    compat.save(database.test_coll, doc)
    assert database.test_coll.find_one()['foo'] == 'bar'


def test_save_new_with_id(database):
    doc = dict(foo='bar', _id=1)
    compat.save(database.test_coll, doc)
    assert database.test_coll.find_one() == doc


def test_save_replace_by_id(database):
    compat.save(database.test_coll, dict(foo='bar', _id=1))

    doc = dict(foo='baz', _id=1)
    compat.save(database.test_coll, doc)
    assert database.test_coll.count_documents({}) == 1
    assert database.test_coll.find_one() == doc


def test_save_no_id_extant_docs(database):
    """
    When no id is supplied, a new document should be created.
    """
    doc = dict(foo='bar')
    compat.save(database.test_coll, dict(doc))
    assert database.test_coll.count_documents({}) == 1
    compat.save(database.test_coll, doc)
    assert database.test_coll.count_documents({}) == 2


def test_save_adds_id(database):
    """
    Ensure _id is added to an inserted document.
    """
    doc = dict(foo='bar')
    compat.save(database.test_coll, doc)
    assert '_id' in doc
