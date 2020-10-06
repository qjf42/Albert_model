## 1. 介绍
聊天机器人的模型服务，每个目录下是一个模型

## 2. 目录结构
```
- processor     // 模型处理基类
- model_server  // 模型服务server
- chichat       // 闲聊模型
```

## 3. 使用方式
### 3.1 启动
1. 将当前目录放在一个dev路径下，e.g
    ```
    mkdir dev && cd dev && git clone https://github.com/qjf42/Albert_model.git && cd Albert_model
    ```
2. 部署到测试或线上环境
    ```
    # 会新建../test ../prod目录，将dev目录下的代码同步过去，并调整相关配置
    ./dist.sh test && cd ../../test/Albert_model
    # ./dist.sh prod && cd ../../prod/Albert_model
    ```
3. 启动服务
    ```
    ./start.sh
    ```
    端口：5512(test)/5502(prod)
4. 注册模型
    - 模型上线需要注册，不需重启整个服务
      - 简单设计，为保证可用，服务为单进程
    - 每个目录下有一个`processor.ProcessorBase`的子类和一个`conf`变量
    - e.g POST http://127.0.0.1:5512/register?model_name=chichat&model_dir=chichat&force_reload=1
      - `model_name`: 模型名，后续调用的id
      - `model_dir`: 模型目录
      - `force_reload`: 默认False，是否强制reload

### 3.2 调用
#### 3.2.1 GET/POST /infer
- 请求

    | 字段 | 类型 | 说明 |
    |-|-|-|
    | model_name | str | 模型id |
    | ... | | 其它需要的参数 |

- 返回

    | 字段 | 类型 | 说明 |
    |-|-|-|
    | success | bool | |
    | err_no | int | 参考`model_server.enums.EnumResponseError` |
    | err_msg | str | |
    | data | dict | 模型结果数据 |
