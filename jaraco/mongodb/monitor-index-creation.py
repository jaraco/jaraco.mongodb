import sys
import time
import re
from jaraco.mongodb import helper

def is_index_op(op):
	return op.get('query', {}).get('createIndexes')

def run():
	db = helper.connect_db(sys.argv[1])

	while True:
		ops = db.current_op()['inprog']
		index_op = next(filter(is_index_op, ops))
		msg = index_op['msg']
		name = index_op['query']['indexes'][0]['name']
		msg = re.sub('Index Build(\ (background\))?', name, msg)
		print(msg, end='\r')
		time.sleep(5)

__name__ == '__main__' and run()
