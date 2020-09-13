# coding: utf-8

from importlib import reload, __import__


class DynamicLoader:
    @staticmethod
    def load(class_path: str, **kwargs):
        cls = __import__(class_path)
        return cls(**kwargs)
