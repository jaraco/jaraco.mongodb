"""
Helper functions to augment PyMongo
"""

import pymongo
import gridfs


def get_collection(uri):
    return pymongo.uri_parser.parse_uri(uri)['collection']


def connect_gridfs(uri, db=None):
    """
    Construct a GridFS instance for a MongoDB URI.
    """
    return gridfs.GridFS(
        db or pymongo.MongoClient(uri).get_database(),
        collection=get_collection(uri) or 'fs',
    )
