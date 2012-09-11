import argparse
import datetime
import time
import logging
import pymongo

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)

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

    start = datetime.datetime.now() - datetime.timedelta(seconds=args.seconds)
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
                logging.info("waiting for new data...")
                time.sleep(1)
                continue

        if not num % 1000:
            logging.info("%s\t%s", num, op['ts'])
        num += 1

        dbname = op['ns'].split('.')[0] or "admin"
        dest[dbname].command("applyOps", [op])

if __name__ == '__main__':
    main()
