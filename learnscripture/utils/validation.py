from django.core.exceptions import BadRequest


def checked_int(value: str | None):
    """
    Like `int()` but raises BadRequest instead of ValueError or TypeError
    """
    try:
        return int(value)
    except ValueError, TypeError:
        raise BadRequest(f"Bad value {value}, expecting int")
