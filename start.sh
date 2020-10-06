#!/bin/bash

set -eu

ENV=dev
ENV_DIR=$(cd $(dirname "$0") && pwd)
cd ${ENV_DIR}

if [ ${ENV} = "prod" ]; then
    PORT=5502
elif [ ${ENV} = "test" ]; then
    PORT=5512
else
    echo "Unknown environment ${ENV}, options: test/prod"
    exit 1
fi


export PYTHONPATH=${ENV_DIR}:${PYTHONPATH:-}
export FLASK_APP=${ENV_DIR}/model_server/model_service.py

mkdir -p log

old_pid=$(ps -eO pid,tname | grep flask | grep ${PORT} | cut -d' ' -f2)
if [ -n "${old_pid}" ]; then
    kill -9 ${old_pid}
fi

flask run --host=0.0.0.0 -p ${PORT}
