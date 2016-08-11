jaraco.mongodb
==============

.. image:: https://img.shields.io/pypi/v/jaraco.mongodb.svg
   :target: https://pypi.org/project/jaraco.mongodb

.. image:: https://img.shields.io/pypi/pyversions/jaraco.mongodb.svg

.. image:: https://img.shields.io/pypi/dm/jaraco.mongodb.svg

.. image:: https://img.shields.io/travis/jaraco/jaraco.mongodb/master.svg
   :target: http://travis-ci.org/jaraco/jaraco.mongodb

migration manager
-----------------

``jaraco.mongodb.migration`` implements the Migration Manager as featured
at the `MongoWorld 2016 <https://www.mongodb.com/world16>`_ presentation
`From the Polls to the Trolls
<https://rawgit.com/yougov/mongoworld-2016/merged/index.html>`_. Use
it to load documents of various schema versions into a target version that
your application expects.

sessions
--------

``jaraco.mongodb.sessions`` implements a CherryPy Sessions store backed by
MongoDB.

By default, the session store will handle sessions with any objects that can
be inserted into a MongoDB collection naturally.

To support richer objects, one may configure the codec to use ``jaraco.modb``.

monitor-index-creation
----------------------

To monitor an ongoing index operation in a server, simply invoke:

    python -m jaraco.mongodb.monitor-index-creation mongodb://host/db

move-gridfs
-----------

To move files from one gridfs collection to another, invoke:

    python -m jaraco.mongodb.move-gridfs --help

And follow the usage for moving all or some gridfs files and
optionally deleting the files after.

oplog
-----

This package provides an ``oplog`` module, which is based on the
`mongooplog-alt <https://github.com/asivokon/mongooplog-alt/>`_ project,
which itself is a Python remake of `official mongooplog utility`_,
shipped with MongoDB starting from version 2.2.0. It reads oplog of a remote
server, and applies operations to the local server. This can be used to keep
independed replica set loosly synced in a sort of one way replication, and may
be useful in various backup and migration scenarios.

``oplog`` implements basic functionality of the official utility and
adds following features:

* tailable oplog reader: runs forever polling new oplog event which is extremly
  useful for keeping two independent replica sets in almost real-time sync.

* option to sync only selected databases/collections.

* option to exclude one or more namespaces (i.e. dbs or collections) from
  being synced.

* ability to "rename" dbs/collections on fly, i.e. destination namespaces can
  differ from the original ones. This feature

* works on mongodb 1.8 and later. Official utility only supports
  version 2.2.x and higher.

* save last processed timestamp to file, resume from saved point later.


.. _official mongooplog utility: http://docs.mongodb.org/manual/reference/mongooplog/

Invoke the command as a module script: ``python -m jaraco.mongodb.oplog``.

Command-line options
********************

Options common to original ``mongooplog``::

  --source <hostname><:port>
    Hostname of the mongod server from which oplog operations are going to be
    pulled. Called "--from" in mongooplog.

  --dest <hostname><:port>, -h

    Hostname of the mongod server to which oplog operations are going to be
    applied. Default is "localhost". Called "--host" in mongooplog.

  --port <number>

    Port of the mongod server to which oplog operations are going to be
    applied, if not specified in ``--host``. Default is 27017.

  -s SECONDS, --seconds SECONDS

    seconds to go back. If not set, try read timestamp from --resume-file.
    If the file not found, assume --seconds=86400 (24 hours)


Options specific to this implementation::

 --to
   An alias for ``--host``.

 --follow, -f

   Wait for new data in oplog. Makes the utility polling oplog forever (until
   interrupted). New data is going to be applied immideately with at most one
   second delay.

 --exclude, -x

    List of space separated namespaces which should be ignored. Can be in form
    of ``dname`` or ``dbname.collection``. May be specified multiple times.

  --ns

    Process only these namespaces, ignoring all others. Space separated list of
    strings in form of ``dname`` or ``dbname.collection``. May be specified
    multiple times.

  --rename [ns_old=ns_new [ns_old=ns_new ...]]

    Rename database(s) and/or collection(s). Operations on namespace ``ns_old``
    from the source server will be applied to namespace ``ns_new`` on the
    destination server. May be specified multiple times.

  --resume-file FILENAME

    resume from timestamp read from this file and write last processed
    timestamp back to this file (default is mongooplog.ts).
    Pass empty string or 'none' to disable this feature.


Example usages
**************

Consider the following sample usage::

    python -m jaraco.mongodb.oplog --source prod.example.com:28000 --dest dev.example.com:28500 -f --exclude logdb data.transactions --seconds 600

This command is going to take operations from the last 10 minutes from prod,
and apply them to dev. Database ``logdb`` and collection ``transactions`` of
``data`` database will be omitted. After operations for the last minutes will
be applied, command will wait for new changes to come, keep running until
Ctrl+C or other termination signal recieved.

The tool provides a ``--dry-run`` option and when logging at the DEBUG level will
emit the oplog entries. Combine these to use the tool as an oplog cat tool::

    $ python -m jaraco.mongodb.oplog --dry-run -s 0 -f --source prod.example.com --ns survey_tabs -l DEBUG


Testing
=======

|BuildStatus|_

.. |BuildStatus| image:: https://secure.travis-ci.org/jaraco/jaraco.mongodb.png
.. _BuildStatus: http://travis-ci.org/jaraco/jaraco.mongodb

Tests for ``oplog`` are written in javascript using test harness
which is used for testing MongoDB iteself. You can run the whole suite with::

    mongo tests/suite.js

Note, that you will need existing writable ``/data/db`` dir.

Tests produce alot of output. Succesful execution ends with line like this::

    ReplSetTest stopSet *** Shut down repl set - test worked ****
