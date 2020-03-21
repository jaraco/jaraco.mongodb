# coding: future-fstrings

'''
Migration support as features in MongoWorld 2016
From the Polls to the Trolls.

The Manager class provides a general purpose support
for migrating documents to a target version through
a series of migration functions.
'''

import re
import itertools

from six.moves import range

from more_itertools import recipes


class Manager(object):
    """
    A manager for facilitating the registration of migration functions
    and applying those migrations to documents.

    To use, implement migration functions to and from each adjacent
    version of your schema and decorate each with the register
    classmethod. For example:

    >>> @Manager.register
    ... def v1_to_2(manager, doc):
    ...     doc['foo'] = 'bar'
    >>> @Manager.register
    ... def v2_to_3(manager, doc):
    ...     doc['foo'] = doc['foo'] + ' baz'

    Note that in addition to the document, the migration manager is also
    passed to the migration function, allowing for other context to be
    made available during the migration.

    To create a manager for migrating documents to version 3:

    >>> mgr = Manager(3)

    Then, use the manager to migrate a document to a target version.

    >>> v1_doc = dict(version=1, data='stub')
    >>> v3_doc = mgr.migrate_doc(v1_doc)

    >>> v3_doc['version']
    3
    >>> v3_doc['foo']
    'bar baz'

    Note that the document is modified in place:

    >>> v1_doc is v3_doc
    True

    >>> Manager._upgrade_funcs.clear()
    """

    version_attribute_name = 'version'
    _upgrade_funcs = set()

    def __init__(self, target_version):
        self.target_version = target_version

    @classmethod
    def register(cls, func):
        """
        Decorate a migration function with this method
        to make it available for migrating cases.
        """
        cls._add_version_info(func)
        cls._upgrade_funcs.add(func)
        return func

    @staticmethod
    def _add_version_info(func):
        """
        Add .source and .target attributes to the registered function.
        """
        pattern = r'v(?P<source>\d+)_to_(?P<target>\d+)$'
        match = re.match(pattern, func.__name__)
        if not match:
            raise ValueError("migration function name must match " + pattern)
        func.source, func.target = map(int, match.groups())

    def migrate_doc(self, doc):
        """
        Migrate the doc from its current version to the target version
        and return it.
        """
        orig_ver = doc.get(self.version_attribute_name, 0)
        funcs = self._get_migrate_funcs(orig_ver, self.target_version)
        for func in funcs:
            func(self, doc)
            doc[self.version_attribute_name] = func.target
        return doc

    @classmethod
    def _get_migrate_funcs(cls, orig_version, target_version):
        """
        >>> @Manager.register
        ... def v1_to_2(manager, doc):
        ...     doc['foo'] = 'bar'
        >>> @Manager.register
        ... def v2_to_1(manager, doc):
        ...     del doc['foo']
        >>> @Manager.register
        ... def v2_to_3(manager, doc):
        ...     doc['foo'] = doc['foo'] + ' baz'
        >>> funcs = list(Manager._get_migrate_funcs(1, 3))
        >>> len(funcs)
        2
        >>> funcs == [v1_to_2, v2_to_3]
        True
        >>> funcs = list(Manager._get_migrate_funcs(2, 1))
        >>> len(funcs)
        1
        >>> funcs == [v2_to_1]
        True

        >>> Manager._upgrade_funcs.clear()
        """
        direction = 1 if target_version > orig_version else -1
        versions = range(orig_version, target_version + direction, direction)
        transitions = recipes.pairwise(versions)
        return itertools.starmap(cls._get_func, transitions)

    @classmethod
    def _get_func(cls, source_ver, target_ver):
        """
        Return exactly one function to convert from source to target
        """
        matches = (
            func
            for func in cls._upgrade_funcs
            if func.source == source_ver and func.target == target_ver
        )
        try:
            (match,) = matches
        except ValueError:
            raise ValueError(f"No migration from {source_ver} to {target_ver}")
        return match
