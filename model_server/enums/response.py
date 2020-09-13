# coding: utf-8
'''服务返回时的错误'''

from enum import Enum


class EnumResponseError(Enum):
    SUCCESS = (True, 0, '')
    INVALID_PARAMS = (False, 100, '')
    UNKNOWN_ERROR = (False, 500, '')

    def __init__(self, success: bool, err_no: int, err_msg: str):
        self.success = success
        self.err_no = err_no
        self.err_msg = err_msg

    def set_err_msg(self, err_msg):
        if err_msg:
            self.err_msg = err_msg
        return self
