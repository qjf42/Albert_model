# coding: utf-8

import sys
import gc
import time
import json
from typing import Any, Dict

import flask
import pandas as pd
import torch
# from torch.autograd import profiler

from .dynamic_loader import DynamicLoader
from .utils import log_utils


class PytorchModel:
    def __init__(self, name: str, model_conf_file: str):
        self.serving = False
        self.meta = {}
        self.name = name
        self.load(model_conf_file)

    @property
    def running(self):
        return self.model is not None and self.serving

    def load(self, model_conf_file: str) -> None:
        '''加载模型处理的pipeline和测试case'''
        with open(model_conf_file) as f:
            conf = json.load(f)

        # （如有）预处理模块
        self.preprocessor = None
        if 'preprocess' in conf:
            try:
                self.preprocessor = DynamicLoader.load(conf['preprocess'])
                assert callable(self.preprocessor), 'preprocessor not callable'
            except Exception as e:
                raise Exception(f'Failed to load preprocessor, {e}')

        # 模型
        try:
            self.model = torch.load(conf['model'], map_location=torch.device('cpu'))
            assert isinstance(self.model, torch.nn.Module), 'model is not a torch.nn.Module'
        except Exception as e:
            raise Exception(f'Failed to load model, {e}')

        # （如有）后处理模块
        self.postprocessor = None
        if 'postprocess' in conf:
            try:
                self.postprocessor = DynamicLoader.load(conf['postprocess'])
                assert callable(self.postprocessor), 'postprocessor not callable'
            except Exception as e:
                raise Exception(f'Failed to load postprocessor, {e}')

        self.test_case = (conf['test_case']['input'], conf['test_case']['expected'])

    def infer(self, params: Dict[str, Any]):
        if not self.running:
            raise Exception(f'Model {self.name} not initialized or running')
        if self.preprocess_module:
            params = self.preprocess_module(params)
        model_res = self.model(params)
        if self.postprocess_module:
            model_res = self.postprocess_module(params, model_res)
        return model_res

    def memory_usage(self):
        # param size
        size = sum(p.numel() * p.element_size() for p in self.model.parameters())
        # TODO
        # forward
        # output
        return f'{(size / 2**20):.2f}MB'

    def profile(self) -> pd.DataFrame:
        # https://pytorch.org/tutorials/recipes/recipes/profiler.html
        pass

    def test(self) -> bool:
        params, expected = self.test_case
        try:
            res = self.infer(params)
        except Exception as e:
            raise Exception(f'Model {self.name} test inference error: {e}')
        assert expected == res, f'Model {self.name} test error, expected({expected}) vs result({res})'
        return True

    def compare(self, model):
        pass


class ModelService:
    def __init__(self): 
        self.models: Dict[str, PytorchModel] = {}

    def register(self, name: str, model_conf_file: str):
        '''模型注册上线、更新'''
        new_model = PytorchModel(name, model_conf_file)
        self.models[name] = new_model
        gc.collect()

    def unregister(self, name: str):
        '''模型下线'''
        if name in self.models:
            del self.models[name]
            gc.collect()

    def infer(self, name: str, params: Dict[str, Any]):
        if name in self.models:
            return self.models[name].infer(params)

    def memory_usage(self):
        for name in self.models:
            pass

    def profile(self, name: str):
        print(self.models[name].profile())


'''FLASK'''

BOT = ModelService()
app = flask.Flask(__name__)
log_utils.set_app_logger(app.logger, **LOG_CONF)


def parse_req(options):
    ret = {}
    req = flask.request
    data = req.get_json(silent=True) or {}
    for key, required in options.items():
        val = req.args.get(key, data.get(key, req.form.get(key)))
        if val is None and required:
            raise ValueError(f'Parameter [{key}] is missing.')
        ret[key] = val
    return ret


@app.route('/register', methods=['POST'])
def register():
    param_options = {
        'query': True,
    }
    try:
        query = parse_req(param_options)['query'].strip()
    except:
        resp = BotResponse().set_error(EnumResponseError.INVALID_PARAMS)
        return flask.jsonify(resp)
    try:
        req = RequestFactory.get_request(EnumRequestSrcType.CMD, query, debug=True)
        resp = BOT.chat(req)
    except Exception as e:
        resp = BotResponse().set_error(EnumResponseError.UNKNOWN_ERROR, str(e))
    return flask.jsonify(resp)

