import logging

from learnscripture.celery import app

logger = logging.getLogger('celerydebug')


@app.task()
def message(message):
    logger.debug("Message %s", message)
    if message == 'crash':
        raise AssertionError("Crashed!")
    print(message)
