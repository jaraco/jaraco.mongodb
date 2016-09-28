import pprint
import textwrap

from .query import compat_explain


def _rep_index_info(coll):
    index_info = coll.index_information()
    return "Indexes are:\n" + pprint.pformat(index_info)


def assert_covered(cur):
    """
    Use the best knowledge about Cursor.explain() to ensure that the query
    was covered by an index.
    """
    explanation = compat_explain(cur)
    tmpl = textwrap.dedent("""
        Query was not covered:
        {explanation}
        """).lstrip()
    report = tmpl.format(explanation=pprint.pformat(explanation))
    report += _rep_index_info(cur.collection)
    stats = explanation['executionStats']
    assert stats['totalDocsExamined'] == 0, report
    assert stats['totalKeysExamined'], "No documents matched"
    return explanation


def assert_distinct_covered(coll, field, query):
    """
    Ensure a distinct query is covered by an index.
    """
    assert coll.count(), "Unable to assert without a document"
    db = coll.database
    res = db.command('distinct', coll.name, key=field, query=query)
    assert 'stats' in res, "Stats not supplied. Maybe SERVER-9126?"
    stats = res['stats']
    tmpl = textwrap.dedent("""
        Distinct query was not covered:
        {explanation}
        """).lstrip()
    report = tmpl.format(explanation=pprint.pformat(stats))
    report += _rep_index_info(coll)
    assert stats['nscannedObjects'] == 0, report
    assert stats['n'], "No documents matched"
    return stats
