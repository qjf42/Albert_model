# coding: utf-8

import pathlib
import importlib
import inspect
from typing import Dict, Any

from .test_case import TestCase


class ProcessorBase:
    '模型处理的基类'
    def __init__(self, name: str):
        self.name = name
        self.conf = {}
        self.test_cases = []

    @classmethod
    def load(cls, name: str, module_path: pathlib.Path, conf: Dict[str, Any]):
        ret = cls(name)
        ret.path = module_path
        ret.conf = conf
        ret._load(conf)
        ret.test()
        return ret

    def _load(self, conf: Dict[str, Any]) -> None:
        raise NotImplementedError

    def get_resource_path(self, rel_path: str) -> str:
        return str(self.path / rel_path)

    def run(self, params: Dict[str, Any]):
        try:
            params = self.preprocess(params)
        except Exception as e:
            raise Exception(f'Preprocess error: {e}')
        try:
            model_res = self.model_process(params)
        except Exception as e:
            raise Exception(f'Model process error: {e}')
        try:
            model_res = self.postprocess(params, model_res)
        except Exception as e:
            raise Exception(f'Postprocess error: {e}')
        return model_res

    def preprocess(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    def model_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def postprocess(self, params: Dict[str, Any], model_res: Dict[str, Any]) -> Dict[str, Any]:
        return model_res

    def test(self) -> None:
        self.test_cases = [TestCase(**c) for c in self.conf.get('test_cases', [])]
        for case in self.test_cases:
            try:
                res = self.run(case.input)
            except Exception as e:
                raise Exception(f'Processor {self.name} test inference error: {e}')
            try:
                assert case.validate(res)
            except Exception as e:
                raise Exception(f'Processor {self.name} test result error: {e}')


class ProcessorFactory(dict):
    def __init__(self):
        '''dir => ProcessorBase'''
        super().__init__()
        # dir => Module
        self._modules: Dict[str, Any] = {}

    def load(self, name: str, dir_name: str, force_reload: bool = False) -> ProcessorBase:
        '''模型处理器的工厂方法
        Args:
            name: 模型名
            dir_name: 模型处理器的目录，其中至少需要包括一个ProcessorBase的子类和一个conf字典，具体的模型文件也放在里面
        '''
        module_path = pathlib.Path(dir_name)
        if not module_path.exists():
            raise ValueError(f'Processor path {dir_name}[{module_path.absolute()}] does not exist!')
        # load module
        if dir_name in self._modules:
            if force_reload:
                module = self._modules[dir_name]
                module = importlib.reload(module)
            else:
                return self[dir_name]
        else:
            module = importlib.import_module('..' + dir_name, '.')
        # look for processor subclass in module
        try:
            cls_members = inspect.getmembers(module, inspect.isclass)
            # XXX 不知道为什么issubclass不管用
            # processor_cls = next(c for _, c in cls_members if issubclass(c, ProcessorBase))
            processor_cls = next(c for _, c in cls_members if c.__base__.__name__ == 'ProcessorBase')
        except:
            raise ValueError(f'No subclass of `ProcessorBase` found in {dir_name}')
        processor = processor_cls.load(name, module_path, module.conf)
        self._modules[dir_name] = module
        self[dir_name] = processor
        return processor
