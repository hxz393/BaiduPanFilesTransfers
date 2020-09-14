BaiduPanFilesTransfers
-----
#### 介绍使用

百度网盘批量转存工具,基于Python 3.8+Tkinter
详细介绍使用请访问:[小众软件](https://meta.appinn.net/t/topic/16995/39)

![1.5版本截图](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/%E6%88%AA%E5%9B%BE1.5.jpg)

**1.获取Cookie和User-Agent:**

使用Chrome或类似浏览器访问百度网盘主页,完全载入后按F12调出控制台,选择网络(NetWork)选项卡,目前应该空空如也:
![向导图1](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-1.png)
按F5刷新页面,下面出现很多条记录,点击home那条右边会出现菜单,显示标头(Headers),响应(Response)等内容.看标头里往下翻找到Cookie项目,后面有一串以BAIDUID开头的长长内容,这就是需要找的Cookies了,把它们选中全部复制出来粘贴到软件对应输入框.
![向导图2](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-2.png)
再往下翻能看到User-Agent项目,同样把它复制粘贴到软件对应输入框便行了.软件会自动保存当前配置,下次无需再次操作.
![向导图3](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-3.png)

**2.输入保存目标和网盘链接:**

保存目录如果不输入则保存到根目录下,保存目录不存在会自动新建.

链接支持格式:

*标准链接*
```
https://pan.baidu.com/s/1EFCrmlh0rhnWy8pi9uhkyA 提取码：4444
https://pan.baidu.com/s/14Az6kqaluwtUDr5JH9WViA 提取:v70q
https://pan.baidu.com/s/1nvBwS25lENYceUu3OMH4tg 6img
https://pan.baidu.com/s/1EFCrmlh0rhnWy8pi9uhkyA
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

**3.注意事项:**

1.如在浏览器端登出百度账号,再次登录需要重新手动获取Cookie值,否则会提示获取不到bdstoken;

2.同一账号在多浏览器登录会导致获取不到shareid.请退出所有账号并重新打开唯一的浏览器登录并获取Cookie和User-Agent.
_ _ _
#### 下载使用
点到release页面下载bpftUI.exe,直接打开使用
_ _ _
#### 自行打包
1. 克隆项目,在CMD中切换至项目目录
2. 使用pyinstaller打包:
``
pyinstaller -F -w -i bpftUI.ico bpftUI.py
``
_ _ _
#### 更新日志
**2020.9.14 更新版本 1.6**

修复无验证码分享文件夹链接转存提示'验证码错误'问题

**2020.8.15 更新版本 1.5**

1.修复非文件多文件共享链接只转存第一个文件的问题;

2.增加User-Agent输入框以应对百度网盘新一轮更新;

3.增加配置保存功能.

**2020.8.12 更新版本 1.4**

修复百度更新后获取不到bdstoken问题

**2020.7.26 更新版本 1.3**

修复部分秒传链接无法识别问题

**2020.7.7 更新版本 1.2**

修复由于md5值大小写原因造成的秒传链接转存失败

**2020.6.19 更新版本 1.1**

增加对提取码不正确,文件已被删除,弹出验证码状态判断

**2020.6.16 更新版本 1.0**

增加对文件夹和秒传链接的支持

