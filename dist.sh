#!/bin/bash
# 从dev环境下cp到test/prod环境

set -eu

DEV_DIR=$(cd $(dirname "$0") && cd .. && pwd)
[ ${DEV_DIR##*/} = "dev" ] && cd ${DEV_DIR} || (echo "Executable only in dev dir" && exit 1)

ENV=$(echo $1 | tr [:upper:] [:lower:])
if [ "x"${ENV} = "xprod" ] || [ "x"${ENV} = "xtest" ]; then
    DIST_DIR=${DEV_DIR}/../${ENV}/Albert_model
    mkdir -p ${DIST_DIR}
else
    echo "Unknown environment ${ENV}, options: test/prod"
    exit 1
fi

# cp
cd ${DEV_DIR}/Albert_model
rsync -av * ${DIST_DIR} --exclude=__pycache__

# 修改配置
sed "s/ENV=dev/ENV=${ENV}/g" start.sh > ${DIST_DIR}/start.sh
ENV_UPPER=$(echo ${ENV} | tr [:lower:] [:upper:])
sed "s/DEV/${ENV_UPPER}/g" model_server/conf/env.py > ${DIST_DIR}/model_server/conf/env.py
