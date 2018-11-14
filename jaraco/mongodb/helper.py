"""
Helper functions to augment PyMongo
"""

import warnings

import pymongo
import gridfs


def filter_warnings():
    warnings.warn(
        "filter_warnings is deprecated and has no effect; do not call",
        DeprecationWarning,
    )


def connect(uri, factory=pymongo.MongoClient):
    """
    Use the factory to establish a connection to uri.
    """
    warnings.warn(
        "do not use. Just call MongoClient directly.", DeprecationWarning)
    return factory(uri)


def connect_db(
        uri, default_db_name=None, factory=pymongo.MongoClient):
    """
    Use pymongo to parse a uri (possibly including database name) into
    a connected database object.

    This serves as a convenience function for the common use case where one
    wishes to get the Database object and is less concerned about the
    intermediate MongoClient object that pymongo creates (though the
    connection is always available as db.client).
    """
    uri_p = pymongo.uri_parser.parse_uri(uri)
    db_name = uri_p['database'] or default_db_name
    if not db_name:
        raise ValueError("A database name must be supplied")
    conn = factory(uri)
    return conn[db_name]


def connect_gridfs(uri, db=None):
    """
    Construct a GridFS instance for a MongoDB URI.
    """
    db = db or connect_db(uri)
    collection = pymongo.uri_parser.parse_uri(uri)['collection']
    return gridfs.GridFS(db, collection=collection or 'fs')
