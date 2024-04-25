"""
打包命令：pyinstaller -F -w -i BaiduPanFilesTransfers.ico --hiddenimport=tkinter -n BaiduPanFilesTransfers BaiduPanFilesTransfers.py

:title: BaiduPanFilesTransfers
:site: https://github.com/hxz393/BaiduPanFilesTransfers
:author: assassing
:contact: hxz393@gmail.com
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
from typing import Any, Union, Tuple, Callable

import requests
import ttkbootstrap as ttk
from retrying import retry
from ttkbootstrap.dialogs import Messagebox

# 全局常量
BASE_URL = 'https://pan.baidu.com'
ERROR_CODES = {
    -1: '链接失效，没获取到 shareid',
    -2: '链接失效，没获取到 user_id',
    -3: '链接失效，没获取到 fs_id',
    -4: '转存失败，无效登录。请退出账号在其他地方的登录',
    -6: '转存失败，请用浏览器无痕模式获取 Cookie',
    -7: '转存失败，转存文件夹名有非法字符，不能包含 < > | * ? / :，请改正目录名后重试',
    -8: '转存失败，目录中已有同名文件或文件夹存在',
    -9: '链接错误，提取码错误',
    -10: '转存失败，容量不足',
    -62: '链接错误尝试次数过多，请手动转存或稍后再试',
    '百度网盘-链接不存在': '链接失效，文件已经被删除或取消分享',
    '百度网盘 请输入提取码': '链接错误，缺少提取码',
    0: '转存成功',
    4: '转存失败，目录中已有同名文件存在',
    12: '转存失败，转存文件数超过限制',
    20: '转存失败，容量不足',
    105: '链接错误，链接格式不正确',
    404: '转存失败，秒传无效',
}
EXP_MAP = {"1 天": 1, "7 天": 7, "30 天": 30, "永久": 0}
LABEL_MAP = {
    'cookie': '1.请输入百度网盘主页完整 Cookies，不带引号：',
    'folder_name': '2.请输入转存或分享目录名（留空为根目录）：',
    'links': '3.请粘贴百度网盘标准链接，每行一个：',
    'options': '4.选项设置',
    'logs': '5.运行结果：',
    'save': '批量转存',
    'share': '批量分享',
    'trust': '系统代理',
    'trust_tip': '应用系统代理访问百度网盘',
    'safe': '安全转存',
    'safe_tip': '每个链接资源保存在单独文件夹中',
    'check': '检测模式',
    'check_tip': '检查链接是否有效但不转存',
    'help': '使用帮助',
}
# noinspection LongLine
ICON_BASE64 = 'eJyFUw1MU1cUvjgyfa+vr++1WGw3FTKDtHVLQDPCtojLFlpKKY4pLE0EDAaEMuKyOBWmI8ZMZ5T6Ax2xpgKKCs5kGtT9KA5B/GFxAUpBES1TZ0Z0kWQZLMZ9O6+um1tIdl6+d+79vvPdd25eDmNR9EgSo3ccWx3NmJ4xlkggipinvBJLotn/RdQrsU16i9aXY5Z9HsonzNr9Jy06354F8r7cxJh6A2OImspoZq3PJ2rrckxab7dJ9k6YtJ9DgSWmHmZlLXsnTXJdz3xpr2vu3AMznvXOY7unWwyeNeX5bQ/ffesIEmQPFsZ5Ufn+t2htCqB2+xWkLzpAfA3Mes+jtxftr9y5s5uL9Byv2bLc/rrvl+vBMRS7WmCe9Rn83qu4cjGEuppOdJ0fQfeFEApyjuDYwV4MDYyNj49PrAQwbbZurXG2Zt3VLR+fppoRWOZUw/FmLYKB+7Cn7QFpSH15G3qv3cGDsV/xzZkBVBQfRklBY3+21RNnEN0uo1Qx2XLoMur3noNBLEd+bj2u9YRgiluHWLUbBk05mvydGA09wGtJ1cSVQa8ufawXi1fr1Ct9sZoifNFyCTu2nYROKET6ks0YvnEfmemfhvfz5rhxsXMIYz+P441Xq6AV8sOQVSuOSULueUnIQ13tKTT4z0JWv4cXZhXgxJeX8X3PTXz4gR8HG9sxGPwRP917CLt1E0TVsgh+UPPOCwKfjZLi3ejqCuBFowsC70RyUimOH+/E8PBddHT0ku7Bjet3YU1fDxWfFYbAZ/XxvP0QAcnJJQgEbiMjYz2UvYKYmHeQkJAPo3E5Fi9eQ2fdQ0qKm7SMMDguo43j7CU8b3ssSVnw+8/g6NF2zJy5lHTbv1BYSP+g9ybi410R7gmd8ZEo2l6i9ZDCpaa60d9/C2Vlu6BW2//2ajQONDR8hcbGr2mdGeFDKlXmAsY+maZSWSto/5sg2LFq1Q4MDIRQVLSd+l8KUcyE01mFwcFROBwb/vJaJ+nblYylhSdKp3Oqid9FmJAkB0pLPejrG0Fb2yU0N59FMDiKrVubIctOxfs7x9n2UR/yszOg1dpE0tbSGbep9ycpKWXYuNGPmppW5OVtpl6y/yD9Dumb/uv9J9KilTtRTRWh/ekdbaOUOzjOWk05KdJzJELTGfvuOcaqp5zqqUOpVTyK90+HRLty'
MW_PADDING = (10, 0)
MAIN_TITLE = 'BaiduPanFilesTransfers'
MAIN_VERSION = '2.6.1'
CONFIG_PATH = 'config.ini'
DELAY_SECONDS = 0.1

# 忽略证书验证警告
requests.packages.urllib3.disable_warnings()


class BaiduPanFilesTransfers:
    """本程序旨在提供一个简单 GUI 界面，用于批量转存、分享、检查百度网盘链接。尽可能地压缩代码"""

    def __init__(self):
        """初始化 UI 元素"""
        self.setup_window()
        self.setup_ui()
        self.init_session()
        self.read_config()

    def setup_window(self) -> None:
        """主窗口配置"""
        self.root = ttk.Window()
        self.root.style.theme_use('yeti')
        self.root.iconbitmap(temp_file.name)
        self.root.title(f"{MAIN_TITLE} {MAIN_VERSION}")
        self.root.update_idletasks()
        self.root.grid_columnconfigure(0, weight=1)
        self.root.place_window_center()

    def setup_ui(self) -> None:
        """定义窗口元素和元素布局"""
        init_row = 1
        # Cookie 标签和输入框
        self.entry_cookie = self.create_entry(init_row, LABEL_MAP['cookie'])
        # 目标路径标签和输入框
        self.entry_folder_name = self.create_entry(init_row + 2, LABEL_MAP['folder_name'])
        # 链接标签和输入框
        self.text_links = self.create_text(init_row + 4, LABEL_MAP['links'])
        # 结果标签和日志框
        self.text_logs = self.create_text(init_row + 7, LABEL_MAP['logs'])
        # 创建选项容器
        self.frame_options = ttk.LabelFrame(self.root, text=LABEL_MAP['options'], padding="10 10 0 9")
        self.frame_options.grid(row=init_row + 6, sticky='w', padx=MW_PADDING)
        self.var_trust_env = self.create_checkbutton(LABEL_MAP['trust'], LABEL_MAP['trust_tip'], 0)
        self.var_safe_mode = self.create_checkbutton(LABEL_MAP['safe'], LABEL_MAP['safe_tip'], 1)
        self.var_check_mode = self.create_checkbutton(LABEL_MAP['check'], LABEL_MAP['check_tip'], 2)
        # 创建按钮容器
        self.frame_bottom = ttk.Frame(self.root)
        self.frame_bottom.grid(row=init_row + 6, sticky='e', padx=MW_PADDING)
        self.bottom_save = self.create_button(LABEL_MAP['save'], self.save, 1)
        self.bottom_share = self.create_button(LABEL_MAP['share'], self.share, 0)
        # 状态标签
        # noinspection PyArgumentList
        self.label_status = ttk.Label(self.root, text=LABEL_MAP['help'], font=('', 10, 'underline'), bootstyle='primary', cursor='heart')
        self.label_status.grid(row=init_row + 7, sticky='e', padx=MW_PADDING, pady=MW_PADDING)
        self.label_status.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/hxz393/BaiduPanFilesTransfers"))

    def create_entry(self, row: int, label_text: str) -> ttk.Entry:
        """建立标签和输入框函数"""
        ttk.Label(self.root, text=label_text).grid(row=row, sticky='w', padx=MW_PADDING, pady=MW_PADDING)
        entry = ttk.Entry(self.root)
        entry.grid(row=row + 1, sticky='we', padx=MW_PADDING, pady=MW_PADDING)
        return entry

    def create_text(self, row: int, label_text: str) -> ttk.Text:
        """建立标签、文本框和滚动条"""
        ttk.Label(self.root, text=label_text).grid(row=row, column=0, sticky='w', padx=MW_PADDING, pady=MW_PADDING)
        text = ttk.Text(self.root, undo=True, font=("", 10), wrap='none', height=10)
        text.grid(row=row + 1, column=0, sticky='wens', padx=MW_PADDING, pady=(10, 10))
        scrollbar = ttk.Scrollbar(self.root)
        scrollbar.grid(row=row + 1, column=1, sticky='sn', rowspan=1)
        scrollbar.config(command=text.yview)
        text.config(yscrollcommand=scrollbar.set)
        self.root.grid_rowconfigure(row + 1, weight=1)
        return text

    def create_checkbutton(self, text: str, tooltip: str, column: int) -> ttk.BooleanVar:
        """创建设置复选框"""
        var = ttk.BooleanVar()
        checkbutton = ttk.Checkbutton(self.frame_options, text=text, variable=var)
        checkbutton.grid(row=0, column=column, padx=(0, 10))
        ToolTip(checkbutton, tooltip)
        return var

    def create_button(self, text: str, command: Callable, column: int) -> ttk.Button:
        """创建功能按钮"""
        button = ttk.Button(self.frame_bottom, text=text, width=10, padding="17 17 17 17", command=lambda: self.thread_it(command))
        button.grid(row=0, column=column, padx=MW_PADDING)
        return button

    def init_session(self) -> None:
        """初始化会话"""
        self.s = requests.Session()
        self.bdstoken = None
        self.headers = {
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

    def read_config(self) -> None:
        """读取配置文件，并填入输入框"""
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                config_list = f.read().splitlines()
            self.entry_cookie.insert(0, config_list[0].strip() if config_list else '')
            self.entry_folder_name.insert(0, config_list[1].strip() if len(config_list) > 1 else '')

    @staticmethod
    def write_config(config: str) -> None:
        """写入配置文件"""
        with open(CONFIG_PATH, 'w') as f:
            f.write(config)

    @staticmethod
    def thread_it(func: Any, *args: Any) -> None:
        """多线程防止主界面卡死"""
        t = threading.Thread(target=func, args=args)
        t.start()

    # noinspection PyArgumentList
    def change_status(self, status: str) -> None:
        """运行状态变化更新函数"""
        if status == 'running':
            self.running = True
            self.bottom_save.config(text='点击暂停', bootstyle='danger', command=lambda: self.change_status('paused'))
        elif status == 'paused':
            self.running = False
            self.bottom_save.config(text='点击继续', bootstyle='success', command=lambda: self.change_status('running'))
        elif status == 'init':
            self.label_status.config(text='准备就绪！', font=('', 10), bootstyle='primary', cursor="arrow")
            self.label_status.unbind("<Button-1>")
            self.bottom_share.config(state="disabled")
            self.text_logs.delete(1.0, ttk.END)
        elif status == 'update':
            self.completed_task_count += 1
            self.label_status.config(text=f'总进度：{self.completed_task_count}/{self.total_task_count}', bootstyle='success')
        elif status == 'sharing':
            self.text_links.delete(1.0, ttk.END)
            self.bottom_save.config(state="disabled")
        elif status == 'error':
            self.label_status.config(text='发生错误：', bootstyle='danger')
        else:
            self.running = False
            self.bottom_save.config(text='批量转存', state="normal", bootstyle='primary', command=lambda: self.thread_it(self.save, ))
            self.bottom_share.config(state="normal")

    @staticmethod
    def normalize_link(url_code: str) -> str:
        """预处理链接至标准格式：链接+空格+提取码"""
        normalized = url_code.replace("share/init?surl=", "s/1").replace("?pwd=", " ")
        normalized = re.sub(r'^.*?(https?://)', 'https://', normalized)
        return normalized

    def check_condition(self, condition: bool, message: str) -> None:
        """输入或返回检查，如果条件 condition 为 True，则直接终止流程。用于主函数。单个链接处理出错直接调用 insert_logs 函数，不中断运行"""
        if condition:
            self.change_status('error')
            self.insert_logs(message)
            sys.exit()

    def insert_logs(self, message: str, is_alt: bool = False) -> None:
        """在文本框末尾插入内容"""
        self.text_links.insert('end', f'{message}\n') if is_alt else self.text_logs.insert('end', f'{message}\n')

    def update_cookie(self, bdclnd: str) -> None:
        """更新 cookie，用于处理带提取码链接。每次请求都会生成新的 bdclnd，需要更新到 cookie 中"""
        cookies_dict = dict(map(lambda item: item.split('=', 1), filter(None, self.headers['Cookie'].split(';'))))
        cookies_dict['BDCLND'] = bdclnd
        self.headers['Cookie'] = ';'.join([f'{key}={value}' for key, value in cookies_dict.items()])

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
    def create_share(self, fs_id: int) -> Union[str, int]:
        """生成分享链接"""
        url = f'{BASE_URL}/share/set'
        params = {'channel': 'chunlei', 'bdstoken': self.bdstoken, 'clienttype': '0', 'app_id': '250528', 'web': '1'}
        data = {'period': EXP_MAP[self.expiry], 'pwd': self.password, 'eflag_disable': 'true', 'channel_list': '[]', 'schannel': '4', 'fid_list': f'[{fs_id}]'}
        r = self.s.post(url=url, params=params, headers=self.headers, data=data, timeout=15, allow_redirects=False, verify=False)
        return r.json()['errno'] if r.json()['errno'] != 0 else r.json()['link']

    @staticmethod
    def parse_response(response: str) -> Union[list, str, int]:
        """解析响应内容并提取数据"""
        shareid_list = re.findall(r'"shareid":(\d+?),"', response)
        user_id_list = re.findall(r'"share_uk":"(\d+?)","', response)
        fs_id_list = re.findall(r'"fs_id":(\d+?),"', response)
        info_title_list = re.findall(r'<title>(.+)</title>', response)

        # 返回包含三个参数的列表，或者错误代码
        if not shareid_list:
            return -1
        elif not user_id_list:
            return -2
        elif not fs_id_list:
            return info_title_list[0] if info_title_list else -3
        else:
            return [shareid_list[0], user_id_list[0], fs_id_list]

    @staticmethod
    def parse_url_and_code(url_code: str) -> Tuple[str, str]:
        """解析 URL 和提取码"""
        url, passwd = re.sub(r'提取码*[：:](.*)', r'\1', url_code).split(' ', maxsplit=1)
        return url.strip()[:47], passwd.strip()[-4:]

    def verify_link(self, link_url: str, pass_code: str) -> Union[list, str, int]:
        """验证链接有效性，验证通过返回转存所需参数列表"""
        # 对于有提取码的链接先验证提取码，试图获取更新 bdclnd。如果返回的 bdclnd 是数字错误代码，直接中断
        if pass_code:
            bdclnd_or_err = self.verify_pass_code(link_url, pass_code)
            if isinstance(bdclnd_or_err, int):
                return bdclnd_or_err
            self.update_cookie(bdclnd_or_err)
        # 请求网盘链接，获取转存必须的 3 个参数
        return self.parse_response(self.request_link(link_url))

    def process_link(self, url_code: str, folder_name: str) -> None:
        """验证和转存链接，输出最终结果"""
        # 检查链接有效性
        reason = self.verify_link(*self.parse_url_and_code(url_code))
        # 如果开启检查模式，插入检查结果，然后结束
        if self.check_mode:
            self.insert_logs(f'链接有效：{url_code}') if isinstance(reason, list) else self.insert_logs(f'链接无效：{url_code} 原因：{ERROR_CODES.get(reason, reason)}')
            return
        # 返回结果为列表时，执行转存文件，输出转存链接结果；否则跳过转存，输出检查链接结果
        if isinstance(reason, list):
            # 如果开启安全转存模式，对每个转存链接建立目录
            if self.safe_mode:
                folder_name = f'{folder_name}/{self.completed_task_count}'
                self.create_dir(folder_name)
            reason = self.transfer_file(reason, folder_name)
        # 展示结果
        self.insert_logs(f'{ERROR_CODES[reason]}：{url_code}' if reason in ERROR_CODES else f'转存失败，错误代码（{reason}）：{url_code}')

    def pause_detection(self, url_code: str) -> None:
        """加入暂停检测逻辑，并插入等待时间"""
        while not self.running:
            time.sleep(DELAY_SECONDS * 10)
        self.process_link(url_code, self.folder_name)
        time.sleep(DELAY_SECONDS)

    def prepare_run(self) -> None:
        """获取变量，准备运行。转存和分享共用逻辑"""
        self.cookie = "".join(self.entry_cookie.get().split())
        self.folder_name = "".join(self.entry_folder_name.get().split())
        self.headers['Cookie'] = self.cookie
        self.s.trust_env = self.var_trust_env.get()
        self.safe_mode = self.var_safe_mode.get()
        self.check_mode = self.var_check_mode.get()
        self.completed_task_count = 0
        self.change_status('init')
        self.write_config(f'{self.cookie}\n{self.folder_name}')

    def setup_save(self) -> None:
        """准备转存，初始化界面"""
        self.link_list = list(dict.fromkeys([self.normalize_link(f'{link} ') for link in self.text_links.get(1.0, ttk.END).split('\n') if link]))
        self.total_task_count = len(self.link_list)
        self.change_status('running')

    def setup_share(self) -> None:
        """准备分享，初始化界面"""
        self.expiry, self.password = self.dialog_result.result
        self.total_task_count = len(self.dir_list_all)
        self.change_status('sharing')

    def handle_input(self) -> None:
        """输入检查，如链接数限制和 cookie 格式"""
        self.check_condition(self.total_task_count == 0, '无有效链接。')
        self.check_condition(self.total_task_count > 1000, f'转存链接数一次不能超过 1000，请减少链接数。当前连接数：{self.total_task_count}')
        self.check_condition(not self.cookie.isascii() or self.cookie.find('BAIDUID') == -1, '百度网盘 cookie 输入不正确，请检查 cookie 后重试。')

    def handle_bdstoken(self) -> None:
        """获取 bdstoken 相关逻辑"""
        self.bdstoken = self.get_bdstoken()
        self.check_condition(isinstance(self.bdstoken, int), f'没获取到 bdstoken，错误代码：{self.bdstoken}')

    def handle_create_dir(self) -> None:
        """新建目录。如果目录已存在则不新建，否则会建立一个带时间戳的目录"""
        if self.folder_name and self.folder_name not in [dir_json['server_filename'] for dir_json in self.get_dir_list()]:
            self.check_condition(self.create_dir(self.folder_name) != 0, '转存目录名带非法字符，请改正目录名后重试。')

    def handle_list_dir(self) -> None:
        """获取目标目录下的文件和目录列表。如果返回的是数字，代表没有获取到文件列表"""
        self.dir_list_all = self.get_dir_list(folder_name=f'/{self.folder_name}')
        self.check_condition(isinstance(self.dir_list_all, int) or not self.dir_list_all, f'{self.folder_name} 中，没获取到任何要分享的文件或目录。')

    def handle_process_save(self) -> None:
        """执行批量转存"""
        for url_code in self.link_list:
            self.insert_logs(f'不支持的链接：{url_code}') if not url_code.startswith('https://pan.baidu.com/') else self.pause_detection(url_code)
            self.change_status('update')

    def handle_process_share(self) -> None:
        """执行批量分享"""
        for info in self.dir_list_all:
            is_dir = "/" if info["isdir"] == 1 else ""
            filename = f"{info['server_filename']}{is_dir}"
            share_link = self.create_share(info['fs_id'])
            self.insert_logs(f'目录：{filename}' if is_dir else f'文件：{filename}', is_alt=True)
            self.insert_logs(f'分享成功：{share_link}?pwd={self.password}，名称：{filename}' if isinstance(share_link, str) else f'分享失败：错误代码（{share_link}），文件名：{filename}')
            self.change_status('update')

    def save(self) -> None:
        """转存主函数"""
        try:
            self.prepare_run()
            self.setup_save()
            self.handle_input()
            self.handle_bdstoken()
            self.handle_create_dir()
            self.handle_process_save()
        except Exception as e:
            self.insert_logs(f'运行出错，错误信息如下：\n{e}\n{traceback.format_exc()}')
            self.change_status('error')
        finally:
            self.s.close()
            self.change_status('stopped')

    def share(self) -> None:
        """分享主函数"""
        try:
            # 创建对话框实例，如果对话框没有返回输入值，则忽略
            self.dialog_result = CustomDialog(self.root)
            if self.dialog_result.result:
                self.prepare_run()
                self.handle_bdstoken()
                self.handle_list_dir()
                self.setup_share()
                self.handle_process_share()
        except Exception as e:
            self.insert_logs(f'运行出错，错误信息如下：\n{e}\n{traceback.format_exc()}')
            self.change_status('error')
        finally:
            self.s.close()
            self.change_status('stopped')

    def run(self) -> None:
        """运行程序"""
        self.root.mainloop()


class CustomDialog(ttk.Toplevel):
    """弹出对话框，用于设置分享链接参数"""

    def __init__(self, parent):
        super().__init__(parent)
        self.style.theme_use('yeti')
        self.place_window_center()
        self.title("设置分享选项")
        self.iconbitmap(temp_file.name)
        self.resizable(width=False, height=False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.create_widgets()
        self.wait_window(self)

    # noinspection PyArgumentList
    def create_widgets(self) -> None:
        """创建控件元素"""
        master = ttk.Frame(self)
        master.pack(padx=10, pady=10, fill="both", expand=True)
        # 有效期下拉选择框
        self.var_expiry = ttk.StringVar(self, value="永久")
        ttk.Label(master, text="设置分享期限：").grid(row=0, column=0, sticky='e')
        ttk.Combobox(master, textvariable=self.var_expiry, values=list(EXP_MAP.keys()), state="readonly", bootstyle='primary').grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        # 提取码输入框
        self.var_password = ttk.StringVar(self, value="1234")
        ttk.Label(master, text="自定义提取码：").grid(row=1, column=0, sticky='e')
        ttk.Entry(master, textvariable=self.var_password, bootstyle="info").grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        # 在两个 frame 之间插入分割线
        ttk.Separator(self, orient='horizontal').pack(fill="x")
        # 底部按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text="确认", command=self.validate, bootstyle='primary').pack(side='right', padx=5)
        ttk.Button(button_frame, text="取消", command=self.destroy, bootstyle='danger').pack(side='right', padx=5)

    def validate(self) -> bool:
        """验证输入提取码有效性"""
        if not re.match("^[a-zA-Z0-9]{4}$", self.var_password.get()):
            Messagebox.show_warning(title="请重新输入", message="提取码必须是四位数字或字母的组合", master=self)
            return False
        self.result = (self.var_expiry.get(), self.var_password.get())
        self.destroy()
        return True


class ToolTip(object):
    """手动实现提示气泡"""

    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tips = None
        self.tooltip_id = None
        self.x = self.y = 0
        self.binding()

    def binding(self) -> None:
        """配置鼠标绑定事件"""
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)

    def enter(self, _: object = None) -> None:
        """鼠标进入事件"""
        self.schedule()

    def leave(self, _: object = None) -> None:
        """鼠标离开事件"""
        self.unschedule()
        self.hide()

    def schedule(self) -> None:
        """设置定时器"""
        self.unschedule()
        self.tooltip_id = self.widget.after(100, self.show)

    def unschedule(self) -> None:
        """取消定时器"""
        if self.tooltip_id:
            self.widget.after_cancel(self.tooltip_id)
            self.tooltip_id = None

    def show(self) -> None:
        """显示气泡提示"""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() - 25
        # 创建一个悬浮窗口
        self.tips = tw = ttk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(tw, text=self.text, background="#ffffe0", relief='solid', borderwidth=1)
        label.pack(ipadx=1)

    def hide(self) -> None:
        """隐藏气泡提示"""
        if self.tips:
            self.tips.destroy()
            self.tips = None


if __name__ == '__main__':
    # 生成图标
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ico') as temp_file:
        temp_file.write(zlib.decompress(base64.b64decode(ICON_BASE64)))
    atexit.register(os.remove, temp_file.name)
    BaiduPanFilesTransfers().run()
