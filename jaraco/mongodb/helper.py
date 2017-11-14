"""
Helper functions to augment PyMongo
"""

import warnings

import pymongo
import gridfs


def filter_warnings():
    _filter_username_warning()


def _filter_username_warning():
    """
    Suppress warnings when passing a URI to MongoDB that includes the database
    name.
    """
    warnings.filterwarnings(
        'ignore', category=UserWarning,
        message=".*must provide a username",
        module='pymongo.mongo_client' if pymongo.version_tuple >= (2, 4) else
        'pymongo.connection',
    )


def _filter_safe_deprecation():
    """
    Due to a bug in pymongo, safe must be used in some cases even while it's
    deprecated. If that's the case, call this function to suppress those
    warnings.
    """
    warnings.filterwarnings(
        'ignore', category=DeprecationWarning,
        message=".*write_concern option instead",
        module='pymongo.common',
    )


def connect(uri, factory=pymongo.MongoClient):
    """
    Use the factory to establish a connection to uri.
    """
    return factory(uri)


def connect_db(uri, default_db_name=None, **kwargs):
    """
    Use pymongo to parse a uri (possibly including database name) into
    a connected database object.

    This serves as a convenience function for the common use case where one
    wishes to get the Database object and is less concerned about the
    intermediate MongoClient object that pymongo creates (though the
    connection is always available as db.client).
    """
    filter_warnings()
    uri_p = pymongo.uri_parser.parse_uri(uri)
    db_name = uri_p['database'] or default_db_name
    if not db_name:
        raise ValueError("A database name must be supplied")
    conn = connect(uri, **kwargs)
    return conn[db_name]


def connect_gridfs(uri, db=None):
    """
    Construct a GridFS instance for a MongoDB URI.
    """
    db = db or connect_db(uri)
    collection = pymongo.uri_parser.parse_uri(uri)['collection']
    return gridfs.GridFS(db, collection=collection or 'fs')
