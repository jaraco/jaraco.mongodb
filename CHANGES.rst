v11.2.1
=======

#27: In oplog module, once again support createIndex operations
even on MongoDB 4.4 and later.

v11.2.0
=======

Rely on native f-strings and remove dependency on future-fstrings.

v11.1.0
=======

#22: The pytest fixture now honors ``--mongodb-uri`` or
the environment variable ``MONGODB_URL`` to run tests
against an existing instance of MongoDB rather than starting
up a new one.

v11.0.1
=======

Rely on PEP 420 for namespace package.

v11.0.0
=======

Require Python 3.6 or later.

#26: Removed ``--noprealloc`` and ``--smallfiles`` from
MongoDBReplicaSet class, restoring compatibility on
later MongoDB releases.

10.3.0
======

Added ``jaraco.mongodb.sampling`` with the new
``estimate`` function for estimating the count of
objects matching a query.

10.2.0
======

Remove dependency on ``namespace_format`` from
(otherwise pinned) ``jaraco.text`` and instead rely
on ``future-fstrings`` to provide for f-strings on
supported Python versions.

10.1.3
======

#25: Pin dependency on jaraco.text 2.x to avoid error.

10.1.2
======

Fixed DeprecationWarning in assert_distinct_covered.

10.1.1
======

Fix a couple of deprecation warnings, including an emergent
one on recent pytest versions.

10.1
====

Add ``codec`` module with support for parsing dates from
JSON input, suitable for making queries.

10.0
====

Switch to `pkgutil namespace technique
<https://packaging.python.org/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages>`_
for the ``jaraco`` namespace.

9.4
===

``create_database_in_shard`` now also reports the 'nodes'
on which the database was created.

9.3
===

Added ``testing.assert_index_used`` function.

9.2.1
=====

Removed deprecation of ``helper.connect_db``, as the
upstream implementation still doesn't provide for a
nice 'default'.

9.2
===

Disabled and deprecated ``helper.filter_warnings``.

Deprecated ``helper.connect``.

Deprecated ``helper.connect_db`` in favor of functions
now available in pymongo 3.5.

Added ``helper.get_collection``.

9.1
===

#21: In ``mongodb_instance`` fixture, allow ``--port`` to be
passed as mongod args, overriding default behavior of starting
on an ephemeral port.

9.0
===

Refreshed project metadata, including conversion to declarative
config. Requires Setuptools 34.4 to install from sdist.

8.1
===

In ``query.upsert_and_fetch``, allow keyword arguments to pass
to the underlying call.

Fix return value in ``query.upsert_and_fetch``.

8.0
===

MongoDB Instances are now started with
``--storageEngine ephemeralForTest`` instead of deferring to
the default storage engine. As a result, these options have
also been removed from the mongod invocation:

 - noprealloc
 - nojournal
 - syncdelay
 - noauth

This change also means that the ``soft_stop`` method has no
benefit and so has been removed.

7.10
====

MongoDBInstances will no longer attempt to store their data in
the root of the virtualenv (if present). Instead, they
unconditionally use a temp directory.

7.9
===

#12: Ensure indexes when moving files using ``move-gridfs`` script.

7.8
===

#19: Added Python 2 compatibility to the ``monitor-index-creation``
script.

7.7
===

Added ``compat.Collection`` with ``save`` method added in 6.2.

7.6
===

No longer pass ``--ipv6`` to mongod in MongoDBInstance. IPv6
is supported since MongoDB 3.0 without this option, and in
some environments, supplying this parameter causes the daemon
to fail to bind to any interfaces.

7.5
===

Added ``jaraco.mongodb.insert-doc`` to take a JSON document
from the command-line and insert it into the indicated collection.

7.4
===

#18: Allow pmxbot command to connect to the MongoDB database
other than localhost.

7.3
===

Add ``jaraco.mongodb.fields`` for escaping values for document
fields.

7.2.3
=====

#17: Remove ``--nohttpinterface`` when constructing MongoDB
instances, following the `same approach taken by MongoDB
<https://jira.mongodb.org/browse/TOOLS-1679>`_.

7.2.2
=====

