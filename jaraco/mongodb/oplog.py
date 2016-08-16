from __future__ import unicode_literals, absolute_import

import argparse
import time
import json
import logging
import pymongo
import bson
import re
import textwrap
import collections
import datetime

import six

import pkg_resources
import jaraco.logging
from jaraco.functools import compose
from pymongo.cursor import CursorType
from jaraco.itertools import always_iterable


class Extend(argparse.Action):
    """
    Argparse action to take an nargs=* argument
    and add any values to the existing value.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        getattr(namespace, self.dest).extend(values)


def delta_from_seconds(seconds):
    return datetime.timedelta(seconds=int(seconds))


def parse_args(*args, **kwargs):
    """
    Parse the args for the command.

    It should be possible for one to specify '--ns', '-x', and '--rename'
    multiple times:

    >>> args = parse_args(['--ns', 'foo', 'bar', '--ns', 'baz'])
    >>> args.ns
    ['foo', 'bar', 'baz']

    >>> parse_args(['-x', '--exclude']).exclude
    []

    >>> renames = parse_args(['--rename', 'a=b', '--rename', 'b=c']).rename
    >>> len(renames)
    2
    >>> type(renames)
    <class 'jaraco.mongodb.oplog.Renamer'>

    >>> parse_args(['--seconds', '86402']).start_ts
    Timestamp(..., 0)
    """
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("--help",
        help="show usage information",
        action="help")

    parser.add_argument("--source", metavar="host[:port]",
        help="host to pull from")

    parser.add_argument('--oplogns', default='local.oplog.rs',
        help="source namespace for oplog")

    parser.add_argument("--dest", metavar="host[:port]",
        help="host to push to (<set name>/s1,s2 for sets)")

    parser.add_argument("-s", "--seconds",
        dest="start_ts",
        type=compose(Timestamp.for_window, delta_from_seconds),
        help="""Seconds in the past to query. Overrides any value
        indicated by a resume file.""")

    parser.add_argument("-f", "--follow", action="store_true",
        help="wait for new data in oplog, run forever.")

    parser.add_argument("--ns", nargs="*", default=[],
        action=Extend,
        help="this namespace(s) only ('dbname' or 'dbname.coll')")

    parser.add_argument("-x", "--exclude", nargs="*", default=[],
        action=Extend,
        help="exclude namespaces ('dbname' or 'dbname.coll')")

    parser.add_argument("--rename", nargs="*", default=[],
        metavar="ns_old=ns_new",
        type=RenameSpec.from_spec,
        action=Extend,
        help="rename namespaces before processing on dest")

    parser.add_argument("--dry-run", default=False,
        action="store_true",
        help="suppress application of ops")

    help = textwrap.dedent("""
        Read from and write to this file the last processed timestamp.
        """)
    parser.add_argument("--resume-file",
        metavar="FILENAME",
        type=ResumeFile,
        help=help,
    )
    jaraco.logging.add_arguments(parser)

    args = parser.parse_args(*args, **kwargs)
    args.rename = Renamer(args.rename)

    args.start_ts = args.start_ts or (
        args.resume_file and args.resume_file.read()
    )

    return args


class RenameSpec(object):
    @classmethod
    def from_spec(cls, string_spec):
        """
        Construct RenameSpec from a pair separated by equal sign ('=').
        """
        old_ns, new_ns = string_spec.split('=')
        return cls(old_ns, new_ns)

    def __init__(self, old_ns, new_ns):
        self.old_ns = old_ns
        self.new_ns = new_ns
        self.old_db, sep, self.old_coll = self.old_ns.partition('.')
        self.new_db, sep, self.new_coll = self.new_ns.partition('.')
        self.regex = re.compile(r"^{0}(\.|$)".format(re.escape(self.old_ns)))

        if '.' in self.old_ns:
            logging.warning("Collection rename operations will fail on "
                "MongoDB 3.2; "
                "see https://github.com/jaraco/jaraco.mongodb/issues/5")

        self.new_ns += "."

    def __call__(self, op):
        """
        Apply this rename to the op
        """
        if self.regex.match(op['ns']):
            ns = self.regex.sub(self.new_ns, op['ns']).rstrip(".")
            logging.debug("renaming %s to %s", op['ns'], ns)
            op['ns'] = ns
        if op['ns'].endswith('.system.indexes'):
            # index operation; update ns in the op also.
            self(op['o'])
        self._handle_create(op)

    def _handle_create(self, op):
        if self._matching_create_command(op, self.old_ns):
            op['ns'] = self.new_db + '.$cmd'
            op['o']['create'] = self.new_coll

    @staticmethod
    def _matching_create_command(op, ns):
        db, sep, coll = ns.partition('.')
        return (
            op.get('op') == 'c'
            and
            op['ns'] == db + '.$cmd'
            and
            op['o'].get('create', None) == coll
        )

    def affects(self, ns):
        return bool(self.regex.match(ns))


class Renamer(list):
    """
    >>> specs = [
    ...      'a=b',
    ...      'alpha=gamma',
    ...  ]
    >>> renames = Renamer.from_specs(specs)
    >>> op = dict(ns='a.a')
    >>> renames(op)
    >>> op['ns']
    'b.a'
    >>> renames.affects('alpha.foo')
    True
    >>> renames.affects('b.gamma')
    False
    """

    def invoke(self, op):
        """
        Replace namespaces in op based on RenameSpecs in self.
        """
        for rename in self:
            rename(op)
    __call__ = invoke

    @classmethod
    def from_specs(cls, specs):
        return cls(map(RenameSpec.from_spec, always_iterable(specs)))

    def affects(self, ns):
        """
        Return True if this renamer affects the indicated namespace.
        """
        return any(rn.affects(ns) for rn in self)


def string_none(value):
    """
    Convert the string 'none' to None
    """
    is_string_none = not value or value.lower() == 'none'
    return None if is_string_none else value


def _same_instance(client1, client2):
    """
    Return True if client1 and client2 appear to reference the same
    MongoDB instance.
    """
    return client1._topology_settings.seeds == client2._topology_settings.seeds


def _full_rename(args):
    """
    Return True only if the arguments passed specify exact namespaces
    and to conduct a rename of every namespace.
    """
    return (
        args.ns and
        all(map(args.rename.affects, args.ns))
    )


def _resolve_shard(client):
    """
    The destination cannot be a mongoS instance, as applyOps is
    not an allowable command for mongoS instances, so if the
    client is a connection to a mongoS instance, raise an error
    or resolve the replica set.
    """
    status = client.admin.command('serverStatus')
    if status['process'] == 'mongos':
        raise RuntimeError("Destination cannot be mongos")
    return client


def _load_dest(host):
    if not host:
        return
    return _resolve_shard(pymongo.MongoClient(host))


def main():
    args = parse_args()
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    jaraco.logging.setup(args, format=log_format)

    logging.info("{name} {version}".format(
        name='jaraco.mongodb.oplog',
        version=pkg_resources.require('jaraco.mongodb')[0].version,
    ))
    logging.info("going to connect")

    src = pymongo.MongoClient(args.source)
    dest = _load_dest(args.dest)

    if dest and _same_instance(src, dest) and not _full_rename(args):
        logging.error(
            "source and destination hosts can be the same only "
            "when both --ns and --rename arguments are given")
        raise SystemExit(1)

    logging.info("connected")

    start = args.start_ts
    if not start:
        logging.error("Resume file or window required")
        raise SystemExit(2)

    logging.info("starting from %s (%s)", start, start.as_datetime())
    db_name, sep, coll_name = args.oplogns.partition('.')
    oplog_coll = src[db_name][coll_name]
    num = 0

    class_ = TailingOplog if args.follow else Oplog
    generator = class_(oplog_coll)

    if not generator.has_ops_before(start):
        logging.warning("No ops before start time; oplog may be overrun")

    try:
        for num, doc in enumerate(generator.since(start)):
            _handle(dest, doc, args, num)
            last_handled = doc
        logging.info("all done")
    except KeyboardInterrupt:
        logging.info("Got Ctrl+C, exiting...")
    finally:
        if 'last_handled' in locals():
            args.resume_file.save(last_handled['ts'])


def applies_to_ns(op, ns):
    return (
        op['ns'].startswith(ns) or
        RenameSpec._matching_create_command(op, ns)
    )


def _handle(dest, op, args, num):
    # Skip "no operation" items
    if op['op'] == 'n':
        return

    # Skip excluded namespaces or namespaces that does not match --ns
    excluded = any(applies_to_ns(op, ns) for ns in args.exclude)
    included = any(applies_to_ns(op, ns) for ns in args.ns)

    if excluded or (args.ns and not included):
        logging.log(logging.DEBUG-1, "skipping %s", op)
        return

    args.rename(op)

    logging.debug("applying op %s", op)
    try:
        args.dry_run or apply(dest, op)
    except pymongo.errors.OperationFailure as e:
        msg = '{e!r} applying {op}'.format(**locals())
        logging.warning(msg)

    # Update status
    ts = op['ts']
    if not num % 1000:
        args.resume_file.save(ts)
        logging.info(
            "%s\t%s\t%s -> %s",
            num, ts.as_datetime(),
            op.get('op'),
            op.get('ns'),
        )


def apply(db, op):
    """
    Apply operation in db
    """
    dbname = op['ns'].split('.')[0] or "admin"
    db[dbname].command("applyOps", [op])


class Oplog(object):
    find_params = {}

    def __init__(self, coll):
        self.coll = coll.with_options(
            codec_options=bson.CodecOptions(
                document_class=collections.OrderedDict,
            ),
        )

    def get_latest_ts(self):
        cur = self.coll.find().sort('$natural', pymongo.DESCENDING).limit(-1)
        latest_doc = next(cur)
        return Timestamp.wrap(latest_doc['ts'])

    def query(self, spec):
        return self.coll.find(spec, **self.find_params)

    def since(self, ts):
        """
        Query the oplog for items since ts and then return
        """
        spec = {'ts': {'$gt': ts}}
        cursor = self.query(spec)
        while True:
            # todo: trap InvalidDocument errors:
            # except bson.errors.InvalidDocument as e:
            #  logging.info(repr(e))
            for doc in cursor:
                yield doc
            if not cursor.alive:
                break
            time.sleep(1)

    def has_ops_before(self, ts):
        """
        Determine if there are any ops before ts
        """
        spec = {'ts': {'$lt': ts}}
        return bool(self.coll.find_one(spec))


class TailingOplog(Oplog):
    find_params = dict(
        cursor_type=CursorType.TAILABLE_AWAIT,
        oplog_replay=True,
    )

    def since(self, ts):
        """
        Tail the oplog, starting from ts.
        """
        while True:
            items = super(TailingOplog, self).since(ts)
            for doc in items:
                yield doc
                ts = doc['ts']


class Timestamp(bson.timestamp.Timestamp):
    @classmethod
    def wrap(cls, orig):
        """
        Wrap an original timestamp as returned by a pymongo query
        with a version of this class.
        """
        # hack to give the timestamp this class' specialized methods
        orig.__class__ = cls
        return orig

    def dump(self, stream):
        """Serialize self to text stream.

        Matches convention of mongooplog.
        """
        items = (
            ('time', self.time),
            ('inc', self.inc),
        )
        # use ordered dict to retain order
        ts = collections.OrderedDict(items)
        json.dump(dict(ts=ts), stream)

    @classmethod
    def load(cls, stream):
        """Load a serialized version of self from text stream.

        Expects the format used by mongooplog.
        """
        data = json.load(stream)['ts']
        return cls(data['time'], data['inc'])

    @classmethod
    def for_window(cls, window):
        """
        Given a timedelta window, return a timestamp representing
        that time.
        """
        utcnow = datetime.datetime.utcnow()
        return cls(utcnow - window, 0)


class ResumeFile(six.text_type):
    def save(self, ts):
        """
        Save timestamp to file.
        """
        with open(self, 'w') as f:
            Timestamp.wrap(ts).dump(f)

    def read(self):
        """
        Read timestamp from file.
        """
        with open(self) as f:
            return Timestamp.load(f)


if __name__ == '__main__':
    main()
