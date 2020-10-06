# coding: utf-8

import logging
from .env import ENV 
from ..enums import EnumEnv

LOG_CONF = {
    'log_name': 'MODEL',
    'log_level': logging.DEBUG if ENV == EnumEnv.DEV else logging.INFO,
    'log_file': 'log/main.log',
    'log_format': '%(levelname)s\t%(asctime)s\t%(remote_addr)s\t%(url)s : %(message)s',
}