#16: Fixed monitor-index-creation script for MongoDB 3.2+.

7.2.1
=====

Corrected oplog replication issues for MongoDB 3.6 (#13,
#14).

7.2
===

Moved ``Extend`` action in oplog module to
`jaraco.ui <https://pypi.org/project/jaraco.ui>`_ 1.6.

7.1
===

In ``move-gridfs``, explicitly handle interrupt to allow a
move to complete and only stop between moves.

7.0.2
=====

Fix AttributeError in ``move-gridfs`` get_args.

7.0.1
=====

Miscellaneous packaging fixes.

7.0
===

Removed support for ``seconds`` argument to ``oplog``
command.

6.4
===

``move-gridfs`` now accepts a limit-date option, allowing
for the archival of files older than a certain date.

6.3.1
=====

#11: With save, only use replace when an _id is specified.

6.3
===

#10: MongoDBInstance now passes the subprocess output
through to stderr and stdout. Callers should either
capture this output separately (such as pytest already
does) or set a ``.process_kwargs`` property on the
instance to customize the ``stdout`` and/or ``stderr``
parameters to Popen.

6.2.1
=====

Use portend for finding available local port, eliminating
remaining DeprecationWarnings.

6.2
===

Add compat module and ``compat.save`` method for
supplying the ``Collection.save`` behavior, deprecated
in PyMongo.

Updated PyMongo 3.0 API usage to eliminate
DeprecationWarnings.

6.1.1
=====

#9: Fix issue with MongoDBInstance by using
``subprocess.PIPE`` for stdout. Users may read from
this pipe by reading ``instance.process.stdout``.

6.1
===

Now, suppress creation of MongoDBInstance log file in
fixture and MongoDBInstance service.

6.0
===

Removed workarounds module.

5.6
===

Added workarounds module with ``safe_upsert_27707``.

5.5
===

No longer startup MongoDBInstance with
``textSearchEnabled=true``, fixing startup on MongoDB 3.4
and dropping implicit support for text search on MongoDB 2.4.

#7: Oplog tool now supports MongoDB 3.4 for the tested
use cases.

5.4
===

``assert_covered`` now will fail when the candidate cursor
returns no results, as that's almost certainly not an effective
assertion.

5.3
===

Nicer rendering of operations in the oplog tool.

In ``testing`` module, assertions now return the objects
on which they've asserted (for troubleshooting or additional
assertions).

5.2.1
=====

#6: Oplog tool will now include, exclude, and apply namespace
renames on 'renameCollection' commands.

5.2
===

Oplog tool no longer has a default window of 86400 seconds,
but instead requires that a window or valid resume file
be specified. Additionally, there is no longer a default
resume file (avoiding potential issues with multiple
processes writing to the same file).

Oplog tool now accepts a ``--window`` argument, preferred
to the now deprecated ``--seconds`` argument. Window
accepts simple time spans, like "3 days" or "04:20" (four
hours, twenty minutes). See the docs for `pytimeparse
<https://github.com/wroberts/pytimeparse>`_ for specifics
on which formats are supported.

5.1.1
=====

Fix version reporting when invoked with ``-m``.

5.1
===

Oplog tool no longer defaults to ``localhost`` for the dest,
but instead allows the value to be None. When combined with
``--dry-run``, dest is not needed and a connection is only
attempted if ``--dest`` is indicated.

Oplog tool now logs the name and version on startup.

5.0
===

Removed ``oplog.increment_ts`` and ``Timestamp.next`` operation
(no longer needed).

Ensure that ts is a oplog.Timestamp during ``save_ts``.

4.4
===

#3: ``create_db_in_shard`` no longer raises an exception when
the database happens to be created in the target shard.

#5: Better MongoDB 3.2 support for oplog replication.

Tests in continuous integration are now run against MongoDB
2.6, 3.0, and 3.2.

4.3
===

Oplog replay now warns if there are no operations preceding
the cutoff.

4.2.2
=====

#2: Retain key order when loading Oplog events for replay.

4.2.1
=====

Avoid race condition if an operation was being applied
when sync was cancelled.

4.2
===

``oplog`` now reports the failed operation when an oplog
entry fails to apply.

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
