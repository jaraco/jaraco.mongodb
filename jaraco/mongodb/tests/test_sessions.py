import datetime
import functools
import importlib

import dateutil
import pytest

pytest.importorskip("cherrypy")
sessions = importlib.import_module('jaraco.mongodb.sessions')


@pytest.fixture(scope='function')
def database(request, mongodb_instance):
    """
    Return a MongoDB database suitable for testing auth. Remove the
    collection between every test.
    """
    database = mongodb_instance.get_connection().sessions_test
    request.addfinalizer(functools.partial(database.sessions.delete_many, {}))
    return database


class TestSessions(object):
    def test_time_conversion(self):
        local_time = datetime.datetime.now().replace(microsecond=0)
        local_time = sessions.Session._make_aware(local_time)
        utc_aware = datetime.datetime.utcnow().replace(
            tzinfo=dateutil.tz.tzutc(), microsecond=0
        )
        assert local_time == utc_aware

    def test_time_conversion2(self):
        local_time = datetime.datetime.now().replace(microsecond=0)
        round_local = sessions.Session._make_local(
            sessions.Session._make_utc(local_time)
        )
        assert round_local == local_time
        assert round_local.tzinfo is None

    def test_session_persists(self, database):
        session = sessions.Session(None, database=database)
        session['x'] = 3
        session['y'] = "foo"
        session.save()
        session_id = session.id
        del session
        session = sessions.Session(session_id, database=database)
        assert session['x'] == 3
        assert session['y'] == 'foo'

    def test_locked_session(self, database):
        session = sessions.Session(None, database=database)
        session.acquire_lock()
        session['x'] = 3
        session['y'] = "foo"
        session.save()
        session_id = session.id
        del session
        session = sessions.Session(session_id, database=database)
        assert session['x'] == 3

    @pytest.mark.xfail
    def test_numeric_keys(self, database):
        session = sessions.Session(None, database=database, use_modb=True)
        session.acquire_lock()
        session[3] = 9
        session.save()
        session_id = session.id
        del session
        session = sessions.Session(session_id, database=database, use_modb=True)
        assert 3 in session
        assert session[3] == 9
