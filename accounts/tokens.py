from django.core.signing import BadSignature, TimestampSigner

login_signer = TimestampSigner(salt="learnscripture:accounts.tokens.login_token")
LOGIN_TOKEN_MAX_AGE = 10 * 24 * 3600  # 10 days in seconds


def get_login_token(account):
    return login_signer.sign(account.username)


def check_login_token(token):
    try:
        return login_signer.unsign(token, max_age=LOGIN_TOKEN_MAX_AGE)
    except BadSignature:
        return None
