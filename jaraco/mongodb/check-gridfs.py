"""
Script to check a GridFS instance for corrupted records.
"""

import logging
import sys
from typing import Annotated

import gridfs
import pymongo
import typer
from more_itertools.recipes import consume

from jaraco.context import ExceptionTrap
from jaraco.itertools import Counter
from jaraco.mongodb import helper
from jaraco.ui import progress
from jaraco.ui.main import main

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


@main
def run(
    db: Annotated[gridfs.GridFS, typer.Argument(parser=helper.connect_gridfs)],
    depth: Annotated[
        int, typer.Argument(help='Bytes to read into each file during check')
    ] = 1024,
):
    logging.basicConfig(stream=sys.stderr)

    checker = FileChecker(db, depth)
    counter = checker.run()

    print("Encountered", counter.count, "errors")
