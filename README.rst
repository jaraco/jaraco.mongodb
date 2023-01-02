.. image:: https://img.shields.io/pypi/v/jaraco.mongodb.svg
   :target: https://pypi.org/project/jaraco.mongodb

.. image:: https://img.shields.io/pypi/pyversions/jaraco.mongodb.svg

.. image:: https://github.com/jaraco/skeleton/workflows/tests/badge.svg
   :target: https://github.com/jaraco/skeleton/actions?query=workflow%3A%22tests%22
   :alt: tests

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: Black

.. image:: https://readthedocs.org/projects/jaracomongodb/badge/?version=latest
   :target: https://jaracomongodb.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/badge/skeleton-2023-informational
   :target: https://blog.jaraco.com/skeleton

Migration Manager
=================

``jaraco.mongodb.migration`` implements the Migration Manager as featured
at the `MongoWorld 2016 <https://www.mongodb.com/world16>`_ presentation
`From the Polls to the Trolls
<https://combinatronics.com/yougov/mongoworld-2016/merged/index.html#/>`_.
Use it to load documents of various schema versions into a target version that
your application expects.

sessions
========

``jaraco.mongodb.sessions`` implements a CherryPy Sessions store backed by
MongoDB.

By default, the session store will handle sessions with any objects that can
be inserted into a MongoDB collection naturally.

To support richer objects, one may configure the codec to use ``jaraco.modb``.

fields
======

``jaraco.mongodb.fields`` provides two functions, encode and decode, which
take arbitrary unicode text and transform it into values suitable as keys
on older versions of MongoDB by backslash-escaping the values.

monitor-index-creation
======================

To monitor an ongoing index operation in a server, simply invoke:

    python -m jaraco.mongodb.monitor-index-creation mongodb://host/db

move-gridfs
===========

To move files from one gridfs collection to another, invoke:

    python -m jaraco.mongodb.move-gridfs --help

And follow the usage for moving all or some gridfs files and
optionally deleting the files after.

oplog
=====

This package provides an ``oplog`` module, which is based on the
`mongooplog-alt <https://github.com/asivokon/mongooplog-alt/>`_ project,
which itself is a Python remake of `official mongooplog utility
<https://docs.mongodb.com/manual/reference/program/mongooplog/>`_,
shipped with MongoDB starting from version 2.2 and deprecated in 3.2.
It reads oplog of a remote
server, and applies operations to the local server. This can be used to keep
independed replica set loosly synced in much the same way as Replica Sets
are synced, and may
be useful in various backup and migration scenarios.

``oplog`` implements basic functionality of the official utility and
adds following features:

* tailable oplog reader: runs forever polling new oplog event which is extremly
  useful for keeping two independent replica sets in almost real-time sync.

* option to sync only selected databases/collections.

* option to exclude one or more namespaces (i.e. dbs or collections) from
  being synced.

* ability to "rename" dbs/collections on fly, i.e. destination namespaces can
  differ from the original ones. This feature works on mongodb 1.8 and later.
  Official utility only supports version 2.2.x and higher.

* save last processed timestamp to file, resume from saved point later.


Invoke the command as a module script: ``python -m jaraco.mongodb.oplog``.

Command-line options
--------------------

Usage is as follows::

    $ python -m jaraco.mongodb.oplog  --help
    usage: oplog.py [--help] [--source host[:port]] [--oplogns OPLOGNS]
                    [--dest host[:port]] [-w WINDOW] [-f] [--ns [NS [NS ...]]]
                    [-x [EXCLUDE [EXCLUDE ...]]]
                    [--rename [ns_old=ns_new [ns_old=ns_new ...]]] [--dry-run]
                    [--resume-file FILENAME] [-s SECONDS] [-l LOG_LEVEL]

    optional arguments:
      --help                show usage information
      --source host[:port]  Hostname of the mongod server from which oplog
                            operations are going to be pulled. Called "--from" in
                            mongooplog.
      --oplogns OPLOGNS     Source namespace for oplog
      --dest host[:port]    Hostname of the mongod server (or replica set as <set
                            name>/s1,s2) to which oplog operations are going to be
                            applied. Default is "localhost". Called "--host" in
                            mongooplog.
      -w WINDOW, --window WINDOW
                            Time window to query, like "3 days" or "24:00" (24
                            hours, 0 minutes).
      -f, --follow          Wait for new data in oplog. Makes the utility polling
                            oplog forever (until interrupted). New data is going
                            to be applied immediately with at most one second
                            delay.
      --ns [NS [NS ...]]    Process only these namespaces, ignoring all others.
                            Space separated list of strings in form of ``dname``
                            or ``dbname.collection``. May be specified multiple
                            times.
      -x [EXCLUDE [EXCLUDE ...]], --exclude [EXCLUDE [EXCLUDE ...]]
                            List of space separated namespaces which should be
                            ignored. Can be in form of ``dname`` or
                            ``dbname.collection``. May be specified multiple
                            times.
      --rename [ns_old=ns_new [ns_old=ns_new ...]]
                            Rename database(s) and/or collection(s). Operations on
                            namespace ``ns_old`` from the source server will be
                            applied to namespace ``ns_new`` on the destination
                            server. May be specified multiple times.
      --dry-run             Suppress application of ops.
      --resume-file FILENAME
                            Read from and write to this file the last processed
                            timestamp.
      -l LOG_LEVEL, --log-level LOG_LEVEL
                            Set log level (DEBUG, INFO, WARNING, ERROR)

Example usages
--------------

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
-------

Tests for ``oplog`` are written in javascript using test harness
which is used for testing MongoDB iteself. You can run the oplog suite with::

    mongo tests/oplog.js

Tests produce alot of output. Succesful execution ends with line like this::

    ReplSetTest stopSet *** Shut down repl set - test worked ****

These tests are run as part of the continuous integration and release acceptance
tests in Travis.
