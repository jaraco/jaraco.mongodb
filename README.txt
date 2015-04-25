jaraco.mongodb
==============

`Documentation <https://pythonhosted.org/jaraco.mongodb>`_

Provides support for MongoDB environments.

sessions
--------

``jaraco.mongodb.sessions`` implements a CherryPy Sessions store backed by
MongoDB.

By default, the session store will handle sessions with any objects that can
be inserted into a MongoDB collection naturally.

To support richer objects, one may configure the codec to use ``jaraco.modb``.
