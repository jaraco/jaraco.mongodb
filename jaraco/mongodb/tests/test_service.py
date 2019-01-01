import datetime

import pymongo
import pytest
from tempora import timing

from jaraco.mongodb import service


def test_MongoDBReplicaSet_writable():
    rs = service.MongoDBReplicaSet()
    rs.start()
    try:
        conn = pymongo.MongoClient(rs.get_connect_hosts())
        conn.database.collection.insert_one({'foo': 'bar'})
    finally:
        rs.stop()


def test_MongoDBReplicaSet_starts_quickly():
    pytest.skip("Takes 20-30 seconds")
    sw = timing.Stopwatch()
    rs = service.MongoDBReplicaSet()
    rs.start()
    try:
        elapsed = sw.split()
        limit = datetime.timedelta(seconds=5)
        assert elapsed < limit
    finally:
        rs.stop()


def test_fixture(mongodb_instance):
    "Cause the fixture to be invoked"
    pass
