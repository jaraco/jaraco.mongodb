import re
import time
from typing import Annotated

import pymongo.database
import typer

from jaraco.mongodb import helper
from jaraco.ui.main import main

from .compat import query_or_command


def is_index_op(op):
    cmd = query_or_command(op) or {}
    return 'createIndexes' in cmd


@main
def run(
    db: Annotated[pymongo.database.Database, typer.Argument(parser=helper.connect_db)],
):
    while True:
        ops = db.client.admin.aggregate([{'$currentOp': {}}])
        index_op = next(filter(is_index_op, ops), None)
        if not index_op:
            print("No index operations in progress")
            break
        msg = index_op['msg']
        name = query_or_command(index_op)['indexes'][0]['name']
        pat = re.compile(r'Index Build( \(background\))?')
        msg = pat.sub(name, msg, count=1)
        print(msg, end='\r')
        time.sleep(5)
