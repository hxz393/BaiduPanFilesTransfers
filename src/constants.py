"""
此模块放置全局静态变量。

:author: assassing
:contact: https://github.com/hxz393
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""
# 程序基本信息
MAIN_TITLE = 'BaiduPanFilesTransfers'
MAIN_VERSION = '2.7.0'
HOME_PAGE = 'https://github.com/hxz393/BaiduPanFilesTransfers'
# noinspection LongLine
# 图标使用 zlib 压缩后，再用 base64 编码的值
ICON_BASE64 = 'eJyFUw1MU1cUvjgyfa+vr++1WGw3FTKDtHVLQDPCtojLFlpKKY4pLE0EDAaEMuKyOBWmI8ZMZ5T6Ax2xpgKKCs5kGtT9KA5B/GFxAUpBES1TZ0Z0kWQZLMZ9O6+um1tIdl6+d+79vvPdd25eDmNR9EgSo3ccWx3NmJ4xlkggipinvBJLotn/RdQrsU16i9aXY5Z9HsonzNr9Jy06354F8r7cxJh6A2OImspoZq3PJ2rrckxab7dJ9k6YtJ9DgSWmHmZlLXsnTXJdz3xpr2vu3AMznvXOY7unWwyeNeX5bQ/ffesIEmQPFsZ5Ufn+t2htCqB2+xWkLzpAfA3Mes+jtxftr9y5s5uL9Byv2bLc/rrvl+vBMRS7WmCe9Rn83qu4cjGEuppOdJ0fQfeFEApyjuDYwV4MDYyNj49PrAQwbbZurXG2Zt3VLR+fppoRWOZUw/FmLYKB+7Cn7QFpSH15G3qv3cGDsV/xzZkBVBQfRklBY3+21RNnEN0uo1Qx2XLoMur3noNBLEd+bj2u9YRgiluHWLUbBk05mvydGA09wGtJ1cSVQa8ufawXi1fr1Ct9sZoifNFyCTu2nYROKET6ks0YvnEfmemfhvfz5rhxsXMIYz+P441Xq6AV8sOQVSuOSULueUnIQ13tKTT4z0JWv4cXZhXgxJeX8X3PTXz4gR8HG9sxGPwRP917CLt1E0TVsgh+UPPOCwKfjZLi3ejqCuBFowsC70RyUimOH+/E8PBddHT0ku7Bjet3YU1fDxWfFYbAZ/XxvP0QAcnJJQgEbiMjYz2UvYKYmHeQkJAPo3E5Fi9eQ2fdQ0qKm7SMMDguo43j7CU8b3ssSVnw+8/g6NF2zJy5lHTbv1BYSP+g9ybi410R7gmd8ZEo2l6i9ZDCpaa60d9/C2Vlu6BW2//2ajQONDR8hcbGr2mdGeFDKlXmAsY+maZSWSto/5sg2LFq1Q4MDIRQVLSd+l8KUcyE01mFwcFROBwb/vJaJ+nblYylhSdKp3Oqid9FmJAkB0pLPejrG0Fb2yU0N59FMDiKrVubIctOxfs7x9n2UR/yszOg1dpE0tbSGbep9ycpKWXYuNGPmppW5OVtpl6y/yD9Dumb/uv9J9KilTtRTRWh/ekdbaOUOzjOWk05KdJzJELTGfvuOcaqp5zqqUOpVTyK90+HRLty'
# 配置文件路径
CONFIG_PATH = 'config.ini'
# 颜色主题，可选值参见：https://ttkbootstrap.readthedocs.io/en/latest/themes/
COLOR_THEME = 'yeti'
# 作用于多个 UI 组件的左边距和上边距
MW_PADDING = (10, 0)
# 气泡提示出现位置，相对于组件右上间距
TOOLTIP_PADDING = 25
# 气泡提示显示等待延迟，毫秒
TOOLTIP_DELAY = 100
# 每次转存延时时间，单位为秒
DELAY_SECONDS = 0.1
# 转存数量限制
SAVE_LIMIT = 1000
# 百度网盘地址
BASE_URL = 'https://pan.baidu.com'
# 目录名禁用的非法字符
INVALID_CHARS = r'<>|*?\:'
# 分享下拉框选项
EXP_MAP = {"1 天": 1, "7 天": 7, "30 天": 30, "永久": 0}
# 颜色相关字典
COLOR_MAP = {
    'tooltip': 'light yellow',
    'placeholder': 'grey',
    'text': 'black',
}
# 默认请求头
HEADERS = {
    'Host': 'pan.baidu.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'navigate',
    'Referer': 'https://pan.baidu.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7,en-GB;q=0.6,ru;q=0.5',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}
# 错误代码对应错误信息字典
ERROR_CODES = {
    -1: '链接错误，链接失效或缺少提取码',
    -4: '转存失败，无效登录。请退出账号在其他地方的登录',
    -6: '转存失败，请用浏览器无痕模式获取 Cookie 后再试',
    -7: r'转存失败，转存文件夹名有非法字符，不能包含 < > | * ? \ :，请改正目录名后重试',
    -8: '转存失败，目录中已有同名文件或文件夹存在',
    -9: '链接错误，提取码错误',
    -10: '转存失败，容量不足',
    -12: '链接错误，提取码错误',
    -62: '转存失败，链接访问次数过多，请手动转存或稍后再试',
    0: '转存成功',
    2: '转存失败，目标目录不存在',
    4: '转存失败，目录中存在同名文件',
    12: '转存失败，转存文件数超过限制',
    20: '转存失败，容量不足',
    105: '链接错误，所访问的页面不存在',
    404: '转存失败，秒传无效',
}
# 标签、标题和提示信息等内容取值来源。主要是 UI 界面相关文字，不包含结果日志插入文字
LABEL_MAP = {
    'cookie': '1.请输入百度网盘主页完整 Cookies，不带引号：',
    'folder_name': '2.请输入转存目标或分享来源目录名（留空为根目录）：',
    'links': '3.请粘贴百度网盘分享链接，每行一个：',
    'links_tip': """百度网盘分享链接示例：
