"""
Script to check a GridFS instance for corrupted records.
"""

import sys
import logging
import argparse
import functools

import gridfs
import pymongo
from jaraco.ui import progress

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


def process_file(gfs, depth, filename):
	file = gfs.get_last_version(filename)
	with ExceptionTrap(pymongo.errors.PyMongoError) as trap:
		file.read(depth)
	if trap:
		exc, cls, tb = trap.exc_info
		log.error("Failed to read %s (%s)", filename, exc)


def run():
	logging.basicConfig(stream=sys.stderr)
	args = get_args()

	gfs = gridfs.GridFS(args.db)
	files = gfs.list()
	bar = progress.TargetProgressBar(len(files))

	handle = functools.partial(process_file, gfs, args.depth)

	list(map(handle, bar.iterate(files)))


if __name__ == '__main__':
	run()
