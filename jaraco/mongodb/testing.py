import pprint

def assert_covered(cur):
    """
    Use the best knowledge about Cursor.explain() to ensure that the query
    was covered by an index.
    """
    explanation = cur.explain()
    index_info = cur.collection.index_information()
    report = (
        "Query was not covered:\n" + pprint.pformat(explanation) +
        "\nIndexes are:\n" + pprint.pformat(index_info))
    assert explanation['nscannedObjects'] == 0, report
