import os
import sys
import tempfile
import subprocess
import glob
import collections
import importlib
import shutil
import functools
import logging
import datetime

import portend
from jaraco.services import paths
from jaraco import services
from jaraco import timing
from . import manage


log = logging.getLogger(__name__)


class MongoDBFinder(paths.PathFinder):
    windows_installed = glob.glob('/Program Files/MongoDB/Server/???/bin')
    windows_paths = [
        # symlink Server/current to Server/X.X
        '/Program Files/MongoDB/Server/current/bin',
        # symlink MongoDB to mongodb-win32-x86_64-2008plus-X.X.X-rcX
        '/Program Files/MongoDB/bin',
    ] + list(reversed(windows_installed))
    heuristic_paths = [
        # on the path
        '',
        # 10gen Debian package
        '/usr/bin',
        # custom install in /opt
        '/opt/mongodb/bin',
    ] + windows_paths

    # allow the environment to stipulate where mongodb must
    #  be found.
    env_paths = [
        os.path.join(os.environ[key], 'bin')
        for key in ['MONGODB_HOME']
        if key in os.environ
    ]
    candidate_paths = env_paths or heuristic_paths
    exe = 'mongod'
    args = ['--version']

    @classmethod
    def find_binary(cls):
        return os.path.join(cls.find_root(), cls.exe)


class MongoDBService(MongoDBFinder, services.Subprocess, services.Service):
    port = 27017

    @services.Subprocess.PortFree()
    def start(self):
        super(MongoDBService, self).start()
        # start the daemon
        mongodb_data = os.path.join(sys.prefix, 'var', 'lib', 'mongodb')
        cmd = [
            self.find_binary(),
            '--dbpath=' + mongodb_data,
        ]
        self.process = subprocess.Popen(cmd, stdout=self.get_log())
        self.wait_for_pattern('waiting for connections on port (?P<port>\d+)')
        log.info('%s listening on %s', self, self.port)

is_virtualenv = lambda: hasattr(sys, 'real_prefix')

class MongoDBInstance(MongoDBFinder, services.Subprocess, services.Service):
    data_dir = None

    mongod_args = (
        '--noprealloc',
        '--nojournal',
        '--nohttpinterface',
        '--syncdelay', '0',
        '--ipv6',
        '--noauth',
        '--setParameter', 'textSearchEnabled=true',
    )

    @staticmethod
    def get_data_dir():
        data_dir = None
        if is_virtualenv():
            # use the virtualenv as a base to store the data
            data_dir = os.path.join(sys.prefix, 'var', 'data')
            if not os.path.isdir(data_dir):
                os.makedirs(data_dir)
        return tempfile.mkdtemp(dir=data_dir)

    def start(self):
        super(MongoDBInstance, self).start()
        self.data_dir = self.data_dir or self.get_data_dir()
        if not hasattr(self, 'port') or not self.port:
            self.port = self.find_free_port()
        cmd = [
            self.find_binary(),
            '--dbpath', self.data_dir,
            '--port', str(self.port),
        ] + list(self.mongod_args)
        if hasattr(self, 'bind_ip') and not '--bind_ip' in cmd:
            cmd.extend(['--bind_ip', self.bind_ip])
        self.process = subprocess.Popen(cmd, stdout=self.get_log())
        portend.occupied('localhost', self.port, timeout=3)
        log.info('{self} listening on {self.port}'.format(**locals()))

    def get_connection(self):
        pymongo = importlib.import_module('pymongo')
        return pymongo.MongoClient('localhost', self.port)

    def purge_all_databases(self):
        manage.purge_all_databases(self.get_connection())

    def get_connect_hosts(self):
        return ['localhost:{self.port}'.format(**locals())]

    def get_uri(self):
        return 'mongodb://' + ','.join(self.get_connect_hosts())

    def stop(self):
        super(MongoDBInstance, self).stop()
        shutil.rmtree(self.data_dir)
        del self.data_dir

    def soft_stop(self):
        """
        Stop the process, but retain the data_dir.
        """
        super(MongoDBInstance, self).stop()


class MongoDBReplicaSet(MongoDBFinder, services.Service):
    replica_set_name = 'test'

    mongod_parameters = (
        '--noprealloc',
        '--smallfiles',
        '--oplogSize', '10',
    )

    def start(self):
        super(MongoDBReplicaSet, self).start()
        self.data_root = tempfile.mkdtemp()
        self.instances = list(map(self.start_instance, range(3)))
        # initialize the replica set
        self.instances[0].connect().admin.command(
            'replSetInitiate', self.build_config())
        # wait until the replica set is initialized
        get_repl_set_status = functools.partial(
            self.instances[0].connect().admin.command, 'replSetGetStatus', 1
        )
        errors = importlib.import_module('pymongo.errors')
        log.info('Waiting for replica set to initialize')

        watch = timing.Stopwatch()
        while watch.elapsed < datetime.timedelta(minutes=5):
            try:
                res = get_repl_set_status()
                if res.get('myState') != 1: continue
            except errors.OperationFailure:
                continue
            break
        else:
            raise RuntimeError("timeout waiting for replica set to start")

    def start_instance(self, number):
        port = self.find_free_port()
        data_dir = os.path.join(self.data_root, 'r{number}'.format(**locals()))
        os.mkdir(data_dir)
        cmd = [
            self.find_binary(),
            '--dbpath', data_dir,
            '--port', str(port),
            '--replSet', self.replica_set_name,
        ] + list(self.mongod_parameters)
        log_file = self.get_log(number)
        process = subprocess.Popen(cmd, stdout=log_file)
        portend.occupied('localhost', port, timeout=50)
        log.info('{self}:{number} listening on {port}'.format(**locals()))
        return InstanceInfo(data_dir, port, process, log_file)

    def get_log(self, number):
        log_name = 'r{number}.log'.format(**locals())
        log_filename = os.path.join(self.data_root, log_name)
        log_file = open(log_filename, 'a')
        return log_file

    def is_running(self):
        return hasattr(self, 'instances') and all(
            instance.process.returncode is None for instance in self.instances)

    def stop(self):
        super(MongoDBReplicaSet, self).stop()
        for instance in self.instances:
            if instance.process.returncode is None:
                instance.process.terminate()
                instance.process.wait()
            instance.log_file.close()
        del self.instances
        shutil.rmtree(self.data_root)

    def build_config(self):
        return dict(
            _id = self.replica_set_name,
            members = [
                dict(
                    _id=number,
                    host='localhost:{instance.port}'.format(**locals()),
                ) for number, instance in enumerate(self.instances)
            ]
        )

    def get_connect_hosts(self):
        return ['localhost:{instance.port}'.format(**locals())
            for instance in self.instances]

    def get_uri(self):
        return 'mongodb://' + ','.join(self.get_connect_hosts())

    def get_connection(self):
        pymongo = importlib.import_module('pymongo')
        return pymongo.MongoClient(self.get_uri())


InstanceInfoBase = collections.namedtuple('InstanceInfoBase',
    'path port process log_file')
class InstanceInfo(InstanceInfoBase):
    def connect(self):
        hp = 'localhost:{self.port}'.format(**locals())
        pymongo = __import__('pymongo')
        rp = pymongo.ReadPreference.PRIMARY_PREFERRED
        return pymongo.MongoClient(hp, read_preference=rp)
