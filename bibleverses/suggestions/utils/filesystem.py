import os.path


def ensure_dir(dirname):
    """
    Ensure that a directory exists
    """
    d = os.path.dirname(dirname)
    if not os.path.exists(d):
        os.makedirs(d)
