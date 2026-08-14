def get_in_batches(qs, batch_size=200):
    start = 0
    while True:
        q = list(qs[start : start + batch_size])
        if len(q) == 0:
            raise StopIteration()
        yield from q
        start += batch_size
