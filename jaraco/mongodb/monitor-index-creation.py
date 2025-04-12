import re
import time

import autocommand

from jaraco.mongodb import helper

from .compat import query_or_command


def is_index_op(op):
    cmd = query_or_command(op) or {}
    return 'createIndexes' in cmd


@autocommand.autocommand(__name__)
def run(db: helper.connect_db):
    while True:
        # broken on PyMongo 4 (#44)
        ops = db.current_op()['inprog']  # type: ignore[index]
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
