import logging

from src.common.ClientMsgType import ClientMsgType
from src.common.ServerMsgType import ServerMsgType


def setup_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    stream_h = logging.StreamHandler()
    file_h = logging.FileHandler('../logs.log')

    stream_h.setLevel(logging.DEBUG)
    file_h.setLevel(logging.DEBUG)

    formatter = logging.Formatter(fmt='[%(asctime)s] %(name)s - %(levelname)s: %(message)s',
                                  datefmt='%d/%m/%Y %H:%M:%S')
    stream_h.setFormatter(formatter)
    file_h.setFormatter(formatter)

    logger.addHandler(stream_h)
    logger.addHandler(file_h)
    return logger


def format_msg(identity, body, message_type):
    formatted_message = {
        "identity": identity,
        "body": body,
        "type": message_type
    }
    return formatted_message
