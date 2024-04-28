"""
通用的工具函数，主要是一些静态函数。

:author: assassing
:contact: https://github.com/hxz393
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""
import atexit
import base64
import os
import re
import tempfile
import threading
import zlib
from typing import Any, Union, Tuple, Callable, List, Optional

from src.constants import CONFIG_PATH, ICON_BASE64

# 预编译正则表达式
SHARE_ID_REGEX = re.compile(r'"shareid":(\d+?),"')
USER_ID_REGEX = re.compile(r'"share_uk":"(\d+?),"')
FS_ID_REGEX = re.compile(r'"fs_id":(\d+?),"')


def thread_it(func: Callable,
              *args: Tuple[Any, ...]) -> None:
    """
    多线程防止转存时主界面卡死。

    :param func: 要调用的函数
    :param args: 函数参数
    :return: 无返回值
    """
    t = threading.Thread(target=func, args=args)
    t.start()


def write_config(config: str) -> None:
    """
    写入配置文件，点击批量转存或分享按钮时才运行。

    :param config: 配置文件内容，以换行转义字符 '\n' 拼接多个配置到一行字符串
    :return: 无返回值
    """
    with open(CONFIG_PATH, 'w') as f:
        f.write(config)


def read_config() -> Optional[List[str]]:
    """
    读取配置文件，在 UI 初始化完毕后执行。

    :return: 读取成功时返回配置列表，一个元素一个配置。配置文件不存在时返回 None，什么也不会发生
    """
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            config = f.read().splitlines()
            return config


def create_icon() -> str:
    """
    从 base64 编码中生成临时图标，在程序结束时自动删除。
    好处是打包时不用导入资源文件。

    :return: 返回图标文件路径
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ico') as temp_file:
        temp_file.write(zlib.decompress(base64.b64decode(ICON_BASE64)))

    ico_path = temp_file.name
    # 显式声明程序退出时，删除临时图标文件，避免在个别系统平台自动删除失败
    atexit.register(os.remove, ico_path)
    return ico_path


def normalize_link(url_code: str) -> str:
    """
    预处理链接至标准格式。

    :param url_code: 需要处理的的原始链接格式
    :return: 返回标准格式：链接+空格+提取码
    """
    # 升级旧链接格式
    normalized = url_code.replace("share/init?surl=", "s/1")
    # 替换掉 ?pwd= 或 &pwd= 为空格
    normalized = re.sub(r'[?&]pwd=', ' ', normalized)
    # 替换掉提取码字样为空格
    normalized = re.sub(r'提取码*[：:]', ' ', normalized)
    # 替换 http 为 https，顺便处理掉开头没用的文字
    normalized = re.sub(r'^.*?(https?://)', 'https://', normalized)
    # 替换连续的空格
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def parse_url_and_code(url_code: str) -> Optional[Tuple[str, str]]:
    """
    以空格分割出 URL 和提取码。

    :param url_code: 输入的标准链接格式
    :return: 链接和提取码
    """
    # 虽然不大可能分割失败，但还是处理一下
    parts = url_code.split(' ')
    if len(parts) < 2:
        return None

    url, passwd = parts[0].strip(), parts[1].strip()
    # 暴力切片，如果输入链接不是以提取码结尾，会得到错误提取码
    return url[:47], passwd[-4:]


def parse_response(response: str) -> Union[List[str], int]:
    """
    验证提取码通过后，再次访问网盘地址，此函数解析返回的页面源码并提取所需要参数。
    shareid_list 和 user_id_list 只有一个值，fs_id_list 需要完整返回

    :param response: 响应内容
    :return: 没有获取到足够参数时，返回错误代码-1；否则返回三个参数的列表
    """
    # 分享 id
    shareid_list = SHARE_ID_REGEX.findall(response)
    # 分享者 id
    user_id_list = USER_ID_REGEX.findall(response)
    # 分享文件列表
    fs_id_list = FS_ID_REGEX.findall(response)

    if not Any(shareid_list, user_id_list, fs_id_list):
        return -1
    else:
        share_id = shareid_list[0]
        user_id = user_id_list[0]
        reason = [share_id, user_id, fs_id_list]
        return reason
