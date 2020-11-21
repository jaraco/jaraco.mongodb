import random

import pytest


collect_ignore = [
    'jaraco/mongodb/pmxbot.py',
    # disable move-gridfs check, as it causes output capturing
    # to be disabled. See pytest-dev/pytest#3752.
    'jaraco/mongodb/move-gridfs.py',
]


@pytest.fixture(scope='function')
def database(request, mongodb_instance):
    """
    Return a clean MongoDB database suitable for testing.
    """
    db_name = request.node.name.replace('.', '_')
    database = mongodb_instance.get_connection()[db_name]
    yield database
    database.client.drop_database(db_name)


@pytest.fixture()
def bulky_collection(database):
    """
    Generate a semi-bulky collection with a few dozen random
    documents.
    """
    coll = database.bulky
    for _id in range(100):
        doc = dict(_id=_id, val=random.randint(1, 100))
        coll.insert_one(doc)
    return coll
