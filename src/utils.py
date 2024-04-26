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
import sys
import tempfile
import threading
import time
import traceback
import webbrowser
import zlib
from typing import Any, Union, Tuple, Callable, List, Optional

import requests
import ttkbootstrap as ttk
from retrying import retry
from ttkbootstrap.dialogs import Messagebox

from src.constants import CONFIG_PATH, ICON_BASE64


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
            return f.read().splitlines()


def create_icon() -> str:
    """
    生成临时图标，在程序结束时自动删除。

    :return: 返回图标文件路径
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ico') as temp_file:
        temp_file.write(zlib.decompress(base64.b64decode(ICON_BASE64)))
    atexit.register(os.remove, temp_file.name)
    return temp_file.name


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
