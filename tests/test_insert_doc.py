import json
import subprocess
import sys


def test_insert_doc_command(mongodb_instance):
    uri = mongodb_instance.get_uri() + '/testdb.test_coll'
    cmd = [
        sys.executable,
        '-m',
        'jaraco.mongodb.insert-doc',
        uri,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    doc = dict(test='value', test2=2)
    proc.communicate(json.dumps(doc).encode('utf-8'))
    assert not proc.wait()
    (saved,) = mongodb_instance.get_connection().testdb.test_coll.find()
    saved.pop('_id')
    assert saved == doc
