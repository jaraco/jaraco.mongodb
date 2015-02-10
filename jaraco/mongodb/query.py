import six


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
