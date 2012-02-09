from raven.contrib.django.models import get_client


def extra(**kwargs):
    """
    Create a dictionary of extra data, as required by Raven for correct logging.
    """

    if 'request' in kwargs:
        # Special handling for Sentry:
        request = kwargs.pop('request')
        client = get_client()
        data = client.get_data_from_request(request)
        data.update(kwargs)
    else:
        data = kwargs

    return {'data':data}
