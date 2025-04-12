"""
Script to move a subset of GridFS files from one db
(or collection) to another.

>>> import io
>>> db_uri = getfixture('mongodb_uri') + '/move_gridfs_test'
>>> source = helper.connect_gridfs(db_uri + '.source')
>>> dest = helper.connect_gridfs(db_uri + '.dest')
>>> id = source.put(io.BytesIO(b'test'), filename='test.txt')
>>> mover = FileMove(source_gfs=source, dest_gfs=dest, delete=True)
>>> mover.ensure_indexes()
>>> mover.run(bar=None)
>>> source.list()
[]
>>> dest.exists(id)
True
>>> dest.list()
['test.txt']
"""

from __future__ import annotations

import datetime
import itertools
import logging
import signal
import sys
from typing import Annotated

import bson
import dateutil.parser
import gridfs
import typer
from more_itertools.recipes import consume

from jaraco.mongodb import helper
from jaraco.ui import progress
from jaraco.ui.main import main

log = logging.getLogger()


class FileMove:
    include = None
    delete = False
    limit = None
    limit_date = None

    def __init__(self, **params):
        vars(self).update(**params)

    def ensure_indexes(self):
        """
        Create the same indexes that the GridFS API would have
        """
        self.dest_gfs.new_file()._GridIn__ensure_indexes()

    @property
    def filter(self):
        filter = {}
        if self.include:
            filter.update(filename={"$regex": self.include})
        if self.limit_date:
            id_max = bson.objectid.ObjectId.from_datetime(self.limit_date)
            filter.update(_id={"$lt": id_max})
        return filter

    @property
    def source_coll(self):
        return self.source_gfs._GridFS__collection

    @property
    def dest_coll(self):
        return self.dest_gfs._GridFS__collection

    def run(self, bar=progress.TargetProgressBar):
        files = self.source_coll.files.find(
            self.filter,
            batch_size=1,
        )
        limit_files = itertools.islice(files, self.limit)
        count = min(files.count(), self.limit or float('inf'))
        progress = bar(count).iterate if bar else iter
        with SignalTrap(progress(limit_files)) as items:
            consume(map(self.process, items))

    def process(self, file):
        chunks = self.source_coll.chunks.find(dict(files_id=file['_id']))
        for chunk in chunks:
            self.dest_coll.chunks.insert(chunk)
        self.dest_coll.files.insert(file)
        self.delete and self.source_gfs.delete(file['_id'])


class SignalTrap:
    """
    A context manager for wrapping an iterable such that it
    is only interrupted between iterations.
    """

    def __init__(self, iterable):
        self.iterable = iterable

    def __enter__(self):
        self.prev = signal.signal(signal.SIGINT, self.stop)
        return self

    def __exit__(self, *args):
        signal.signal(signal.SIGINT, self.prev)
        del self.prev

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iterable)

    next = __next__

    def stop(self, signal, frame):
        self.iterable = iter([])


@main
def run(
    source_gfs: Annotated[gridfs.GridFS, typer.Argument(parser=helper.connect_gridfs)],
    dest_gfs: Annotated[gridfs.GridFS, typer.Argument(parser=helper.connect_gridfs)],
    include: Annotated[
        str | None, typer.Option(help="a filter of files (regex) to include")
    ] = None,
    delete: Annotated[bool, typer.Option(help="delete files after moving")] = False,
    limit: int | None = None,
    limit_date: Annotated[
        datetime.datetime | None,
        typer.Option(
            parser=dateutil.parser.parse, help='only move files older than this date'
        ),
    ] = None,
):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    mover = FileMove(**locals())
    mover.ensure_indexes()
    mover.run()
