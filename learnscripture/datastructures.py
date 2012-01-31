
def make_choices(name, choice_list):
    """
    Creates a class containing the given set of choices,
    which are specified as (value, constant name, user presentable title)
    e.g.

    >>> Colors = make_choices('Colors', [(1, 'RED', 'red'),
                                         (2, 'GREEN', 'green')])

    >>> Colors.RED
    1

    """
    class Choices(object):
        names = []
        values = []
        titles = {}
        choice_list = []

        @classmethod
        def get_value_for_name(cls, name):
            for v, n in zip(cls.values, cls.names):
                if n == name:
                    return v

    Choices.__name__ = name

    for (v, name, title) in choice_list:
        assert name.upper() == name
        setattr(Choices, name, v)
        Choices.values.append(v)
        Choices.names.append(name)
        Choices.titles[v] = title
        Choices.choice_list.append((v, title))

    return Choices
