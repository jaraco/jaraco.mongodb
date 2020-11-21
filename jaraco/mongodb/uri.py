from six.moves import urllib

import jaraco.functools


@jaraco.functools.once
def _add_scheme():
    """
    urllib.parse doesn't support the mongodb scheme, but it's easy
    to make it so.
    """
    lists = [
        urllib.parse.uses_relative,
        urllib.parse.uses_netloc,
        urllib.parse.uses_query,
    ]
    for each in lists:
        each.append('mongodb')


def join(base, new):
    """
    Use urllib.parse to join the MongoDB URIs.
    Registers the MongoDB scheme first.
    """
    _add_scheme()
    return urllib.parse.urljoin(base, new)
