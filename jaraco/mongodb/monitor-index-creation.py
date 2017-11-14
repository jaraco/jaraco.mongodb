import time
import re
import argparse

from jaraco.mongodb import helper


def is_index_op(op):
	return op.get('query', {}).get('createIndexes')


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('db')
	return parser.parse_args()


def run():
	db = helper.connect_db(get_args().db)

	while True:
		ops = db.current_op()['inprog']
		index_op = next(filter(is_index_op, ops), None)
		if not index_op:
			print("No index operations in progress")
			break
		msg = index_op['msg']
		name = index_op['query']['indexes'][0]['name']
		pat = re.compile('Index Build( \(background\))?')
		msg = pat.sub(name, msg, count=1)
		print(msg, end='\r')
		time.sleep(5)


__name__ == '__main__' and run()
