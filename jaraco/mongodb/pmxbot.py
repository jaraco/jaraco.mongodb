import contextlib
import shlex

import pmxbot.storage

from . import sharding


class Storage(pmxbot.storage.SelectableStorage, pmxbot.storage.MongoDBStorage):
    collection_name = 'unused'


def get_client():
    """
    Use the same MongoDB client as pmxbot if available.
    """
    with contextlib.suppress(Exception):
        store = Storage.from_URI()
        assert isinstance(store, pmxbot.storage.MongoDBStorage)
        return store.db.database.client


@pmxbot.core.command("create-db-in-shard")
def cdbs(client, event, channel, nick, rest):
    """
    Create a database in a shard. !create-db-in-shard {db name} {shard name}
    """
    db_name, shard = shlex.split(rest)
    return sharding.create_db_in_shard(db_name, shard, client=get_client())
