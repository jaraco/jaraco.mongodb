"""
Script to move a subset of GridFS files from one db
(or collection) to another.
"""

import sys
import logging
import argparse
import itertools

from six.moves import map

from jaraco.ui import progress
from more_itertools.recipes import consume

from jaraco.mongodb import helper


log = logging.getLogger()


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('source_gfs', type=helper.connect_gridfs)
	parser.add_argument('dest_gfs', type=helper.connect_gridfs)
	parser.add_argument('--include',
		help="a filter of files (regex) to include",
	)
	parser.add_argument('--delete', default=False, action="store_true",
		help="delete files after moving",
	)
	parser.add_argument('--limit', type=int)
	return parser.parse_args()


class FileMove:
	include = None
	delete = False
	limit = None

	def __init__(self, **params):
		vars(self).update(**params)

	@property
	def filter(self):
		if not self.include:
			return
		return dict(filename={"$regex": self.include})

	@property
	def source_coll(self):
		return self.source_gfs._GridFS__collection

	@property
	def dest_coll(self):
		return self.dest_gfs._GridFS__collection

	def run(self):
		files = self.source_coll.files.find(self.filter,
			batch_size=1)
		limit_files = itertools.islice(files, self.limit)
		count = min(files.count(), self.limit or float('inf'))
		bar = progress.TargetProgressBar(count)
		to_process = map(self.process, bar.iterate(limit_files))
		consume(to_process)

	def process(self, file):
		chunks = self.source_coll.chunks.find(dict(files_id=file['_id']))
		for chunk in chunks:
			self.dest_coll.chunks.insert(chunk)
		self.dest_coll.files.insert(file)
		self.delete and self.source_gfs.delete(file['_id'])


def run():
	logging.basicConfig(stream=sys.stderr, level=logging.INFO)
	args = get_args()

	mover = FileMove(**vars(args))
	mover.run()


if __name__ == '__main__':
	run()
