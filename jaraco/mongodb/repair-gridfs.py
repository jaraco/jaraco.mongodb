"""
Script to repair broken GridFS files. It handles

- Removing files with missing chunks.
"""

import argparse
import logging
import sys

import gridfs
from more_itertools.recipes import consume

from jaraco.context import ExceptionTrap
from jaraco.itertools import Counter
from jaraco.mongodb import helper
from jaraco.ui import progress

log = logging.getLogger()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('db', type=helper.connect_gridfs)
    return parser.parse_args()


class FileRepair:
    def __init__(self, gfs):
        self.gfs = gfs
        db = gfs._GridFS__database
        coll = gfs._GridFS__collection
        bu_coll_name = coll.name + '-saved'
        self.backup_coll = db[bu_coll_name]

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
        with ExceptionTrap(gridfs.errors.CorruptGridFile) as trap:
            file.read(1)
        trap.filename = filename
        return trap

    def handle_trap(self, trap):
        cls, exc, tb = trap.exc_info
        spec = dict(filename=trap.filename)
        for file_doc in self.gfs._GridFS__files.find(spec):
            self.backup_coll.files.insert(file_doc)
            chunk_spec = dict(files_id=file_doc['_id'])
            for chunk in self.gfs._GridFS__chunks.find(chunk_spec):
                self.backup_coll.chunks.insert(chunk)
        log.info("Removing %s (%s)", trap.filename, exc)
        self.gfs.delete(spec)


def run():
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    args = get_args()

    repair = FileRepair(args.db)
    counter = repair.run()

    log.info("Removed %s corrupt files.", counter.count)


if __name__ == '__main__':
    run()
