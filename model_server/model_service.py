# coding: utf-8

import gc
from typing import Any, Dict

import flask

from .conf import LOG_CONF
from .enums import EnumResponseError
from .interfaces import Response
from .utils import log_utils
from ..processor import ProcessorBase, ProcessorFactory


class ModelService:
    def __init__(self):
        self.processor_factory = ProcessorFactory()
        # 模型名 => 位置 => processor之间一一映射
        self._name2dirs: Dict[str, str] = {}

    def _check_model(self, name: str) -> ProcessorBase:
        try:
            return self.processor_factory[self._name2dirs[name]]
        except:
            raise ValueError(f'Model [{name}] does not exisit')

    def register(self, name: str, model_dir: str, force_reload: bool = False):
        '''模型注册上线、更新'''
        self.processor_factory.load(name, model_dir, force_reload)
        self._name2dirs[name] = model_dir
        gc.collect()

    def unregister(self, name: str):
        '''模型下线'''
        self._check_model(name)
        dir_name = self._name2dirs[name]
        del self._name2dirs[name]
        del self.processor_factory[dir_name]
        gc.collect()

    def infer(self, name: str, params: Dict[str, Any]):
        model = self._check_model(name)
        return model.run(params)

    """
    def memory_usage(self):
        for name in self.models:
            pass

    def profile(self, name: str):
        self._check_model(name)
        print(self.models[name].profile())
    """


'''FLASK'''

SERVICE = ModelService()
app = flask.Flask(__name__)
log_utils.set_app_logger(app.logger, **LOG_CONF)


def parse_req(options=None):
    req = flask.request
    params = dict(req.args)
    params.update(req.get_json(silent=True) or {})
    params.update(req.form or {})
    if not options:
        return params
    ret = {}
    for key, required in options.items():
        val = params.get(key)
        if val is None and required:
            raise ValueError(f'Parameter [{key}] is missing.')
        ret[key] = val
    return ret


@app.route('/register', methods=['POST'])
def register():
    param_options = {
        'model_name': True,
        'model_dir': True,
        'force_reload': False,
    }
    try:
        params = parse_req(param_options)
        model_name = params['model_name']
        model_dir = params['model_dir']
        force_reload = params.get('force_reload', False)
    except Exception as e:
        resp = Response().set_error(EnumResponseError.INVALID_PARAMS, str(e))
        return flask.jsonify(resp)
    app.logger.info(f'Registering model [{model_name}] in [{model_dir}]...')
    try:
        SERVICE.register(model_name, model_dir, force_reload)
        app.logger.info(f'Registering model [{model_name}] succeeded.')
    except Exception as e:
        resp = Response().set_error(EnumResponseError.UNKNOWN_ERROR, str(e))
        app.logger.info(f'Registering model [{model_name}] failed, {e}.')
    return flask.jsonify(Response())


@app.route('/unregister', methods=['POST'])
def unregister():
    param_options = {
        'model_name': True,
    }
    try:
        model_name = parse_req(param_options)['model_name']
    except:
        resp = Response().set_error(EnumResponseError.INVALID_PARAMS)
        return flask.jsonify(resp)
    try:
        resp = SERVICE.unregister(model_name)
    except Exception as e:
        resp = Response().set_error(EnumResponseError.UNKNOWN_ERROR, str(e))
    return flask.jsonify(resp)


@app.route('/infer', methods=['GET'])
def infer():
    params = parse_req()
    try:
        model_name = params.pop('model_name')
    except:
        resp = Response().set_error(EnumResponseError.INVALID_PARAMS, 'missing param "model_name"')
        return flask.jsonify(resp)
    try:
        resp = Response()
        for k, v in SERVICE.infer(model_name, params).items():
            resp.add_data(k, v)
    except Exception as e:
        resp = Response().set_error(EnumResponseError.INFER_ERROR, str(e))
    return flask.jsonify(resp)
