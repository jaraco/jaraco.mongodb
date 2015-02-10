import pprint

from .query import compat_explain


def assert_covered(cur):
    """
    Use the best knowledge about Cursor.explain() to ensure that the query
    was covered by an index.
    """
    explanation = compat_explain(cur)
    index_info = cur.collection.index_information()
    report = (
        "Query was not covered:\n" + pprint.pformat(explanation) +
        "\nIndexes are:\n" + pprint.pformat(index_info))
    docs = explanation['executionStats']['totalDocsExamined']
    assert docs == 0, report
