BaiduPanFilesTransfers
-----
#### 介绍使用

百度网盘批量转存工具,基于Python 3.8+Tkinter
详细介绍使用请访问:[小众软件](https://www.appinn.com/baidupan-files-transfers/)
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
**2020.7.26 更新版本 1.3**

修复部分秒传链接无法识别问题

**2020.7.7 更新版本 1.2**

修复由于md5值大小写原因造成的秒传链接转存失败

**2020.6.19 更新版本 1.1**

增加对提取码不正确,文件已被删除,弹出验证码状态判断

**2020.6.16 更新版本 1.0**

增加对文件夹和秒传链接的支持

