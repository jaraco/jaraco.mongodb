# Copyright 2013 PublishThis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import calendar
import datetime
import time
import json
import logging
import pymongo
import bson
import re

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("--help",
                        help="show usage information",
                        action="help")

    parser.add_argument("--from", metavar="host[:port]", dest="fromhost",
                        help="host to pull from")

    parser.add_argument("-h", "--host", "--to", metavar="host[:port]",
                        default="localhost",
                        help="mongo host to push to (<set name>/s1,s2 for sets)")

    parser.add_argument("-p", "--port", metavar="host[:port]",
                        default=27017, type=int,
                        help="server port. Can also use --host hostname:port")

    parser.add_argument("-s", "--seconds", type=int, default=None,
                        help="""seconds to go back. If not set, try read
                        timestamp from --resume-file. If the file not found,
                        assume --seconds=86400 (24 hours)""")

    parser.add_argument("-f", "--follow", action="store_true",
                        help="wait for new data in oplog, run forever.")

    parser.add_argument("--ns", nargs="*", default=[],
                        help="this namespace(s) only ('dbname' or 'dbname.coll')")

    parser.add_argument("-x", "--exclude", nargs="*", default=[],
                        help="exclude namespaces ('dbname' or 'dbname.coll')")

    parser.add_argument("--rename", nargs="*", default=[],
                        metavar="ns_old=ns_new",
                        help="rename namespaces before processing on dest")

    parser.add_argument("--resume-file", default="mongooplog.ts",
                        metavar="FILENAME",
                        help="""resume from timestamp read from this file and
                             write last processed timestamp back to this file
                             (default is %(default)s).
                             Pass empty string or 'none' to disable this
                             feature.
                             """)

    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging()

    rename = {}     # maps old namespace (regex) to the new namespace (string)
    for rename_pair in args.rename:
        old_ns, new_ns = rename_pair.split("=")
        old_ns_re = re.compile(r"^{0}(\.|$)".format(re.escape(old_ns)))
        rename[old_ns_re] = new_ns + "."

    logging.info("going to connect")

    src = pymongo.Connection(args.fromhost)
    dest = pymongo.Connection(args.host, args.port)

    if src == dest:
        rename_ns = {x.split("=")[0] for x in args.rename}
        if any(ns not in rename_ns for ns in args.ns) or not args.ns:
            logging.error(
                "source and destination hosts can be the same only "
                "when both --ns and --rename arguments are given")
            return 1

    logging.info("connected")

    # Find out where to start from
    utcnow = calendar.timegm(time.gmtime())
    if args.seconds:
        start = bson.timestamp.Timestamp(utcnow - args.seconds, 0)
    else:
        day_ago = bson.timestamp.Timestamp(utcnow - 24*60*60, 0)
        start = read_ts(args.resume_file) or day_ago

    logging.info("starting from %s", start)
    q = {"ts": {"$gte": start}}
    oplog = (src.local['oplog.rs'].find(q, tailable=True, await_data=True)
                                  .sort("$natural", pymongo.ASCENDING))
    num = 0
    ts = start

    try:
        while oplog.alive:
            try:
                op = next(oplog)
            except StopIteration:
                if not args.follow:
                    logging.info("all done")
                    return
                else:
                    logging.debug("waiting for new data...")
                    time.sleep(1)
                    continue
            except bson.errors.InvalidDocument as e:
                logging.info(repr(e))
                continue

            # Skip "no operation" items
            if op['op'] == 'n':
                continue

            # Update status
            ts = op['ts']
            if not num % 1000:
                save_ts(ts, args.resume_file)
                logging.info("%s\t%s\t%s -> %s",
                             num, ts.as_datetime(),
                             op.get('op'),
                             op.get('ns'))
            num += 1

            # Skip excluded namespaces or namespaces that does not match --ns
            excluded = any(op['ns'].startswith(ns) for ns in args.exclude)
            included = any(op['ns'].startswith(ns) for ns in args.ns)

            if excluded or (args.ns and not included):
                logging.debug("skipping ns %s", op['ns'])
                continue

            # Rename namespaces
            for old_ns, new_ns in rename.items():
                if old_ns.match(op['ns']):
                    ns = old_ns.sub(new_ns, op['ns']).rstrip(".")
                    logging.debug("renaming %s to %s", op['ns'], ns)
                    op['ns'] = ns

            # Apply operation
            try:
                dbname = op['ns'].split('.')[0] or "admin"
                dest[dbname].command("applyOps", [op])
            except pymongo.errors.OperationFailure as e:
                logging.warning(repr(e))

    except KeyboardInterrupt:
        logging.info("Got Ctrl+C, exiting...")

    finally:
        save_ts(ts, args.resume_file)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def save_ts(ts, filename):
    """Save last processed timestamp to file. """
    try:
        if filename and filename.lower() != 'none':
            with open(filename, 'w') as f:
                obj = {"ts": {"time": ts.time, "inc":  ts.inc}}
                json.dump(obj, f)
    except IOError:
        return False
    else:
        return True

def read_ts(filename):
    """Read last processed timestamp from file. Return next timestamp that
    need to be processed, that is timestamp right after last processed one.
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)['ts']
            ts = bson.Timestamp(data['time'], data['inc'] + 1)
            return ts

    except (IOError, KeyError):
        return None


if __name__ == '__main__':
    main()
