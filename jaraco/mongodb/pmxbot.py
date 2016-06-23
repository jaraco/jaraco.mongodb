import shlex

import pmxbot

from . import sharding


@pmxbot.core.command("create-db-in-shard")
def cdbs(client, event, channel, nick, rest):
        """
        Create a database in a shard. !create-db-in-shard {db name} {shard name}
        """
        db_name, shard = shlex.split(rest)
        return sharding.create_db_in_shard(db_name, shard)
