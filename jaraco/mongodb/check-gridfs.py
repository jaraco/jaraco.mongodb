"""
Script to check a GridFS instance for corrupted records.
"""

import sys
import logging
import argparse

import gridfs
import pymongo
from jaraco.ui import progress


log = logging.getLogger()


def connect_db(uri):
	host, sep, db_name = uri.rpartition('/')
	return pymongo.MongoClient(host)[db_name]


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--depth', default=1024,
		help="Bytes to read into each file during check",
	)
	parser.add_argument('db', type=connect_db)
	return parser.parse_args()


def run():
	logging.basicConfig(stream=sys.stderr)
	args = get_args()

	gfs = gridfs.GridFS(args.db)
	files = gfs.list()
	bar = progress.TargetProgressBar(len(files))

	for filename in bar.iterate(files):
		file = gfs.get_last_version(filename)
		try:
			file.read(args.depth)
		except Exception:
			log.exception("Failed to read %s", filename)


if __name__ == '__main__':
	run()
