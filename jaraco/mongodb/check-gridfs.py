"""
Script to check a GridFS instance for corrupted records.
"""

import sys
import logging
import argparse

from six.moves import filter, map

import gridfs
import pymongo
from jaraco.ui import progress
from more_itertools.recipes import consume
from jaraco.itertools import Counter

from jaraco.mongodb import helper
from jaraco.context import ExceptionTrap


log = logging.getLogger()


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--depth', default=1024,
		help="Bytes to read into each file during check",
	)
	parser.add_argument('db', type=helper.connect_db)
	return parser.parse_args()


class FileChecker:
	def __init__(self, gfs, depth):
		self.gfs = gfs
		self.depth = depth

	def process(self, filename):
		file = self.gfs.get_last_version(filename)
		with ExceptionTrap(pymongo.errors.PyMongoError) as trap:
			file.read(self.depth)
		trap.filename = filename
		return trap

	def handle_trap(self, trap):
		exc, cls, tb = trap.exc_info
		log.error("Failed to read %s (%s)", trap.filename, exc)


def run():
	logging.basicConfig(stream=sys.stderr)
	args = get_args()

	gfs = gridfs.GridFS(args.db)
	files = gfs.list()
	bar = progress.TargetProgressBar(len(files))

	checker = FileChecker(gfs, args.depth)

	processed_files = map(checker.process, bar.iterate(files))
	errors = filter(None, processed_files)
	counter = Counter(errors)
	consume(map(checker.handle_trap, counter))

	print("Encountered", counter.count, "errors")


if __name__ == '__main__':
	run()
