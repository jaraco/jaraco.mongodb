mongooplog-alt
==============

About
-----

**mongooplog-alt** is the Python remake of `official mongooplog utility`_,
shipped with MongoDB starting from version 2.2.0. It reads oplog of a remote
server, and applies operations to the local server. This can be used to keep
independed replica set loosly synced in a sort of one way replication, and may
be useful in various backup and migration scenarios.

``mongooplog-alt`` implements basic functionality of the official utility and
adds following features:

* tailable oplog reader: runs forever polling new oplog event which is extremly
  useful for keeping two independent replica sets in almost real-time sync.

* option to exclude one or more namespaces (i.e. dbs or collections) from
  being synced.

* works on mongodb 1.8.x, 2.0.x, and 2.2.x. Official utility supports 2.2.x
  only.

* at the time of writing (2.2.0), official ``mongooplog`` suffers from bug that
  limits its usage with replica sets (https://jira.mongodb.org/browse/SERVER-6915)


.. _official mongooplog utility: http://docs.mongodb.org/manual/reference/mongooplog/


Installation
------------

Using pip (preferred)::

    pip install --upgrade mongooplog-alt

Using easy_install::

    easy_install -U mongooplog-alt


Command-line options
--------------------

Options common to original ``mongooplog``::

 --from <hostname><:port>
    Hostname of the mongod server from which oplog operations are going to be
    pulled.

 --host <hostname><:port>, -h

    Hostname of the mongod server to which oplog operations are going to be
    applied. Default is "localhost"

 --port <number>

    Port of the mongod server to which oplog operations are going to be
    applied, if not specified in ``--host``. Default is 27017.

 --seconds <number>
    
    Number of seconds of latest operations to pull from the remote host.
    Default is 86400, or 24 hours.


Options specific to ``mongooplog-alt``::

 --follow, -f

   Wait for new data in oplog. Makes the utility polling oplog forever (until
   interrupted). New data is going to be applied immideately with at most one
   second delay.

 --exclude, -x

    List of space separated namespaces which should be ignored. Can be in form
    of ``dname`` or ``dbname.collection``.

  --ns

    Process only these namespaces, ignoring all others. Space separated list of
    strings in form of ``dname`` or ``dbname.collection``.

  --rename [ns_old=ns_new [ns_old=ns_new ...]]

    Rename database(s) and/or collection(s). Operations on namespace ``ns_old``
    from the source server will be applied to namespace ``ns_new`` on the
    destination server.


Usage
-----

Consider the following sample usage::

    mongooplog-alt --from prod.example.com:28000 --host dev.example.com:28500 -f --exclude logdb data.transactions --seconds 600

This command is going to take operations from the last 10 minutes from prod,
and apply them to dev. Database ``logdb`` and collection ``transactions`` of
``data`` database will be omitted. After operations for the last minutes will
be applied, command will wait for new changes to come, keep running until
Ctrl+C or other termination signal recieved.


Testing
-------

Tests for ``mongooplog-alt`` are written in javascript using test harness
which is used for testing MongoDB iteself. You can run the whole suite with::

    mongo tests/suite.js

Note, that you will need existing writable ``/data/db`` dir.

Tests produce alot of output. Succesfull execution ends with line like this::

    ReplSetTest stopSet *** Shut down repl set - test worked ****

