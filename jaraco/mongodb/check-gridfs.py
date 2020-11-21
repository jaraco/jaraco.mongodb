"""
Script to check a GridFS instance for corrupted records.
"""

import sys
import logging
import argparse

import pymongo
from jaraco.ui import progress
from more_itertools.recipes import consume
from jaraco.itertools import Counter

from jaraco.mongodb import helper
from jaraco.context import ExceptionTrap


log = logging.getLogger()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--depth',
        default=1024,
        help="Bytes to read into each file during check",
    )
    parser.add_argument('db', type=helper.connect_gridfs)
    return parser.parse_args()


class FileChecker:
    def __init__(self, gfs, depth):
        self.gfs = gfs
        self.depth = depth

    def run(self):
        files = self.gfs.list()
        bar = progress.TargetProgressBar(len(files))
        processed_files = map(self.process, bar.iterate(files))
        errors = filter(None, processed_files)
        counter = Counter(errors)
        consume(map(self.handle_trap, counter))
        return counter

    def process(self, filename):
        file = self.gfs.get_last_version(filename)
        with ExceptionTrap(pymongo.errors.PyMongoError) as trap:
            file.read(self.depth)
        trap.filename = filename
        return trap

    def handle_trap(self, trap):
        cls, exc, tb = trap.exc_info
        log.error("Failed to read %s (%s)", trap.filename, exc)


def run():
    logging.basicConfig(stream=sys.stderr)
    args = get_args()

    checker = FileChecker(args.db, args.depth)
    counter = checker.run()

    print("Encountered", counter.count, "errors")


if __name__ == '__main__':
    run()
