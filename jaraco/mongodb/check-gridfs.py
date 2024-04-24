"""
Script to check a GridFS instance for corrupted records.
"""

import logging
import sys

import autocommand
import pymongo
from more_itertools.recipes import consume

from jaraco.context import ExceptionTrap
from jaraco.itertools import Counter
from jaraco.mongodb import helper
from jaraco.ui import progress

log = logging.getLogger()


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


@autocommand.autocommand(__name__)
def run(
    db: helper.connect_gridfs,  # type: ignore
    depth: (int, 'Bytes to read into each file during check') = 1024,  # type: ignore # noqa: F722
):
    logging.basicConfig(stream=sys.stderr)

    checker = FileChecker(db, depth)
    counter = checker.run()

    print("Encountered", counter.count, "errors")
