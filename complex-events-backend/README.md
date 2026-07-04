# Complex Events Backend

后端已精简为只服务以下前端页面：

- 登录页面
- 数据管理 / 数据上传
- 本体管理 / 事件列表
- 本体管理 / 基于图的事件关联要素可视化

## 保留接口

- `/user/login`、`/user/info`、`/user/logout`
- `/file`、`/file/upload`、`/file/deleteReports`、`/file/search`、`/file/searchById`
- `/data/list`、`/data/find`、`/data/eventLink`、`/data/eventLinkResult`、`/data/delete`、`/data/edit`、`/data/addAction`
- `/graph/latest`、`/graph/search`、`/graph/expandNode/<id>`、`/graph/expandCommonNodes`、`/graph/build`、`/graph/rebuild`、节点/边编辑、子图保存/读取接口
- `/associate/*` 中事件列表页直接使用的规则、共同要素、关系入图和聚类接口

## 配置项

配置文件位于 `app/config.py`，也可以通过 `.env` 或环境变量覆盖。

- `LOGIN_USERNAME`: 登录用户名
- `LOGIN_PASSWORD`: 登录密码
- `LOGIN_DISPLAY_NAME`: 登录后展示名称
- `UPLOAD_FOLDER`: 上传文件保存目录
- `SUB_GRAPH_PATH`: 子图文件保存目录
- `LOG_DIR`: 日志目录
- `MONGODB_HOST`: MongoDB-主机
- `MONGODB_PORT`: MongoDB-端口
- `MONGODB_USER`: MongoDB-用户名
- `MONGODB_PASSWORD`: MongoDB-密码
- `MONGODB_DATABASE`: MongoDB-数据库名
- `MONGODB_REPORTS_COLLECTION`: MongoDB-上传文件元数据集合名
- `MONGODB_EXTRACT_RESULT_COLLECTION`: MongoDB-事件列表集合名
- `MONGODB_EVENT_LINK_COLLECTION`: MongoDB-事件关联集合名
- `MONGODB_SUB_GRAPH_COLLECTION`: MongoDB-子图集合名
- `MONGODB_EVENT_LINK_RULES_COLLECTION`: MongoDB-事件关联规则集合名
- `NEO4J_URI`: Neo4j-连接地址
- `NEO4J_USER`: Neo4j-用户名
- `NEO4J_PASSWORD`: Neo4j-密码

## 运行

```bash
pip install -r requirements.txt
python main.py
```

默认端口为 `8800`。
