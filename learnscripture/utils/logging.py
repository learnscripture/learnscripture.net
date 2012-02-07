

def extra(**kwargs):
    """
    Create a dictionary of extra data, as required by Raven for correct logging.
    """
    return dict(data=dict((k, repr(v)) for k, v in kwargs.items()))
