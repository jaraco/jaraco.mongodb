import six

collect_ignore = ['jaraco/mongodb/pmxbot.py']

if six.PY2:
    collect_ignore.append('jaraco/mongodb/monitor-index-creation.py')
