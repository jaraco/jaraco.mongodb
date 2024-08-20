"""
Decode support for JSON strings using ordered dictionaries and parsing
MongoDB-specific objects like dates.

For example, if you have a JSON object representing a sort, you
want to retain the order of keys:

>>> ob = decode('{"key1": 1, "key2": 2}')
>>> list(ob.keys())
['key1', 'key2']

Or if you want to query by a date, PyMongo needs a Python datetime
object, which has no JSON representation, so this codec converts
``$date`` keys to date objects.

>>> ob = decode('{"$gte": {"$date": "2019-01-01"}}')
>>> ob['$gte']
datetime.datetime(2019, 1, 1, 0, 0)

This function is useful in particular if you're accepting JSON queries
over an HTTP connection and you don't have the luxury of Javascript
expressions like you see in the Mongo shell or Compass.
"""

import collections
import functools
import json

import dateutil.parser

from jaraco.functools import compose


def maybe_date(obj):
    """
    >>> maybe_date({"$date": "2019-01-01"})
    datetime.datetime(2019, 1, 1, 0, 0)
    """
    return dateutil.parser.parse(obj['$date']) if list(obj) == ['$date'] else obj


smart_hook = compose(maybe_date, collections.OrderedDict)


decode = functools.partial(json.loads, object_pairs_hook=smart_hook)  # type: ignore
