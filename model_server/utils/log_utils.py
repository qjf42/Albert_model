#coding: utf-8

import logging
from flask import has_request_context, request
from flask.logging import default_handler


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)


def set_app_logger(logger, log_level, log_file, log_format, **kwargs):
    '''配置flask app的logger'''
    logger.setLevel(log_level)
    formatter = RequestFormatter(log_format)
    default_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


_loggers = {}
def get_logger(log_name, log_level, log_file, log_format, **kwargs):
    global _loggers
    if log_name in _loggers:
        return _loggers[log_name]

    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)
    formatter = logging.Formatter(log_format)

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    _loggers[log_name] = logger

    return logger
