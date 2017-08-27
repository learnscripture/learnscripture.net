import pickle


class PicklerMixin(object):
    """
    Very simple strategy for serializing - just use pickle. May be adequate for some purposes
    """
    @classmethod
    def load(cls, filehandle):
        return pickle.load(filehandle)

    @classmethod
    def dump(cls, obj, filehandle):
        return pickle.dump(obj, filehandle)
