import argparse


def extract_param(param, args, type=None):
    """
    From a list of args, extract the one param if supplied,
    returning the value and unused args.

    >>> extract_param('port', ['foo', '--port=999', 'bar'], type=int)
    (999, ['foo', 'bar'])
    >>> extract_param('port', ['foo', '--port', '999', 'bar'], type=int)
    (999, ['foo', 'bar'])
    >>> extract_param('port', ['foo', 'bar'])
    (None, ['foo', 'bar'])
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--' + param, type=type)
    res, unused = parser.parse_known_args(args)
    return getattr(res, param), unused