https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg
https://pan.baidu.com/s/1jeDvKgas8-xUss7BUFpifQ uftv 
https://pan.baidu.com/e/1X5j-baPwZHmcXioKQPxb_w rsyf
https://pan.baidu.com/s/1gFqh-WGW2LdNqKpHbwtZ9Q?pwd=1234
https://pan.baidu.com/s/1kO3Yp3Q-opIFuY7GRPtd2A 提取码：qm3h
https://pan.baidu.com/share/init?surl=7M-O0-SskRPdoZ0emZrd5w&pwd=1234
http://pan.baidu.com/s/1_evfkiTrEZvOkC2hb-NiKw ju9a
文件名 https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA fm9k""",
    'options': '4.选项设置',
    'logs': '5.运行日志：',
    'logs_tip': '显示运行结果或错误信息',
    'save': '批量转存',
    'share': '批量分享',
    'trust': '系统代理',
    'trust_tip': '应用系统代理访问百度网盘',
    'safe': '安全转存',
    'safe_tip': '每个链接资源保存在单独文件夹中',
    'check': '检测模式',
    'check_tip': '检查链接是否有效但不转存',
    'help': '使用帮助',
    'settings_title': '设置分享选项',
    'expiry_title': '设置分享期限：',
    'password_title': '自定义提取码：',
    'default_password': '1234',
    'ok': '确认',
    'cancel': '取消',
    'validate_title': '请重新输入',
    'validate_msg': '提取码必须是四位数字或字母的组合',
    'undo': '撤销    Ctrl+z',
    'redo': '重做    Ctrl+y',
    'cut': '剪切    Ctrl+x',
    'copy': '复制    Ctrl+c',
    'paste': '粘贴    Ctrl+v',
    'select_all': '全选    Ctrl+a',
    'clear': '删除    Delete',
}
