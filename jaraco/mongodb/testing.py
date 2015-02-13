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
    docs = explanation['executionStats']['totalDocsExamined']
    assert docs == 0, report
