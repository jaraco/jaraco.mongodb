import datetime

import pymongo
import pytest
from tempora import timing

from jaraco.mongodb import service


@pytest.mark.xfail(reason="#31")
def test_MongoDBReplicaSet_writable():
    rs = service.MongoDBReplicaSet()
    with rs.run():
        conn = pymongo.MongoClient(rs.get_connect_hosts())
        conn.database.collection.insert_one({'foo': 'bar'})


def test_MongoDBReplicaSet_starts_quickly():
    pytest.skip("Takes 20-30 seconds")
    sw = timing.Stopwatch()
    rs = service.MongoDBReplicaSet()
    with rs.run():
        elapsed = sw.split()
        limit = datetime.timedelta(seconds=5)
        assert elapsed < limit


def test_fixture(mongodb_instance):
    "Cause the fixture to be invoked"
    pass
