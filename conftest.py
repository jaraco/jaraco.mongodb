import sys

PY2 = sys.version_info < (3,)

if PY2:
    collect_ignore = ['jaraco/mongodb/monitor-index-creation.py']
