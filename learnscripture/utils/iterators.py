def chunks(sliceable, n):
    """Yield successive n-sized chunks from list or other sliceable"""
    for i in range(0, len(sliceable), n):
        yield sliceable[i : i + n]


def intersperse(iterable, delimiter):
    it = iter(iterable)
    try:
        yield next(it)
    except StopIteration:
        return
    for x in it:
        yield delimiter
        yield x


def chunked_queryset(qs, batch_size, index="id"):
    """
    Yields a QuerySet split into batches of exact size 'batch_size'
    (apart from the last batch which can be smaller) as using equal sizes
    of batches decreases a number of db hits and allows better control
    of the memory usage.
    Allows for arbitrary ordering of queryset.

    This requires a non-nullable column `index` (default 'id') that can be used
    with the `BETWEEN` operator to be present, and the result is only efficient
    if there is a DB index on that column.
    """

    ids = qs.order_by().prefetch_related(None).select_related(None).values_list(index, flat=True)
    if not ids:
        return
    for i in range(0, len(ids), batch_size):
        filter_args = {f"{index}__in": ids[i : i + batch_size]}
        yield qs.filter(**filter_args)


def iter_chunked_queryset(queryset, batch_size, index="id"):
    for qs in chunked_queryset(queryset, batch_size, index=index):
        yield from qs
