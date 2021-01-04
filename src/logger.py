import logging.handlers
import os

handler = logging.handlers.WatchedFileHandler(os.environ.get('LOG_FILE', 'accommodation_checker.message.log'))
formatter = logging.Formatter(
    '%(asctime)s [%(name)-20s][%(levelname)-18s] %(message_body)s (%(filename)s:%(lineno)d)'
)
handler.setFormatter(formatter)
logger = logging.getLogger('Accommodation Checker')
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
logger.addHandler(handler)


def _log_message(message):
    """
    Logs messages to their respective

    Ordinary Properties logged:
        1. message sid
        2. status
        3. date created
        4. date sent
    Error Properties logged:
        1. message sid
        2. status
        3. date created
        4. error code
        5. error message
    :param message: twilio MessageInstance instance
    :return: None
    """
    if message.status == 'failed':
        log = {
            'sid': message.sid,
            'status': message.status,
            'date_created': message.date_create,
            'date_sent': message.date_sent
        }
        logger.error(''.join([f'{key}: {value}' for key, value in log.items()]))
    else:
        log = {
            'sid': message.sid,
            'status': message.status,
            'date_created': message.date_create,
            'error_code': message.error_code,
            'error_message': message.error_message
        }
        logger.info(logger.error(''.join([f'{key}: {value}' for key, value in log.items()])))


def _schedule_message_for_logging(message):
    # TODO: schedule message for logging with the custom event loop
    _log_message(message)


def log_message(func):
    """
    a decorator that logs the message returned by the decorated function
    :param func: decorator target function
    :return: None
    """

    def wrapper(*args, **kwargs):
        message = func(*args, **kwargs)
        _schedule_message_for_logging(message)
        return message

    return wrapper
