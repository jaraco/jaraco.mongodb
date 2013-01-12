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
import datetime
import time
import logging
import pymongo
import bson

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("--help",
                        help="show usage information",
                        action="help")

    parser.add_argument("--from", metavar="host[:port]", dest="fromhost",
                        help="host to pull from")

    parser.add_argument("-h", "--host", metavar="host[:port]",
                        default="localhost",
                        help="mongo host to push to (<set name>/s1,s2 for sets)")

    parser.add_argument("-p", "--port", metavar="host[:port]",
                        default=27017, type=int,
                        help="server port. Can also use --host hostname:port")

    parser.add_argument("-s", "--seconds", type=int, default=86400,
                        help="seconds to go back. Default is 86400 (24 hours)")

    parser.add_argument("-f", "--follow", action="store_true",
                        help="wait for new data in oplog, run forever.")

    parser.add_argument("-x", "--exclude", nargs="*", default=[],
                        help="exclude namespaces ('dbname' or 'dbname.coll')")

    return parser.parse_args()

def main():
    args = parse_args()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logging.info("going to connect")

    src = pymongo.Connection(args.fromhost)
    dest = pymongo.Connection(args.host, args.port)

    logging.info("connected")

    start_datetime = datetime.datetime.utcnow() - datetime.timedelta(seconds=args.seconds)
    start = bson.timestamp.Timestamp(int(start_datetime.strftime("%s")), 0)
    logging.info("starting from %s", start)

    q = {"ts": {"$gte": start}}
    oplog = (src.local['oplog.rs'].find(q, tailable=True, await_data=True)
                                  .sort("$natural", pymongo.ASCENDING))
    num = 0

    while oplog.alive:
        try:
            op = oplog.next()
        except StopIteration:
            if not args.follow:
                logging.info("all done")
                return
            else:
                logging.debug("waiting for new data...")
                time.sleep(1)
                continue

        if op['op'] == 'n':
            continue

        if any(op['ns'].startswith(ns) for ns in args.exclude):
            logging.debug("skipping ns %s", op['ns'])
            continue

        if not num % 1000:
            logging.info("%s\t%s", num, op['ts'])
        num += 1

        dbname = op['ns'].split('.')[0] or "admin"
        dest[dbname].command("applyOps", [op])

if __name__ == '__main__':
    main()
