# complex-event

# Start
## Frontend
```shell
cd complex-event-frontend
npm run dev
```

## Backend
```shell
cd complex-event-backend
python main.py
```

# 流式数据处理
## 运行
如果需要顺利运行的话还需要部署流媒体服务器，
使用后端文件夹/streaming目录下的docker-compose.yaml创建docker容器


需要ffmpeg 并且配置好环境变量

> 配置好 = 系统终端默认能够执行ffmpeg命令，并且不报错

# 注意事项
1. 系统首次运行会自动加载音频转文本模型whisper, 自动从网络中下载，下载路径未知，大概率是系统默认路径。下载速度可能受网络硬性