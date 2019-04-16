# coding: future-fstrings

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
from tempora import timing
from . import manage
from . import cli


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

    process_kwargs = {}
    """
    keyword arguments to Popen to control the process creation
    """

    @services.Subprocess.PortFree()
    def start(self):
        super(MongoDBService, self).start()
        # start the daemon
        mongodb_data = os.path.join(sys.prefix, 'var', 'lib', 'mongodb')
        cmd = [
            self.find_binary(),
            '--dbpath=' + mongodb_data,
        ]
        self.process = subprocess.Popen(cmd, **self.process_kwargs)
        self.wait_for_pattern(r'waiting for connections on port (?P<port>\d+)')
        log.info('%s listening on %s', self, self.port)


class MongoDBInstance(MongoDBFinder, services.Subprocess, services.Service):
    mongod_args = (
        '--storageEngine', 'ephemeralForTest',
    )

    process_kwargs = {}
    """
    keyword arguments to Popen to control the process creation
    """

    def merge_mongod_args(self, add_args):
        merged = list(self.mongod_args)

        if any(arg.startswith('--storageEngine') for arg in add_args):
            merged.remove('--storageEngine')
            merged.remove('ephemeralForTest')

        self.port, add_args[:] = cli.extract_param('port', add_args, type=int)

        merged.extend(add_args)
        self.mongod_args = merged

    def start(self):
        super(MongoDBInstance, self).start()
        if not hasattr(self, 'port') or not self.port:
            self.port = portend.find_available_local_port()
        self.data_dir = tempfile.mkdtemp()
        cmd = [
            self.find_binary(),
            '--dbpath', self.data_dir,
            '--port', str(self.port),
        ] + list(self.mongod_args)
        if hasattr(self, 'bind_ip') and '--bind_ip' not in cmd:
            cmd.extend(['--bind_ip', self.bind_ip])
        self.process = subprocess.Popen(cmd, **self.process_kwargs)
        portend.occupied('localhost', self.port, timeout=3)
        log.info(f'{self} listening on {self.port}')

    def get_connection(self):
        pymongo = importlib.import_module('pymongo')
        return pymongo.MongoClient('localhost', self.port)

    def purge_all_databases(self):
        manage.purge_all_databases(self.get_connection())

    def get_connect_hosts(self):
        return [f'localhost:{self.port}']

    def get_uri(self):
        return 'mongodb://' + ','.join(self.get_connect_hosts())

    def stop(self):
        super(MongoDBInstance, self).stop()
        shutil.rmtree(self.data_dir)
        del self.data_dir


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
                if res.get('myState') != 1:
                    continue
            except errors.OperationFailure:
                continue
            break
        else:
            raise RuntimeError("timeout waiting for replica set to start")

    def start_instance(self, number):
        port = portend.find_available_local_port()
        data_dir = os.path.join(self.data_root, repr(number))
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
        log.info(f'{self}:{number} listening on {port}')
        return InstanceInfo(data_dir, port, process, log_file)

    def get_log(self, number):
        log_filename = os.path.join(self.data_root, f'r{number}.log')
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
            _id=self.replica_set_name,
            members=[
                dict(
                    _id=number,
                    host=f'localhost:{instance.port}',
                ) for number, instance in enumerate(self.instances)
            ]
        )

    def get_connect_hosts(self):
        return [
            f'localhost:{instance.port}'
            for instance in self.instances
        ]

    def get_uri(self):
        return 'mongodb://' + ','.join(self.get_connect_hosts())

    def get_connection(self):
        pymongo = importlib.import_module('pymongo')
        return pymongo.MongoClient(self.get_uri())


InstanceInfoBase = collections.namedtuple('InstanceInfoBase',
                                          'path port process log_file')


class InstanceInfo(InstanceInfoBase):
    def connect(self):
        pymongo = __import__('pymongo')
        rp = pymongo.ReadPreference.PRIMARY_PREFERRED
        return pymongo.MongoClient(
            f'localhost:{self.port}', read_preference=rp)
