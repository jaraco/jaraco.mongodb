"""
A MongoDB-backed CherryPy session store.

Although this module requires CherryPy, it does not impose the requirement
on the package, as any user of this module will already require CherryPy.
"""

import importlib
import datetime
import time
import logging
import pprint

import pymongo.errors
import cherrypy
import dateutil.tz

from . import timers

log = logging.getLogger(__name__)

class LockTimeout(RuntimeError): pass

class Session(cherrypy.lib.sessions.Session):
	"""
	A MongoDB-backed CherryPy session store. Takes the following params:

		database: the pymongo Database object.
		collection_name: The name of the collection to use in the db.
		use_modb: Use `jaraco.modb` package to encode/decode values.
		lock_timeout: A timedelta or numeric seconds indicating how long
			to block acquiring a lock. If None (default), acquiring a lock
			will block indefinitely.
	"""
	def __init__(self, id, **kwargs):
		kwargs.setdefault('collection_name', 'sessions')
		kwargs.setdefault('use_modb', False)
		kwargs.setdefault('lock_timeout', None)
		super(Session, self).__init__(id, **kwargs)
		self.setup_expiration()
		if self.use_modb:
			modb = importlib.import_module('jaraco.modb')
			self.encode = modb.encode
			self.decode = modb.decode
		if isinstance(self.lock_timeout, (int, float)):
			self.lock_timeout = datetime.timedelta(seconds=self.lock_timeout)
		if not isinstance(self.lock_timeout, (datetime.timedelta, type(None))):
			raise ValueError("Lock timeout must be numeric seconds or "
				"a timedelta instance.")

	# by default (unless modb is enabled), encode/decode is a no-op.
	encode = decode = staticmethod(lambda data: data)

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
		self.collection.ensure_index('_expiration_datetime',
			expireAfterSeconds=0)

	def _exists(self):
		return bool(self.collection.find_one(self.id))

	def _load(self):
		doc = self.collection.find_one(dict(
			_id=self.id,
			_expiration_datetime = {'$exists': True},
			),
			fields=dict(_id=False),
		)
		if not doc: return
		expiration_time = doc.pop('_expiration_datetime')
		doc = self.decode(doc)
		return (doc, self._make_local(expiration_time))

	@staticmethod
	def _make_aware(local_datetime):
		return local_datetime.replace(tzinfo = dateutil.tz.tzlocal())

	@staticmethod
	def _make_utc(local_datetime):
		return Session._make_aware(local_datetime).astimezone(
			dateutil.tz.tzutc()
		)

	@staticmethod
	def _make_local(utc_datetime):
		"""
		For a naive utc_datetime, return the same time in the local timezone
		(also naive).
		"""
		return utc_datetime.replace(
			tzinfo = dateutil.tz.tzutc()
		).astimezone(dateutil.tz.tzlocal()).replace(
			tzinfo = None
		)

	def _save(self, expiration_datetime):
		data = dict(self._data)
		data = self.encode(data)
		# CherryPy defines the expiration in local time, which may be
		#  different for some hosts. Convert it to UTC before sticking
		#  it in the database.
		expiration_datetime = self._make_utc(expiration_datetime)
		data.update(
			_expiration_datetime = expiration_datetime,
			_id = self.id,
		)
		try:
			self.collection.save(data)
		except pymongo.errors.InvalidDocument:
			log.warning("Unable to save session:\n%s",
				pprint.pformat(data))
			raise

	def _delete(self):
		self.collection.remove(self.id)

	def acquire_lock(self):
		"""
		Acquire the lock. Blocks indefinitely until lock is available
		unless `lock_timeout` was supplied. If the lock_timeout elapses,
		raises LockTimeout.
		"""
		# first ensure that a record exists for this session id
		try:
			self.collection.insert(dict(_id=self.id), safe=True)
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
			res = self.collection.update(unlocked_spec, locked_spec, safe=True)
			if res['updatedExisting']:
				# we have the lock
				break
			time.sleep(0.1)
		else:
			raise LockTimeout("Timeout acquiring lock for {self.id}"
				.format(**vars()))
		self.locked = True

	def release_lock(self):
		record_spec = dict(_id=self.id)
		self.collection.update(record_spec, {'$unset': {'locked': 1}})
		# if no data was saved (no expiry), remove the record
		record_spec.update(_expiration_datetime={'$exists': False})
		self.collection.remove(record_spec)
		self.locked = False

	def __len__(self):
		return self.collection.count()
