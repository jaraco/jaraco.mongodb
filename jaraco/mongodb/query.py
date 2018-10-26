import six

import pymongo


def project(*args, **kwargs):
    """
    Build a projection for MongoDB.

    Due to https://jira.mongodb.org/browse/SERVER-3156, until MongoDB 2.6,
    the values must be integers and not boolean.

    >>> project(a=True) == {'a': 1}
    True

    Once MongoDB 2.6 is released, replace use of this function with a simple
    dict.
    """
    projection = dict(*args, **kwargs)
    return {key: int(value) for key, value in six.iteritems(projection)}


def compat_explain(cur):
    """
    Simulate MongoDB 3.0 explain result on prior versions.
    http://docs.mongodb.org/v3.0/reference/explain-results/
    """
    res = cur.explain()
    if 'nscannedObjects' in res:
        res['executionStats'] = dict(
            nReturned=res.pop('n'),
            totalKeysExamined=res.pop('nscanned'),
            totalDocsExamined=res.pop('nscannedObjects'),
            executionTimeMillis=res.pop('millis'),
        )
    return res


def upsert_and_fetch(coll, doc, **kwargs):
    """
    Fetch exactly one matching document or upsert
    the document if not found, returning the matching
    or upserted document.

    See https://jira.mongodb.org/browse/SERVER-28434
    describing the condition where MongoDB is uninterested in
    providing an upsert and fetch behavior.

    >>> instance = getfixture('mongodb_instance').get_connection()
    >>> coll = instance.test_upsert_and_fetch.items
    >>> doc = {'foo': 'bar'}
    >>> inserted = upsert_and_fetch(coll, doc)
    >>> inserted
    {...'foo': 'bar'...}
    >>> upsert_and_fetch(coll, doc) == inserted
    True
    """
    return coll.find_one_and_update(
        doc,
        {"$setOnInsert": doc},
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER,
        **kwargs
    )
