from django.core.signing import BadSignature, dumps, loads


def sign_payment_info(d):
    """
    Takes a dict of payment info, and returns a string with MAC
    """
    return dumps(d, salt="learnscripture.payments")


def unsign_payment_string(s):
    """
    Takes a signed payment string, and returns a dict of payment
    info if the signature is good, or None otherwise.
    """
    try:
        # Only allow values 1 day old, that is more than enough time to complete payment
        return loads(s, salt="learnscripture.payments", max_age=24 * 3600)
    except BadSignature:
        return None
