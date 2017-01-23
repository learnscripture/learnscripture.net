from __future__ import absolute_import

import logging

from celery.task import task

logger = logging.getLogger('celerydebug')


@task()
def message(message):
    logger.debug("Message %s", message)
    print(message)
