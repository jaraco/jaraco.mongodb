import sys
import time
from jaraco.mongodb import helper

def is_index_op(op):
    return op.get('query', {}).get('createIndexes')

db = helper.connect_db(sys.argv[1])

while True:
    ops = db.current_op()['inprog']
    index_op = next(filter(is_index_op, ops))
    print(index_op['msg'], end='\r')
    time.sleep(5)
