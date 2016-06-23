import socket
import operator

import pymongo
from jaraco.text import namespace_format as nf

hostname = socket.gethostname()
by_id = operator.itemgetter('_id')


def get_ids(collection):
        return map(by_id, collection.find(projection=['_id']))


def create_db_in_shard(db_name, shard, client=None):
        """
        In a sharded cluster, create a database in a particular shard.
        """
        client = client or pymongo.MongoClient()
        # flush the router config to ensure it's not stale
        res = client.admin.command('flushRouterConfig')
        if not res.get('ok'):
                raise RuntimeError("unable to flush router config")
        if shard not in get_ids(client.config.shards):
                raise ValueError(nf("Unknown shard {shard}"))
        if db_name in get_ids(client.config.databases):
                raise ValueError("database already exists")
        # MongoDB doesn't have a 'create database' command, so insert an
        #  item into a collection and then drop the collection.
        client[db_name].foo.insert({'foo': 1})
        client[db_name].foo.drop()
        if client[db_name].collection_names():
                raise ValueError("database has collections")
        res = client.admin.command('movePrimary', value=db_name, to=shard)
        if not res.get('ok'):
                raise RuntimeError(str(res))
        return nf("Successfully created {db_name} in {shard} via {hostname}")
