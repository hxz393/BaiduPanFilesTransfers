BaiduPanFilesTransfers
=====
## 介绍使用

百度网盘批量转存工具,基于Python 3.8+Tkinter
详细介绍使用请访问:[小众软件](https://meta.appinn.net/t/topic/16995/39)

![1.12版本截图](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/%E6%88%AA%E5%9B%BE1.12.jpg)



## 下载软件

点到[release](https://github.com/hxz393/BaiduPanFilesTransfers/releases)页面下载bpftUI.exe,直接打开使用.



## 获取Cookie和User-Agent

使用Chrome或类似浏览器访问百度网盘主页,完全载入后按F12调出控制台,选择网络(NetWork)选项卡,目前应该空空如也:
![向导图1](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-1.png)
按F5刷新页面,下面出现很多条记录,点击main?from=homeFlow那条右边会出现菜单,显示标头(Headers),响应(Response)等内容.看标头里往下翻找到Cookie项目,后面有一串以BAIDUID开头的长长内容,这就是需要找的Cookies了,把它们选中全部复制出来粘贴到软件对应输入框.
![向导图2](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-2.png)
再往下翻能看到User-Agent项目,同样把它复制粘贴到软件对应输入框便行了.软件会自动保存当前配置,下次无需再次操作.
![向导图3](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-3.png)



## 输入保存目标和网盘链接

保存目录如果不输入则保存到根目录下,保存目录不存在会自动新建.

链接支持格式:

*标准链接*

```
https://pan.baidu.com/s/1EFCrmlh0rhnWy8pi9uhkyA 提取码：4444
https://pan.baidu.com/s/14Az6kqaluwtUDr5JH9WViA 提取:v70q
https://pan.baidu.com/s/1nvBwS25lENYceUu3OMH4tg 6img
https://pan.baidu.com/s/1EFCrmlh0rhnWy8pi9uhkyA
https://pan.baidu.com/share/init?surl=W7U9g47xiDez_5ItgNIs0w
```

*游侠 v1标准*

```
https://pan.baidu.com/#bdlink=QkQyMTUxNjJENzE5NDc4QkNBRDJGMTMyNTlFMTEzNzAjRkJBMTEzQTY1M0QxN0Q1NjM3QUQ1MEEzRTgwMkE2QTIjMzcxOTgxOTIzI1pha3VybyAyMDAxMjYuN3oK
bdlink=QkQyMTUxNjJENzE5NDc4QkNBRDJGMTMyNTlFMTEzNzAjRkJBMTEzQTY1M0QxN0Q1NjM3QUQ1MEEzRTgwMkE2QTIjMzcxOTgxOTIzI1pha3VybyAyMDAxMjYuN3oK
```

*梦姬标准*

```
965FEAFCC6DC216CB56128B531694C9D#495B4FB5879AE0B22A31826D33D86D80#802846691#梦姬标准.7z
```

*Go格式*

```
BaiduPCS-Go rapidupload -length=418024594 -md5=31f141fee63d038a46db179367315f3a -slicemd5=5b2c842f421143a9a49938dc157c52e6 -crc32=3179342807 \"/音乐/Yes/1969. Yes.zip\"
```

*PanDL标准*

```
bdpan://44K344Or44Kv44Gu5p6c5a6fICsg44Go44KJ44Gu44GC44Gq44CA5o+P44GN5LiL44KN44GXOFDlsI/lhorlrZAg5pel5paHLnppcHw2NDAxODQxNTd8ZDNjOTBmOTI3ZjUxYzIyMmRjMTc1NDM1YTY0OWMyYTJ8OTk4NTE0NDE3Y2I5Y2I0MTQ0MGRlZTFiMmMyNTYwMzY=`
```



## 注意事项

- 如在浏览器端登出百度账号,再次登录需要重新手动获取Cookie值,否则会提示获取不到bdstoken;

- 同一账号在多浏览器登录会导致获取不到shareid.请在其他浏览器上退出登录,并重新打开唯一的浏览器登录(建议使用Chrome)并获取Cookie和User-Agent.

- 如果依然有Cookie问题,或转存提示'无效登录',可以在网盘主页打开开发工具中,手动清除Cookie后重新登录.操作如下图所示:
![向导图4](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-4.jpg)



## 自行打包

- 克隆项目,在CMD中切换至项目目录.

- 使用pyinstaller打包:
  ``
  pyinstaller -F -w -i bpftUI.ico bpftUI.py
  ``



## 更新日志
**2023.05.12 更新版本 1.14**

1.调整程序UI，现在可以随意调整窗口大小;
2.使用 f-string 替代字符串拼接；
3.优化代码；
4.改正中文文本格式。


**2023.03.21 更新版本 1.13**

1.更换秒传转存请求接口,解决错误代码#9019;

2.添加程序运行图标.

**2023.01.08 更新版本 1.12.1**

修复秒传目录或文件名带"&"时不正确行为

**2023.01.03 更新版本 1.12**

1.更换秒传转存请求接口;

2.修改部分秒传出错提示文字.
