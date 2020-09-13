# coding: utf-8
'''开发/生产环境'''

from enum import Enum, auto


class EnumEnv(Enum):
    DEV = auto()
    PROD = auto()
