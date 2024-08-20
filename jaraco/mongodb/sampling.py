import builtins
from typing import Mapping


def estimate(coll, filter: Mapping = {}, sample=1):
    """
    Estimate the number of documents in the collection
    matching the filter.

    Sample may be a fixed number of documents to sample
    or a percentage of the total collection size.

    >>> coll = getfixture('bulky_collection')
    >>> estimate(coll)
    100
    >>> query = {"val": {"$gte": 50}}
    >>> val = estimate(coll, filter=query)
    >>> val > 0
    True
    >>> val = estimate(coll, filter=query, sample=10)
    >>> val > 0
    True
    >>> val = estimate(coll, filter=query, sample=.1)
    >>> val > 0
    True
    """
    total = coll.estimated_document_count()
    if not filter and sample == 1:
        return total
    if sample <= 1:
        sample *= total
    pipeline = list(
        builtins.filter(
            None,
            [
                {'$sample': {'size': sample}} if sample < total else {},
                {'$match': filter},
                {'$count': 'matched'},
            ],
        )
    )
    docs = next(coll.aggregate(pipeline))
    ratio = docs['matched'] / sample
    return int(total * ratio)
