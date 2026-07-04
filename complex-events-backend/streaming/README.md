# 注意事项

本包`streaming` 下只有`process`参与`flask`服务

其余文件主要用于[./docker-compose.yaml](./docker-compose.yaml) 构建流媒体容器，支持传输流式数据

构建容器完成之后需要启动容器


# 推流
可以使用OBS软件测试


# 启动容器+推流
可以在localhost:8889下看到由[./html/index.html](./html/index.html)提供的画面

该功能也已经集成到前端，需要手动填写推流地址

> 推流地址以`/hls/xxxxx.m3u8`等格式结尾
> 
> 可从[./html/index.html](./html/index.html)文件中获得