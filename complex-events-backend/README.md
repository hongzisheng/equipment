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
- `SQLITE_DB_PATH`: SQLite 数据库文件路径，默认 `database/db.sqlite3`
- `SQLITE_REPORTS_COLLECTION`: 本地文档集合名，默认 `reports`
- `SQLITE_EXTRACT_RESULT_COLLECTION`: 本地文档集合名，默认 `extract_results`
- `SQLITE_EVENT_LINK_COLLECTION`: 本地文档集合名，默认 `event_links`
- `SQLITE_SUB_GRAPH_COLLECTION`: 本地文档集合名，默认 `sub_graph`
- `SQLITE_EVENT_LINK_RULES_COLLECTION`: 本地文档集合名，默认 `event_link_rules`

## 运行

```bash
pip install -r requirements.txt
python main.py
```

默认端口为 `8800`。
