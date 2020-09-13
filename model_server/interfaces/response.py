# coding: utf-8

from dataclasses import dataclass, field
from typing import Any, Dict
from ..enums import EnumResponseError, EnumResponseType


@dataclass
class Response:
    success: bool = True
    err_no: int = EnumResponseError.SUCCESS.err_no
    err_msg: str = None
    data: Dict = field(default_factory=dict)

    def add_data(self, k: str, v: Any):
        self.data[k] = v
        return self

    def set_query(self, query: str):
        return self.add_data('query', query)

    def set_error(self, err: EnumResponseError, err_msg: str = None):
        self.success = err.success
        self.err_no = err.err_no
        self.err_msg = err.err_msg
        return self

    @property
    def response(self) -> Dict[str, Any]:
        return self.data.get('response')

    def set_response(self, value: str, type=EnumResponseType.TEXT):
        return self.add_data('response', {
            'type': type.type,
            'value': value,
        })

    def add_debug(self, k: str, v, append=False):
        debug_info = self.data.setdefault('debug', {})
        if append:
            debug_info.setdefault(k, []).append(v)
        else:
            debug_info[k] = v
        return self
