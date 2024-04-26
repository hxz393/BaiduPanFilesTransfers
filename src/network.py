"""
和网络请求相关函数。

:author: assassing
:contact: https://github.com/hxz393
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""
import time
from typing import Union

import requests
from retrying import retry

from src.constants import *


class Network:
    """网络请求相关类"""

    def __init__(self):
        """初始化会话"""
        self.s = requests.Session()
        self.headers = HEADERS
        self.bdstoken = None

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_bdstoken(self) -> Union[str, int]:
        """获取 bdstoken"""
        url = f'{BASE_URL}/api/gettemplatevariable'
        params = {'clienttype': '0', 'app_id': '38824127', 'web': '1', 'fields': '["bdstoken","token","uk","isdocuser","servertime"]'}
        r = self.s.get(url=url, params=params, headers=self.headers, timeout=10, allow_redirects=False, verify=False)
        return r.json()['errno'] if r.json()['errno'] != 0 else r.json()['result']['bdstoken']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_dir_list(self, folder_name: str = '/') -> Union[list, int]:
        """获取用户网盘中目录列表"""
        url = f'{BASE_URL}/api/list'
        params = {'order': 'time', 'desc': '1', 'showempty': '0', 'web': '1', 'page': '1', 'num': '1000', 'dir': folder_name, 'bdstoken': self.bdstoken, }
        r = self.s.get(url=url, params=params, headers=self.headers, timeout=15, allow_redirects=False, verify=False)
        return r.json()['errno'] if r.json()['errno'] != 0 else r.json()['list']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def create_dir(self, folder_name: str) -> int:
        """新建目录"""
        url = f'{BASE_URL}/api/create'
        params = {'a': 'commit', 'bdstoken': self.bdstoken}
        data = {'path': folder_name, 'isdir': '1', 'block_list': '[]', }
        r = self.s.post(url=url, params=params, headers=self.headers, data=data, timeout=15, allow_redirects=False, verify=False)
        return r.json()['errno']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def verify_pass_code(self, link_url: str, pass_code: str) -> Union[str, int]:
        """验证提取码"""
        url = f'{BASE_URL}/share/verify'
        params = {'surl': link_url[25:48], 'bdstoken': self.bdstoken, 't': str(int(round(time.time() * 1000))), 'channel': 'chunlei', 'web': '1', 'clienttype': '0', }
        data = {'pwd': pass_code, 'vcode': '', 'vcode_str': '', }
        r = self.s.post(url=url, params=params, headers=self.headers, data=data, timeout=10, allow_redirects=False, verify=False)
        return r.json()['errno'] if r.json()['errno'] != 0 else r.json()['randsk']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def request_link(self, url: str) -> str:
        """请求网盘链接，获取响应"""
        r = self.s.get(url=url, headers=self.headers, timeout=15, verify=False)
        return r.content.decode("utf-8")

    @retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
    def transfer_file(self, verify_links_reason: list, folder_name: str) -> int:
        """转存文件"""
        url = f'{BASE_URL}/share/transfer'
        params = {'shareid': verify_links_reason[0], 'from': verify_links_reason[1], 'bdstoken': self.bdstoken, 'channel': 'chunlei', 'web': '1', 'clienttype': '0', }
        data = {'fsidlist': f'[{",".join(i for i in verify_links_reason[2])}]', 'path': f'/{folder_name}', }
        r = self.s.post(url=url, params=params, headers=self.headers, data=data, timeout=15, allow_redirects=False, verify=False)
        return r.json()['errno']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def create_share(self, fs_id: int, expiry: str, password: str) -> Union[str, int]:
        """生成分享链接"""
        url = f'{BASE_URL}/share/set'
        params = {'channel': 'chunlei', 'bdstoken': self.bdstoken, 'clienttype': '0', 'app_id': '250528', 'web': '1'}
        data = {'period': EXP_MAP[expiry], 'pwd': password, 'eflag_disable': 'true', 'channel_list': '[]', 'schannel': '4', 'fid_list': f'[{fs_id}]'}
        r = self.s.post(url=url, params=params, headers=self.headers, data=data, timeout=15, allow_redirects=False, verify=False)
        return r.json()['errno'] if r.json()['errno'] != 0 else r.json()['link']
