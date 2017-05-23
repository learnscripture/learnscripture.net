from __future__ import absolute_import

import logging

from learnscripture.celery import app

logger = logging.getLogger('celerydebug')


@app.task()
def message(message):
    logger.debug("Message %s", message)
    print(message)
