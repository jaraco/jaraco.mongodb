import sys
import json

import argparse

import pymongo.uri_parser


def get_collection(uri):
    parsed = pymongo.uri_parser.parse_uri(uri)
    client = pymongo.MongoClient(uri)
    return client[parsed['database']][parsed['collection']]


def parse_args():
    parser = argparse.ArgumentParser(
        "Insert a document from stdin into the specied collection"
    )
    parser.add_argument(
        'collection',
        metavar='collection_uri',
        type=get_collection,
    )
    return parser.parse_args()


def main():
    args = parse_args()
    args.collection.insert_one(json.load(sys.stdin))


__name__ == '__main__' and main()
