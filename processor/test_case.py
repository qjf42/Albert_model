# coding: utf-8

import inspect


class TestCase:
    def __init__(self, input, expected, res_func: str = None):
        self.input = input
        # 支持对infer结果做简单的变换，如len
        self.res_func = None
        if res_func is not None:
            self.res_func = eval(res_func)
            assert callable(self.res_func) and len(inspect.getfullargspec(self.res_func).args) == 1
        self.expected = expected

    def validate(self, res):
        res_func_expr = ''
        if self.res_func:
            res = self.res_func(res)
            res_func_expr = f'{self.res_func.__name__}(res)'
        assert self.expected == res, f'input({self.input}), expected {res_func_expr} ({self.expected}), got ({res})'
