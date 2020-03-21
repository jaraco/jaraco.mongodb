r"""
Backslash-escape text such that it is safe for MongoDB fields,
honoring `Restrictions on Field Names
<https://docs.mongodb.com/v3.4/reference/limits/#Restrictions-on-Field-Names>`_.

>>> decode(encode('my text with dots...'))
'my text with dots...'

>>> decode(encode(r'my text with both \. and literal .'))
'my text with both \\. and literal .'

>>> decode(encode('$leading dollar'))
'$leading dollar'
"""

from __future__ import unicode_literals


import re


def encode(text):
    text = text.replace('\\', '\\\\')
    text = re.sub(r'^\$', '\\$', text)
    return text.replace('.', '\\D')


def unescape(match):
    char = match.group(1)
    return '.' if char == 'D' else char


def decode(encoded):
    return re.sub(r'\\(.)', unescape, encoded)
