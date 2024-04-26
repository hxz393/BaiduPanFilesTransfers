"""
所有和网络请求相关函数。

:author: assassing
:contact: https://github.com/hxz393
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""
import time
from typing import Union, List, Any

import requests
from retrying import retry

from src.constants import HEADERS, BASE_URL


class Network:
    """
    网络请求相关类。
    注意，此类函数用 retry 来处理网络问题，达到重试次数则由主函数来捕获异常，中断运行。只要请求能返回数据，都可以正确处理。
    请求地址没有取全参数（params），只留关键参数。
    """

    def __init__(self):
        """
        初始化会话、请求头和 bdstoken。
        """
        self.s = requests.Session()
        self.headers = HEADERS
        self.bdstoken = ''
        # 忽略证书验证警告
        requests.packages.urllib3.disable_warnings()

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_bdstoken(self) -> Union[str, int]:
        """
        获取 bdstoken，用于创建、转存等操作，是所有其他请求的先决条件。
        获取到的 token 在整个会话中通用。

        :return: 获取成功返回 bdstoken，获取失败返回错误代码
        """
        url = f'{BASE_URL}/api/gettemplatevariable'
        params = {
            'clienttype': '0',
            'app_id': '38824127',
            'web': '1',
            'fields': '["bdstoken","token","uk","isdocuser","servertime"]'
        }

        r = self.s.get(
            url=url,
            params=params,
            headers=self.headers,
            timeout=10,
            allow_redirects=False,
            verify=False
        )

        if r.json()['errno'] != 0:
            return r.json()['errno']
        else:
            return r.json()['result']['bdstoken']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_dir_list(self, folder_name: str = '/') -> Union[List[Any], int]:
        """
        获取指定目录下的文件或目录列表。
        用于创建目录前，检查目录是否已存在；
        用于批量分享时，生成任务列表。

        :param folder_name: 指定要获取列表的目录名，不指定则为根目录
        :return: 获取成功时返回文件列表，获取失败时返回错误代码
        """
        url = f'{BASE_URL}/api/list'
        params = {
            'order': 'time',
            'desc': '1',
            'showempty': '0',
            'web': '1',
            'page': '1',
            'num': '1000',
            'dir': folder_name,
            'bdstoken': self.bdstoken
        }

        r = self.s.get(
            url=url,
            params=params,
            headers=self.headers,
            timeout=15,
            allow_redirects=False,
            verify=False
        )

        if r.json()['errno'] != 0:
            return r.json()['errno']
        else:
            return r.json()['list']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def create_dir(self, folder_name: str) -> int:
        """
        新建指定目录。
        用于批量转存前，建立缺失的目标目录。

        :param folder_name: 指定要建立的目录名
        :return: 获取请求返回的代码，成功时返回 0
        """
        url = f'{BASE_URL}/api/create'
        params = {
            'a': 'commit',
            'bdstoken': self.bdstoken
        }
        data = {
            'path': folder_name,
            # 建立目录时固定为 1
            'isdir': '1',
            # 没发现用途，总是为空
            'block_list': '[]',
        }

        r = self.s.post(
            url=url,
            params=params,
            headers=self.headers,
            data=data,
            timeout=15,
            allow_redirects=False,
            verify=False
        )

        return r.json()['errno']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def verify_pass_code(self,
                         link_url: str,
                         pass_code: str) -> Union[str, int]:
        """
        验证提取码是否正确。
        如果正确，则会返回转存所必须的 randsk 参数。

        :param link_url: 网盘地址
        :param pass_code: 提取码
        :return: 成功时返回 randsk 字符串，失败时返回错误代码
        """
        url = f'{BASE_URL}/share/verify'
        params = {
            # 可放心用暴力切片
            'surl': link_url[25:48],
            'bdstoken': self.bdstoken,
            # 当前时间的毫秒级时间戳
            't': str(int(round(time.time() * 1000))),
            # 下面是不明所以的固定参数
            'channel': 'chunlei',
            'web': '1',
            'clienttype': '0'
        }
        data = {
            'pwd': pass_code,
            # 并没有发现下面两个参数的用途
            'vcode': '',
            'vcode_str': ''
        }

        r = self.s.post(
            url=url,
            params=params,
            headers=self.headers,
            data=data,
            timeout=10,
            allow_redirects=False,
            verify=False
        )

        if r.json()['errno'] != 0:
            return r.json()['errno']
        else:
            return r.json()['randsk']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_transfer_params(self, url: str) -> str:
        """
        更新 bdclnd 到 cookie 后，再次请求网盘链接，获取响应内容。
        请求不再需要提取码。

        :param url: 网盘地址
        :return: 返回原始请求内容，丢给 parse_response 函数取处理
        """
        r = self.s.get(
            url=url,
            headers=self.headers,
            timeout=15,
            verify=False
        )

        return r.content.decode("utf-8")

    @retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
    def transfer_file(self,
                      params_list: List[str],
                      folder_name: str
                      ) -> int:
        """
        转存百度网盘文件。

        :param params_list: 带有 shareid、share_uk 和 fs_id 的列表
        :param folder_name: 转存目标目录
        :return: 返回转存请求结果代码
        """
        url = f'{BASE_URL}/share/transfer'
        params = {
            # shareid 是文件 id
            'shareid': params_list[0],
            # share_uk 猜是分享者的 id
            'from': params_list[1],
            'bdstoken': self.bdstoken,
            'channel': 'chunlei',
            'web': '1',
            'clienttype': '0'
        }
        data = {
            # 针对一个分享链接带有多个分享文件的情况，转换一下列表格式（暂没测试链接，不确定是否可以直传 f'[{params_list[2]}]'）
            'fsidlist': f'[{",".join(i for i in params_list[2])}]',
            # 目标目录为空，则直接等于根目录 '/'
            'path': f'/{folder_name}'
        }

        r = self.s.post(
            url=url,
            params=params,
            headers=self.headers,
            data=data,
            timeout=15,
            allow_redirects=False,
            verify=False
        )

        return r.json()['errno']

    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def create_share(self,
                     fs_id: int,
                     expiry: str,
                     password: str) -> Union[str, int]:
        """
        生成百度网盘分享链接。

        :param fs_id: 文件或目录独一无二的 id
        :param expiry: 自定义失效时长
        :param password: 自定义提取码
        :return: 成功时返回生成的分享链接，失败时返回错误代码
        """
        url = f'{BASE_URL}/share/set'
        params = {
            'channel': 'chunlei',
            'bdstoken': self.bdstoken,
            'clienttype': '0',
            'app_id': '250528',
            'web': '1'
        }
        data = {
            'period': expiry,
            'pwd': password,
            'eflag_disable': 'true',
            'channel_list': '[]',
            'schannel': '4',
            'fid_list': f'[{fs_id}]'
        }

        r = self.s.post(
            url=url,
            params=params,
            headers=self.headers,
            data=data,
            timeout=15,
            allow_redirects=False,
            verify=False
        )

        if r.json()['errno'] != 0:
            return r.json()['errno']
        else:
            return r.json()['link']
