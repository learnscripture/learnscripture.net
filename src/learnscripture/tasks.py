import logging

from learnscripture.utils.tasks import task

logger = logging.getLogger("task_queue_debug")


@task
def message(message: str):
    logger.debug("Message %s", message)
    if message == "crash":
        raise AssertionError("Crashed!")
    print(message)
