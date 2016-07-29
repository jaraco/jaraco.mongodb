4.1
===

``oplog`` command now accepts multiple indications of the
following arguments::

 - --ns
 - --exclude
 - --rename

See the docstring for the implications of this change.

4.0
===

Drop support for Python 3.2.

3.18.1
======

Add helper module to docs.

3.18
====

Added ``sharding`` module with ``create_db_in_shard``
function and pmxbot command.

3.17
====

Add Trove classifier for Pytest Framework.

3.16
====

Extract migration manager functionality from YouGov's
cases migration.

3.15.2
======

Correct syntax error.

3.15.1
======

Set a small batch size on fs query for move-gridfs to
prevent the cursor timing out while chunks are moved.

3.15
====

Add ``jaraco.mongodb.move-gridfs`` command.

3.14
====

Exposed ``mongod_args`` on ``MongoDBInstance``
and ``MongoDBReplicaSet``.

Allow arbitrary arguments to be included as mongodb
args with pytest plugin. For example::

    py.test --mongod-args=--storageEngine=wiredTiger

3.13
====

Added ``manage`` module with support for purging all databases.
Added ``.purge_all_databases`` to MongoDBInstance.

3.12
====

Minor usability improvements in monitor-index-creation script.

3.11
====

Better error reporting in mongodb_instance fixture.

3.10
====

MongoDBInstance now allows for a ``.soft_stop`` and subsequent ``.start``
to restart the instance against the same data_dir.

3.8
===

``repair-gridfs`` command now saves documents before removing
files.

3.7
===

Add ``helper.connect_gridfs`` function.

Add script for removing corrupt GridFS files:
``jaraco.mongodb.repair-gridfs``.

3.6
===

Add ``helper`` and ``uri`` modules with functions to facilitate common
operations in PyMongo.

3.5
===

Add script for checking GridFS. Invoke with
``python -m jaraco.mongodb.check-gridfs``.

3.4
===

#1: Rename a namespace in index operations.

3.3
===

Add a ``dry-run`` option to suppress application of operations.

3.0
===

Oplog command no longer accepts '-h', '--host', '--to', '--port', '-p',
or '--from', but
instead accepts '--source' and '--dest' options for specifying source
and destination hosts/ports.

2.8
===

Adopt abandoned ``mongooplog_alt`` as ``jaraco.mongodb.oplog``.

2.7
===

Support PyMongo 2.x and 3.x.

2.6
===

Adopted ``service`` module from jaraco.test.services.

2.4
===

Add ``testing.assert_distinct_covered``.

2.3
===

Add ``query.compat_explain``, providing forward compatibility
for MongoDB 3.0 `explain changes
<http://docs.mongodb.org/v3.0/reference/explain-results/>`_.

``testing.assert_covered`` uses compat_explain for MongoDB 3.0
compatibility.

2.2
===

Add query module with ``project`` function.

2.0
===

Removed references to ``jaraco.modb``. Instead, allow the Sessions object to
accept a ``codec`` parameter. Applications that currently depend on the
``use_modb`` functionality must instead use the following in the config::

    "sessions.codec": jaraco.modb

1.0
===

Initial release, introducing ``sessions`` module based on ``yg.mongodb`` 2.9.
