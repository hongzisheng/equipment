# 浏览器模拟爬虫

本文件夹下（app.spider）使用的是`Chorme` 浏览器模拟爬虫

## 使用方法
### 下载符合当前电脑`Chrome` 浏览器版本的`chromedriver`驱动

[下载地址](https://googlechromelabs.github.io/chrome-for-testing/) 可能会发生变化

跳转失败的时候尝试在浏览器中搜索 **chromedriver下载**

> 注意 **ATTENTION**:
> 
> 1. 下载的名称叫 `chromedriver` 不是叫 ~~`chrome`~~ 
> 2. 选择合适当前电脑系统和架构的版本，比如win64,win32,`mac-x64`,`mac-arm` 等 
> 3. chromedriver适配的版本必须与chrome版本一致，chrome浏览器版本可以在 `浏览器设置-关于Chrome` 中查看,
> 查看浏览器版本与下载页面的版本是否一致（一般匹配最新版）


### 下载好之后将运行文件放到当前文件夹（app.spider）

下载好之后如果是压缩包先解压缩

然后
只需要把可执行文件复制过来，比如windows 时候是`chromedriver.exe`

### 替换webdriver_util.py文件中的驱动路径

把绝对路径复制到Service()方法里面

例如：
```python
    service = Service('E:\complex-events\complex-events-backend\spider\chromedriver.exe')
```

## 完成
接下来即可运行app.spider文件夹下的任何文件