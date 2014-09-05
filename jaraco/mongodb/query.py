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
