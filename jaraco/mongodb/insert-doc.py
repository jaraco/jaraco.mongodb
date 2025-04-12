import json
import sys

import autocommand
import pymongo.collection
import pymongo.uri_parser


def get_collection(uri: str) -> pymongo.collection.Collection:
    parsed = pymongo.uri_parser.parse_uri(uri)
    client: pymongo.MongoClient = pymongo.MongoClient(uri)
    return client[parsed['database']][parsed['collection']]


@autocommand.autocommand(__name__)
def main(collection: get_collection):
    """
    Insert a document from stdin into the specified collection.
    """
    collection.insert_one(json.load(sys.stdin))  # type: ignore[attr-defined]
