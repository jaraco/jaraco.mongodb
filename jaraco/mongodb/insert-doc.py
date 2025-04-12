import json
import sys
from typing import Annotated

import pymongo.collection
import pymongo.uri_parser
import typer

from jaraco.ui.main import main


def get_collection(uri: str) -> pymongo.collection.Collection:
    parsed = pymongo.uri_parser.parse_uri(uri)
    client: pymongo.MongoClient = pymongo.MongoClient(uri)
    return client[parsed['database']][parsed['collection']]


@main
def run(
    collection: Annotated[
        pymongo.collection.Collection, typer.Argument(parser=get_collection)
    ],
):
    """
    Insert a document from stdin into the specified collection.
    """
    collection.insert_one(json.load(sys.stdin))
