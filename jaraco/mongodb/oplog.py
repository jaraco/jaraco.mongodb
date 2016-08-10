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

import jaraco.logging
from pymongo.cursor import CursorType
from jaraco.itertools import always_iterable


class Extend(argparse.Action):
    """
    Argparse action to take an nargs=* argument
    and add any values to the existing value.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        getattr(namespace, self.dest).extend(values)


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
        default="localhost",
        help="host to push to (<set name>/s1,s2 for sets)")

    parser.add_argument("-s", "--seconds", type=int, default=None,
        help="""seconds to go back. If not set, try read
        timestamp from --resume-file. If the file not found,
        assume --seconds=86400 (24 hours)""")

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
        type=Renamer.item,
        action=Extend,
        help="rename namespaces before processing on dest")

    parser.add_argument("--dry-run", default=False,
        action="store_true",
        help="suppress application of ops")

    help = textwrap.dedent("""
        resume from timestamp read from this file and
        write last processed timestamp back to this file
        (default is %(default)s).
        Pass empty string or 'none' to disable this
        feature.
        """)
    parser.add_argument("--resume-file", default="mongooplog.ts",
        metavar="FILENAME", type=string_none,
        help=help,
    )
    jaraco.logging.add_arguments(parser)

    args = parser.parse_args(*args, **kwargs)
    args.rename = Renamer(args.rename)
    return args


class Renamer(dict):
    """
    >>> specs = [
    ...      'a=b',
    ...      'alpha=gamma',
    ...  ]
    >>> renames = Renamer(map(Renamer.item, specs))
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
        Replace namespaces in op based on keys/values in self.
        """
        for old_ns, new_ns in self.items():
            if old_ns.match(op['ns']):
                ns = old_ns.sub(new_ns, op['ns']).rstrip(".")
                logging.debug("renaming %s to %s", op['ns'], ns)
                op['ns'] = ns
            if op['ns'].endswith('.system.indexes'):
                # index operation; update ns in the op also.
                self.invoke(op['o'])
    __call__ = invoke

    @classmethod
    def from_specs(cls, specs):
        return cls(map(cls.item, always_iterable(specs)))

    @staticmethod
    def item(spec):
        """
        Return a pair of old namespace (regex) to the new namespace (string).

        spec should be a pair separated by equal sign ('=').
        """
        old_ns, new_ns = spec.split('=')
        regex = re.compile(r"^{0}(\.|$)".format(re.escape(old_ns)))

        return regex, new_ns + "."

    def affects(self, ns):
        """
        Return True if this renamer affects the indicated namespace.
        """
        return any(exp.match(ns) for exp in self)


def string_none(value):
    """
    Convert the string 'none' to None
    """
    is_string_none = not value or value.lower() == 'none'
    return None if is_string_none else value


def _calculate_start(args):
    """
    Return the start time as a bson timestamp.
    """
    utcnow = int(time.time())

    if args.seconds:
        return bson.timestamp.Timestamp(utcnow - args.seconds, 0)

    day_ago = bson.timestamp.Timestamp(utcnow - 24*60*60, 0)
    saved_ts = read_ts(args.resume_file)
    spec_ts = increment_ts(saved_ts) if saved_ts else None
    return spec_ts or day_ago


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


def main():
    args = parse_args()
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    jaraco.logging.setup(args, format=log_format)

    logging.info("going to connect")

    src = pymongo.MongoClient(args.source)
    dest = _resolve_shard(pymongo.MongoClient(args.dest))

    if _same_instance(src, dest) and not _full_rename(args):
        logging.error(
            "source and destination hosts can be the same only "
            "when both --ns and --rename arguments are given")
        raise SystemExit(1)

    logging.info("connected")

    start = _calculate_start(args)

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
            save_ts(last_handled['ts'], args.resume_file)

def _handle(dest, op, args, num):
    # Skip "no operation" items
    if op['op'] == 'n':
        return

    # Update status
    ts = op['ts']
    if not num % 1000:
        save_ts(ts, args.resume_file)
        logging.info(
            "%s\t%s\t%s -> %s",
            num, ts.as_datetime(),
            op.get('op'),
            op.get('ns'),
        )

    # Skip excluded namespaces or namespaces that does not match --ns
    excluded = any(op['ns'].startswith(ns) for ns in args.exclude)
    included = any(op['ns'].startswith(ns) for ns in args.ns)

    if excluded or (args.ns and not included):
        logging.log(logging.DEBUG-1, "skipping ns %s", op['ns'])
        return

    args.rename(op)

    logging.debug("applying op %s", op)
    try:
        apply(dest, op) if not args.dry_run else None
    except pymongo.errors.OperationFailure as e:
        msg = '{e!r} applying {op}'.format(**locals())
        logging.warning(msg)


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
        return latest_doc['ts']

    def query(self, spec):
        return self.coll.find(spec, **self.find_params)

    def since(self, ts):
        """
        Query the oplog for items since ts and then return
        """
        spec = {'ts': {'$gte': ts}}
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


def save_ts(ts, filename):
    """Save last processed timestamp to file. """
    try:
        if filename:
            with open(filename, 'w') as f:
                obj = {"ts": {"time": ts.time, "inc":  ts.inc}}
                json.dump(obj, f)
    except IOError:
        pass


def read_ts(filename):
    """Read last processed timestamp from file. Return next timestamp that
    need to be processed, that is timestamp right after last processed one.
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)['ts']
        return bson.Timestamp(data['time'], data['inc'])
    except (IOError, KeyError):
        pass


def increment_ts(ts):
    """
    Return a new ts with an incremented .inc.
    """
    return bson.Timestamp(ts.time, ts.inc + 1)


if __name__ == '__main__':
    main()
