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
            'date_created': message.date_created,
            'date_sent': message.date_sent
        }
        logger.error(' '.join([f'{key}: {value}' for key, value in log.items()]))
    else:
        log = {
            'sid': message.sid,
            'status': message.status,
            'date_created': message.date_created,
            'error_code': message.error_code,
            'error_message': message.error_message
        }
        logger.info(logger.error(' '.join([f'{key}: {value}' for key, value in log.items()])))


def log_updated_message(message):
    """Refreshes the message instance and logs it"""
    updated_message = message.fetch()
    _log_message(updated_message)
