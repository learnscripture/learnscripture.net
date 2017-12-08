
def make_choices(name, choice_list):
    """
    Creates a class containing the given set of choices,
    which are specified as (value, constant name, user presentable title)
    e.g.

    >>> Colors = make_choices('Colors', [(1, 'RED', 'red'),
    ...                                  (2, 'GREEN', 'green')])

    >>> Colors.RED
    1

    If 2-tuples are passed, the first value will be used for both
    value and constant name.
    """
    class Choices(object):
        names = []
        values = []
        titles = {}
        choice_list = []
        name_for_value = {}

        @classmethod
        def get_value_for_name(cls, name):
            for v, n in zip(cls.values, cls.names):
                if n == name:
                    return v

    Choices.__name__ = name

    for d in choice_list:
        if len(d) == 3:
            v, name, title = d
        else:
            name, title = d
            v = name
        assert name.upper() == name
        setattr(Choices, name, v)
        Choices.values.append(v)
        Choices.names.append(name)
        Choices.titles[v] = title
        Choices.choice_list.append((v, title))
        Choices.name_for_value[v] = name

    return Choices


def make_class_enum(enum_name, choice_list):
    """
    Given a name of a class and a list of (val, constant name, title, class),
    returns an enum class representing the choices, and a dictionary mapping
    choices to classes.

    Also adds the choice number to the class as attribute 'enum_val'
    """

    enum = make_choices(enum_name,
                        [(val, name, title)
                         for (val, name, title, cls) in choice_list])
    enum.classes = dict((val, cls) for (val, name, title, cls) in choice_list)
    for val, cls in enum.classes.items():
        cls.enum_val = val
    return enum


class LazyDict:
    def __init__(self, source):
        self.source = source

    def __getitem__(self, item):
        return self.source(item)


class lazy_dict_like:
    """
    Used as a decorator to turn a method of a single
    parameter into a property that returns a dict-like
    object.

    Useful in Django templates which don't allow function/method calls, used in
    combination with 'lookup' template filter.

    """
    def __init__(self, method):
        self.method = method

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return LazyDict(lambda item: self.method(obj, item))
