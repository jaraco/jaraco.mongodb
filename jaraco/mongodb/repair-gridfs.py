"""
Script to repair broken GridFS files. It handles

 - Removing files with missing chunks.
"""

import sys
import logging
import argparse

from six.moves import filter, map

import gridfs
from jaraco.ui import progress
from more_itertools.recipes import consume
from jaraco.itertools import Counter

from jaraco.mongodb import helper
from jaraco.context import ExceptionTrap


log = logging.getLogger()


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('db', type=helper.connect_gridfs)
	return parser.parse_args()


class FileRepair:
	def __init__(self, gfs):
		self.gfs = gfs

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
		log.info("Removing %s (%s)", trap.filename, exc)
		spec = dict(filename=trap.filename)
		self.gfs.delete(spec)


def run():
	logging.basicConfig(stream=sys.stderr, level=logging.INFO)
	args = get_args()

	repair = FileRepair(args.db)
	counter = repair.run()

	log.info("Removed %s corrupt files.", counter.count)


if __name__ == '__main__':
	run()
