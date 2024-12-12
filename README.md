# 程序介绍

百度网盘批量转存程序，基于 `Python 3.10` + `Tkinter` 构建，主要用于批量转存网络上分享的资源到自己的百度网盘。此外还带有批量分享和批量检测链接有效性的功能。

程序主界面：

![百度网盘批量转存程序主界面截图](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/v2.8.0.jpg)

## 下载及运行

程序开发编译环境为 `Win10 x64` 专业版，操作系统 `Win7` 以上可直接下载运行，其他操作系统需要自行编译或配置运行环境。

下载方式：

- 方式一：到 [release](https://github.com/hxz393/BaiduPanFilesTransfers/releases) 页面下载最新版的 `exe` 文件，文件名为 `BaiduPanFilesTransfers.exe`，下完可直接打开使用。
- 方式二：到 [百度网盘](https://pan.baidu.com/s/1RK7uBqaqgqJHLJbadXI48g?pwd=6666) 下载对应压缩包 `BaiduPanFilesTransfers.zip`，下完后请解压缩再使用。

如果之前有运行过旧版本，直接用新版本文件覆盖掉旧文件即可使用。

## 手动编译

手动编译需要事先安装好 `Python 3.6` 以上版本。

编译步骤如下：

1. 在安装有 `Git` 的主机上克隆本项目：

   ```sh
   git clone https://github.com/hxz393/BaiduPanFilesTransfers.git
   ```

   或者在 [项目主页](https://github.com/hxz393/BaiduPanFilesTransfers) 点击蓝色`<> Code` 按钮选择 `Download ZIP` 选项，[下载](https://github.com/hxz393/BaiduPanFilesTransfers/archive/refs/heads/master.zip) 源码压缩包，下载完毕后解压缩压缩包。

2. 在命令行中切换到本项目路径。

   例如，在 Windows 中，打开 `CMD` 命令提示符或 `PowerShell`，输入：

   ```sh
   cd B:\2.脚本\BaiduPanFilesTransfers-master
   ```

   在 Linux/macOS 中，路径的分隔符会不同：

   ```sh
   cd /root/BaiduPanFilesTransfers-master
   ```

   如果使用 `PyCharm` 作为 IDE，可以直接在自带的控制台中输入后面的打包命令。

3. 使用 `venv` 创建并启用虚拟环境：

   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```

   在 Linux/macOS 下启动虚拟环境命令稍有不同：

   ````
   python -m venv venv && source venv/bin/activate
   ````

4. 安装项目依赖，指定使用国内科大的镜像源：

   ```sh
   pip install -r requirements.txt --index https://mirrors.ustc.edu.cn/pypi/web/simple/
   ```

   Windows 的 Python 安装包一般会默认安装 `Tkinter`。macOS 用户则需要手动安装，对应 Homebrew 命令为：

   ```sh
   brew install python-tk # 也可以指定 Python 版本，如 brew install python-tk@3.12
   ```

5. 使用 `pyinstaller` 命令编译打包成可执行文件：

   ```sh
   pyinstaller -F -w -i BaiduPanFilesTransfers.ico --hidden-import=tkinter --clean -n BaiduPanFilesTransfers BaiduPanFilesTransfers.py
   ```

   如果过程没有异常，可执行文件 `BaiduPanFilesTransfers.exe` 会生成到 `dist` 目录下面。

6. （可选）使用 `deactivate` 命令退出当前环境：

   ```
   venv\Scripts\deactivate.bat
   ```

## 代码贡献

请提交 pull request 到 dev 分支，待我验证测试通过再合并到主分支。

## 开源许可

本程序采用 [GPL-3.0 license](https://github.com/hxz393/BaiduPanFilesTransfers/blob/master/LICENSE) 源授权许可协议，若违背开源社区的基本准则，将开源项目据为私有用于商业用途，属于侵权行为，本人将追究法律责任。



# 程序使用

获取 Cookies 为必须步骤，大多数运行错误都是 Cookies 不正确造成，请仔细阅读获取方法。

## 获取 Cookies

使用 `Chrome` 或类似浏览器（最好用无痕式窗口模式）登录 [百度网盘主页](https://pan.baidu.com/)，完全载入后按 `F12` 键调出控制台。选择 `网络（Network）` 选项卡。

如下图所示，目前应该空空如也：
![向导图1](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-1.png)
按 `F5` 刷新页面，下面会新增多条记录，点击以 `main` 开头的记录，右边会出现菜单，显示 `标头(Headers)`、`响应(Response) ` 等内容。在标头页面往下翻，找到请求标头中以 `Cookie:` 开头的行，后面有一串以 `XF` 开头的内容，这就是需要找的 `Cookies`。把它们全部选中，右键选择复制，粘贴到程序对应输入框内：
![向导图2](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-2.png)

**注意一定获取 `main` 页面下的 Cookies**，其他页面的 Cookie 不完整，会出现各种转存失败问题。直接访问地址：[main 页面](https://pan.baidu.com/disk/main)

## 输入保存位置

保存位置如果留空不填，资源会保存到根目录下，打开百度网盘主页便能看到。

输入文件保存位置后，如果目录不存在，会自动新建目录。如果目录已存在，则直接转存在指定目录下。

支持指定二级目录，例如，要保存到 `test` 目录内的 `2024-01-02` 目录中，填入 `test/2024-01-02` 即可。

保存位置（目录名）不能包含大多数英文特殊符号，包括：`>`、`|`、`*`、`?`、`:`、`\` 等，否则程序会检测到并中断运行。

如果保存路径加文件名长度超过 `255` 个字符，用百度网盘客户端下载文件时会失败，所以应尽量使用短目录名。

## 输入网盘链接

程序已尽可能适应常见的百度网盘链接格式。如出现提示「不支持的链接」或「链接错误」，请检查输入链接是否符合下面的格式之一：

```sh
https://pan.baidu.com/s/1nvBwS25lENYceUu3OMH4tg 6img
https://pan.baidu.com/s/1nvBwS25lENYceUu3OMH4tg?pwd=6img
https://pan.baidu.com/s/1nvBwS25lENYceUu3OMH4tg 提取码：6img
https://pan.baidu.com/s/1nvBwS25lENYceUu3OMH4tg 提取:6img
https://pan.baidu.com/s/1EFCrmlh0rhnWy8pi9uhkyA
https://pan.baidu.com/share/init?surl=W7U9g47xiDez_5ItgNIs0w
https://pan.baidu.com/e/1X5j-baPwZHmcXioKQPxb_w rsss
目录名 https://pan.baidu.com/s/1eOrU0S9VLoe4GgAy2gZlmw z6r4
```

## 执行批量转存

所有信息输入完毕后，点击「批量转存」按钮来执行批量转存百度网盘链接。

转存过程中可以「暂停/恢复」，也可以直接点击程序窗口右上角的关闭按钮来中止运行。

如果想加快转存速度，可多开程序，分批同时转存。总转存速度不要超过每分钟 `60` 条链接。

## 执行批量分享

批量分享是指分享指定目录下的文件或文件夹，每个生成一条分享链接。==百度网盘官方现已推出批量分享功能，在网页端操作即可，优先使用。==

执行批量分享之前，同样需要先输入 `Cookies` 和要分享的目标路径，然后点击「批量分享」按钮准备执行。此时会弹出分享设置弹窗：

![百度网盘批量转存程序分享设置界面截图](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-4.jpg)

设置好分享期限和提取码（支持随机）后，点击确定开始执行批量分享，请等待运行完成。此时原先链接输入框内，会插入即将分享的文件名；日志输入框内，会显示生成的分享链接和结果：

![百度网盘批量转存程序批量分享结果截图](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-5.jpg)

百度网盘硬性限制，**单帐号每日最多只能创建 300 个分享链接**，之后会报错，非程序方面限制。

## 使用系统代理（选项）

程序默认会绕过网络系统代理，但不能绕过网络全局代理。

如果处于特殊网络环境下，需要配置网络系统代理模式，才能正常访问百度网盘，勾选上「系统代理」框后，再执行转存。

## 使用指定目录（选项）

用于指定转存文件到多个不同的目录。效果如下：

![百度网盘批量转存指定目录功能](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-7.jpg)

勾选以后，将支持类似于 `自设目录 https://pan.baidu.com/s/1eOrU0S9VLoe4GgAy2gZlmw z6r4` 的链接，`自设目录` 会创建到「转存目录」（步骤 2 中输入的目录）中，文件转存到 `自设目录` 里面。

如果输入的是普通链接，也就是不带目录名，以 `http` 开头的链接，则每个链接将单独保存在数字为命名的子目录中。例如「转存目录」中输入的 `test`，则第一个链接保存在 `test/1` 中，第二个链接保存在 `test/2` 中，以此类推。

注意，此模式要求**必须输入转存目录**。连接中的指定目录名**不能包含空格**，否则只会取到空格前一截作为目录名。

## 使用检测模式（选项）

勾选此模式后，点击「批量转存」来运行，将对输入的链接可用性进行检查，并不执行转存操作：

![百度网盘批量转存程序批量检测结果截图](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-6.jpg)

**请勿频繁对相同的链接进行检测**，会导致弹验证码。



# 常见问题

使用程序遇见错误时，先查看下面总结的一些常见问题和解决方案。再查看所有 [Issue](https://github.com/hxz393/BaiduPanFilesTransfers/issues) 中是否有同样问题。如果都没有帮助，再提交反馈。

## 转存成功，但实际上没有转存

转存普通链接时出现的问题，初步发现于 2023.09.20。

**原因**：百度网盘 cookie 调整，不能再使用原先保存的 cookie。

**解决**：重新在浏览器获取新的 cookie，即可正常工作。

## 转存失败，错误代码（31500）

旧版本转存秒传链接时的错误。

**原因**：秒传已不能使用。

**解决**：在新版本中，相关代码已剔除，请升级到新版本。

## 转存失败，错误代码 XX

程序突然不能转存。

**原因**：Cookie 失效或不正确；百度网盘改版，程序失效。

**解决**：先试着通过浏览器无痕模式打开百度网盘主页，登陆获取的 Cookie 看能不能正常工作。如果换过多台电脑和账号都不工作，那就是程序需要修复更新了。可以提交 [Issue](https://github.com/hxz393/BaiduPanFilesTransfers/issues) 反馈。

## 只有第一个链接转存成功

后面链接提示「链接访问次数过多」。

**原因**：Cookie 不正确。

**解决**：通过浏览器无痕模式打开百度网盘主页，重新登陆获取 Cookie 即可。

## 链接访问次数过多

**原因**：通常见于带提取码的链接。如果短时间内对着一个链接反复访问 3 次以上，不管提取码是否正确，都会触发百度网盘防御机制。如果直接在网页端访问链接，会发现要输入验证码。

**解决**：只影响单个链接，其他链接能够正常转存。可以手动转存个别出问题链接。如果所有链接都报这一错误，参考问题「只有第一个链接转存成功」的解决办法。

## 转存次数到达 1000 上限

连续转存 1000 个链接，再多 1 个都会报错，报错码千奇百怪。甚至网页端都无法再转存，提示「数据错误，请稍后重试」 。

**原因**：百度网盘基于 IP 地址层面的封锁，禁止用户大量转存。

**解决**：可以重启拨号路由器，更换对外 IP 地址。如果需要使用代理服务器，请勾选「使用系统代理」。

## 免费用户转存 500 文件限制

**原因**：一般常见于文件夹转存，免费用户被百度限制，文件夹内文件数超过 500 个，会提示「转存文件数超过限制」。

**解决**：暂时不打算支持，效率太低。有需要可以留一下其他 [开源](https://greasyfork.org/zh-CN/scripts/453280-%E7%99%BE%E5%BA%A6%E4%BA%91%E6%89%B9%E9%87%8F%E4%BF%9D%E5%AD%98) 或免费项目，建议开通百度网盘会员来解除限制。

## 百度群组文件转存

不支持转存群组文件。建议手动操作转存，或使用 [专用工具](https://www.52pojie.cn/thread-1882639-1-1.html)。

## 系统版本过低

`Win 10` 以下版本的操作系统，运行时提示缺少必要 `dll` 文件。

**原因**：操作系统太旧，无法支持 `Python 3.10` 。

**解决**：升级操作系统；或使用 `2.4.0` 版本；或参考「自行打包」方法打包。

## 已有同名文件或文件夹存在

有时明明转存成功，提示却是「转存失败，目录中已有同名文件或文件夹存在」。

**原因**：触发机制不明，欢迎提供线索。

**解决**：最好在网页端确认下，是虚报，还是真有同名但实际上不同的文件。视情况手动转存，或勾选「安全转存」功能。

 

# 更新日志
为避免更新日志过长，只保留最近更新日志。

## 版本 2.8.2（2024.12.12）

修复内容：

1. 指定链接转存到不同目录时，重复链接不会被忽略。

## 版本 2.8.1（2024.10.25）

更新内容：

1. 批量分享支持随机提取码；
2. 批量转存和检测时，日志增加文件名输出；
3. 其他 UI 界面显示优化调整（窗口大小、日志始终跳转到底部、提示文字等）。

## 版本 2.8.0（2024.05.11）

更新内容：

1. 修改安全转存功能为指定目录功能，一次性能将不同链接保存到不同目录中。

## 版本 2.6.0（2024.04.09）

更新内容：

1. 使用 `ttkbootstrap` 美化界面；
2. 添加对百度网盘企业版的支持；
3. 添加批量分享功能；
4. 添加检测模式功能。

## 版本 2.5.0（2024.03.14）

更新内容：

1. 添加链接自动去重和空格修剪功能；
2. 添加暂停恢复功能；
3. 添加转存间隔时间。

## 版本 2.4.0（2023.12.21）

更新内容：

1. 添加安全转存功能。

修复内容：

1. 剔除秒传转存相关代码；
2. 向下降级到 `python 3.6` 版本，`Win7` 系统也能使用了；
3. 修复图标模糊问题；
4. 代码结构优化调整。

## 版本 2.3.0（2023.09.08）

修复内容：

1. 修复秒传转存接口。

## 版本 2.2.2（2023.06.02）

修复内容：

1. 秒传转存换回旧接口。
