# -*- coding: utf-8 -*-
from __future__ import generator_stop


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]


def intersperse(iterable, delimiter):
    it = iter(iterable)
    try:
        yield next(it)
    except StopIteration:
        return
    for x in it:
        yield delimiter
        yield x
