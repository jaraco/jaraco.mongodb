# coding: future-fstrings

"""
A MongoDB-backed CherryPy session store.

Although this module requires CherryPy, it does not impose the requirement
on the package, as any user of this module will already require CherryPy.

To enable these sessions, your code must call :meth:`Session.install()` and
then configure the CherryPy endpoint to use MongoDB sessions. For example::

    jaraco.mongodb.sessions.Session.install()

    session_config = {
        'sessions.on': True,
        'sessions.storage_type': 'MongoDB',
        'sessions.database': pymongo.MongoClient().database,
    }
    config = {
        '/': session_config,
    }

    cherrypy.quickstart(..., config=config)

The ``jaraco.modb`` module implements the codec interface, so may be used
to encode more complex objects in the session::

    session_config.update({
        'sessions.codec': jaraco.modb,
    })

"""

import datetime
import time
import logging
import pprint

import pymongo.errors
import cherrypy
import dateutil.tz

from . import timers
from . import compat

log = logging.getLogger(__name__)


class LockTimeout(RuntimeError):
    pass


class NullCodec(object):
    def decode(self, data):
        return data

    def encode(self, data):
        return data


class Session(cherrypy.lib.sessions.Session):
    """
    A MongoDB-backed CherryPy session store. Takes the following params:

        database: the pymongo Database object.
        collection_name: The name of the collection to use in the db.
        codec: An object with 'encode' and 'decode' methods, used to encode
            objects before saving them to MongoDB and decode them when loaded
            from MongoDB.
        lock_timeout: A timedelta or numeric seconds indicating how long
            to block acquiring a lock. If None (default), acquiring a lock
            will block indefinitely.
    """

    codec = NullCodec()
    "by default, objects are passed directly to MongoDB"

    def __init__(self, id, **kwargs):
        kwargs.setdefault('collection_name', 'sessions')
        kwargs.setdefault('lock_timeout', None)
        super(Session, self).__init__(id, **kwargs)
        self.setup_expiration()
        if isinstance(self.lock_timeout, (int, float)):
            self.lock_timeout = datetime.timedelta(seconds=self.lock_timeout)
        if not isinstance(self.lock_timeout, (datetime.timedelta, type(None))):
            msg = "Lock timeout must be numeric seconds or a timedelta instance."
            raise ValueError(msg)

    @classmethod
    def install(cls):
        """
        Add this session to the cherrypy session handlers. CherryPy looks
        for session classes in vars(cherrypy.lib.sessions) with a name
        in title-case followed by "Session".
        """
        cherrypy.lib.sessions.MongodbSession = cls

    @property
    def collection(self):
        return self.database[self.collection_name]

    def setup_expiration(self):
        """
        Use pymongo TTL index to automatically expire sessions.
        """
        self.collection.create_index(
            '_expiration_datetime',
            expireAfterSeconds=0,
        )

    def _exists(self):
        return bool(self.collection.find_one(self.id))

    def _load(self):
        filter = dict(
            _id=self.id,
            _expiration_datetime={'$exists': True},
        )
        projection = dict(_id=False)
        doc = self.collection.find_one(filter, projection)
        if not doc:
            return
        expiration_time = doc.pop('_expiration_datetime')
        doc = self.codec.decode(doc)
        return (doc, self._make_local(expiration_time))

    @staticmethod
    def _make_aware(local_datetime):
        return local_datetime.replace(tzinfo=dateutil.tz.tzlocal())

    @staticmethod
    def _make_utc(local_datetime):
        return Session._make_aware(local_datetime).astimezone(dateutil.tz.tzutc())

    @staticmethod
    def _make_local(utc_datetime):
        """
        For a naive utc_datetime, return the same time in the local timezone
        (also naive).
        """
        return (
            utc_datetime.replace(tzinfo=dateutil.tz.tzutc())
            .astimezone(dateutil.tz.tzlocal())
            .replace(tzinfo=None)
        )

    def _save(self, expiration_datetime):
        data = dict(self._data)
        data = self.codec.encode(data)
        # CherryPy defines the expiration in local time, which may be
        #  different for some hosts. Convert it to UTC before sticking
        #  it in the database.
        expiration_datetime = self._make_utc(expiration_datetime)
        data.update(
            _expiration_datetime=expiration_datetime,
            _id=self.id,
        )
        try:
            compat.save(self.collection, data)
        except pymongo.errors.InvalidDocument:
            log.warning(
                "Unable to save session:\n%s",
                pprint.pformat(data),
            )
            raise

    def _delete(self):
        self.collection.delete_one(self.id)

    def acquire_lock(self):
        """
        Acquire the lock. Blocks indefinitely until lock is available
        unless `lock_timeout` was supplied. If the lock_timeout elapses,
        raises LockTimeout.
        """
        # first ensure that a record exists for this session id
        try:
            self.collection.insert_one(dict(_id=self.id))
        except pymongo.errors.DuplicateKeyError:
            pass
        unlocked_spec = dict(_id=self.id, locked=None)
        lock_timer = (
            timers.Timer.after(self.lock_timeout)
            if self.lock_timeout
            else timers.NeverExpires()
        )
        while not lock_timer.expired():
            locked_spec = {'$set': dict(locked=datetime.datetime.utcnow())}
            res = self.collection.update_one(unlocked_spec, locked_spec)
            if res.raw_result['updatedExisting']:
                # we have the lock
                break
            time.sleep(0.1)
        else:
            raise LockTimeout(f"Timeout acquiring lock for {self.id}")
        self.locked = True

    def release_lock(self):
        record_spec = dict(_id=self.id)
        self.collection.update_one(record_spec, {'$unset': {'locked': 1}})
        # if no data was saved (no expiry), remove the record
        record_spec.update(_expiration_datetime={'$exists': False})
        self.collection.delete_one(record_spec)
        self.locked = False

    def __len__(self):
        return self.collection.count()
