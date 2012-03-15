import re
import urlparse
import urllib


from raven.contrib.django.models import get_client


SENSITIVE_RE = re.compile('password|secret', flags=re.IGNORECASE)


def sanitise_request_data(data):
    http_data = data.get('sentry.interfaces.Http', None)
    if http_data is not None:
        if http_data.get('method', '') == 'POST':
            post_data = http_data.get('data', None)
            if post_data is not None:
                # Seems to be some confusion about whether post_data is a string
                # or dict.
                string_data = isinstance(post_data, basestring)
                if string_data:
                    params = urlparse.parse_qs(post_data)
                else:
                    params = post_data
                for k in params.keys():
                    if SENSITIVE_RE.search(k):
                        params.pop(k)
                if string_data:
                    http_data['data'] = urllib.urlencode(params.items(), doseq=True)
                else:
                    http_data['data'] = params
    return data

def extra(**kwargs):
    """
    Create a dictionary of extra data, as required by Raven for correct logging.
    """

    if 'request' in kwargs:
        # Special handling for Sentry:
        request = kwargs.pop('request')
        client = get_client()
        data = sanitise_request_data(client.get_data_from_request(request))
        data.update(kwargs)
    else:
        data = kwargs

    return {'data':data}
