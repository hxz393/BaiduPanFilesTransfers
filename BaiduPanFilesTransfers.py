"""
打包命令：pyinstaller -F -w -i BaiduPanFilesTransfers.ico -n BaiduPanFilesTransfers BaiduPanFilesTransfers.py

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
from typing import Any, Union, Tuple

import requests
import ttkbootstrap as ttk
from retrying import retry

requests.packages.urllib3.disable_warnings()

# 全局变量
BASE_URL = 'https://pan.baidu.com'
ERROR_CODES = {
    -1: '链接失效，没获取到 shareid',
    -2: '链接失效，没获取到 user_id',
    -3: '链接失效，没获取到 fs_id',
    -4: '转存失败，无效登录。请退出账号在其他地方的登录',
    -6: '转存失败，请用浏览器无痕模式获取 Cookie',
    -7: '转存失败，转存文件夹名有非法字符，请改正目录名后重试',
    -8: '转存失败，目录中已有同名文件或文件夹存在',
    -9: '链接错误，提取码错误或分享已过期',
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
# noinspection LongLine
ICON_BASE64 = 'eJyFUw1MU1cUvjgyfa+vr++1WGw3FTKDtHVLQDPCtojLFlpKKY4pLE0EDAaEMuKyOBWmI8ZMZ5T6Ax2xpgKKCs5kGtT9KA5B/GFxAUpBES1TZ0Z0kWQZLMZ9O6+um1tIdl6+d+79vvPdd25eDmNR9EgSo3ccWx3NmJ4xlkggipinvBJLotn/RdQrsU16i9aXY5Z9HsonzNr9Jy06354F8r7cxJh6A2OImspoZq3PJ2rrckxab7dJ9k6YtJ9DgSWmHmZlLXsnTXJdz3xpr2vu3AMznvXOY7unWwyeNeX5bQ/ffesIEmQPFsZ5Ufn+t2htCqB2+xWkLzpAfA3Mes+jtxftr9y5s5uL9Byv2bLc/rrvl+vBMRS7WmCe9Rn83qu4cjGEuppOdJ0fQfeFEApyjuDYwV4MDYyNj49PrAQwbbZurXG2Zt3VLR+fppoRWOZUw/FmLYKB+7Cn7QFpSH15G3qv3cGDsV/xzZkBVBQfRklBY3+21RNnEN0uo1Qx2XLoMur3noNBLEd+bj2u9YRgiluHWLUbBk05mvydGA09wGtJ1cSVQa8ufawXi1fr1Ct9sZoifNFyCTu2nYROKET6ks0YvnEfmemfhvfz5rhxsXMIYz+P441Xq6AV8sOQVSuOSULueUnIQ13tKTT4z0JWv4cXZhXgxJeX8X3PTXz4gR8HG9sxGPwRP917CLt1E0TVsgh+UPPOCwKfjZLi3ejqCuBFowsC70RyUimOH+/E8PBddHT0ku7Bjet3YU1fDxWfFYbAZ/XxvP0QAcnJJQgEbiMjYz2UvYKYmHeQkJAPo3E5Fi9eQ2fdQ0qKm7SMMDguo43j7CU8b3ssSVnw+8/g6NF2zJy5lHTbv1BYSP+g9ybi410R7gmd8ZEo2l6i9ZDCpaa60d9/C2Vlu6BW2//2ajQONDR8hcbGr2mdGeFDKlXmAsY+maZSWSto/5sg2LFq1Q4MDIRQVLSd+l8KUcyE01mFwcFROBwb/vJaJ+nblYylhSdKp3Oqid9FmJAkB0pLPejrG0Fb2yU0N59FMDiKrVubIctOxfs7x9n2UR/yszOg1dpE0tbSGbep9ycpKWXYuNGPmppW5OVtpl6y/yD9Dumb/uv9J9KilTtRTRWh/ekdbaOUOzjOWk05KdJzJELTGfvuOcaqp5zqqUOpVTyK90+HRLty'
APP_WIDTH = 480
APP_HEIGHT = 480
MAIN_TITLE = 'BaiduPanFilesTransfers'
MAIN_VERSION = '2.6.0'
CONFIG_PATH = 'config.ini'
DELAY_SECONDS = 0.1
PADDING = (10, 0)


class BaiduPanFilesTransfers:
    """
    本程序旨在提供一个简单 GUI 界面，用于批量转存百度网盘文件。尽可能地压缩代码。
    """

    def __init__(self):
        """初始化 UI 元素"""
        self.setup_window()
        self.setup_ui()
        self.init_session()
        self.read_config()

    def setup_window(self) -> None:
        """主窗口配置"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ico') as temp_file:
            temp_file.write(zlib.decompress(base64.b64decode(ICON_BASE64)))
        atexit.register(os.remove, temp_file.name)
        self.root = ttk.Window()
        self.root.iconbitmap(temp_file.name)
        self.root.title(f"{MAIN_TITLE} {MAIN_VERSION}")
        self.root.geometry(f'{APP_WIDTH}x{APP_HEIGHT}')
        self.root.minsize(APP_WIDTH, APP_HEIGHT)
        self.root.style.theme_use('yeti')

    def setup_ui(self) -> None:
        """定义窗口元素和元素布局"""
        self.init_row = 1
        # Cookie 标签和输入框
        self.entry_cookie = self.create_label_entry(self.init_row, '1.下面填入百度网盘 Cookies，不带引号：')
        # 保存文件夹名称标签和输入框
        self.entry_folder_name = self.create_label_entry(self.init_row + 2, '2.下面填入文件保存位置（默认根目录），不能包含<,>,|,*,?,,/：')
        # 链接标签和输入框
        ttk.Label(self.root, text='3.下面粘贴链接，每行一个。格式为：链接 提取码 或 链接（无提取码）').grid(row=self.init_row + 4, sticky=ttk.W, padx=PADDING, pady=PADDING)
        self.text_links = self.create_text_scrollbar(self.init_row + 5)
        # 创建一个 Frame 作为容器，存放按钮一行
        self.frame = ttk.Frame(self.root)
        self.frame.grid(row=self.init_row + 6, pady=PADDING, sticky=ttk.W, padx=PADDING)
        # 批量转存按钮
        self.bottom_save = ttk.Button(self.frame, text='批量转存', command=lambda: self.thread_it(self.main, ), width=10)
        self.bottom_save.grid(row=0, column=0, padx=(0, 5))
        # 批量分享按钮
        self.bottom_share = ttk.Button(self.frame, text='批量分享', command=lambda: self.thread_it(self.main, ), width=10)
        self.bottom_share.grid(row=0, column=1, padx=(0, 5))
        # 系统代理复选框
        self.var_trust_env = ttk.BooleanVar()
        self.checkbutton_trust_env = ttk.Checkbutton(self.frame, text='系统代理', variable=self.var_trust_env)
        self.checkbutton_trust_env.grid(row=0, column=2, padx=(0, 5))
        # 安全转存复选框
        self.var_safe_mode = ttk.BooleanVar()
        self.checkbutton_safe_mode = ttk.Checkbutton(self.frame, text='安全转存', variable=self.var_safe_mode)
        self.checkbutton_safe_mode.grid(row=0, column=3)
        # 状态标签
        # noinspection PyArgumentList
        self.label_status = ttk.Label(self.root, text='使用帮助', font=('', 10, 'underline'), bootstyle='primary', cursor='heart')
        self.label_status.grid(row=self.init_row + 6, sticky=ttk.E, padx=PADDING, pady=PADDING)
        self.label_status.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/hxz393/BaiduPanFilesTransfers"))
        # 结果文本框
        self.text_logs = self.create_text_scrollbar(self.init_row + 7)
        # 创建一个空的 Frame
        self.frame_empty = ttk.Frame(self.root)
        self.frame_empty.grid(row=self.init_row + 8, pady=PADDING, sticky=ttk.W, padx=PADDING)

    def create_label_entry(self, row: int, label_text: str) -> ttk.Entry:
        """建立标签和输入框函数"""
        ttk.Label(self.root, text=label_text).grid(row=row, column=0, sticky=ttk.W, padx=PADDING, pady=PADDING)
        entry = ttk.Entry(self.root)
        entry.grid(row=row + 1, column=0, sticky=ttk.W + ttk.E, padx=PADDING, pady=PADDING)
        self.root.grid_columnconfigure(0, weight=1)
        return entry

    def create_text_scrollbar(self, row: int) -> ttk.Text:
        """建立文本框和滚动条"""
        text = ttk.Text(self.root, height=5, wrap=ttk.NONE)
        text.grid(row=row, column=0, sticky=ttk.W + ttk.E + ttk.N + ttk.S, padx=PADDING, pady=PADDING)
        scrollbar = ttk.Scrollbar(self.root)
        scrollbar.grid(row=row, column=1, sticky=ttk.S + ttk.N, rowspan=1)
        scrollbar.config(command=text.yview)
        text.config(yscrollcommand=scrollbar.set)
        self.root.grid_rowconfigure(row, weight=1)
        return text

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
                config_list = f.readlines()
            self.entry_cookie.insert(0, config_list[0] if config_list else '')
            self.entry_folder_name.insert(0, config_list[1] if len(config_list) > 1 else '')

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
            self.bottom_save.configure(text='点击暂停', bootstyle='danger', command=lambda: self.change_status('paused'))
        elif status == 'paused':
            self.running = False
            self.bottom_save.configure(text='点击继续', bootstyle='success', command=lambda: self.change_status('running'))
        elif status == 'init':
            self.label_status.configure(font=('', 10), bootstyle='success', cursor="arrow")
            self.label_status.unbind("<Button-1>")
            self.bottom_share.configure(state="disabled")
            self.text_logs.delete(1.0, ttk.END)
        elif status == 'update':
            self.label_status.configure(text=f'转存进度：{self.completed_task_count}/{self.total_task_count}')
        elif status == 'error':
            self.label_status.configure(text='发生错误：', bootstyle='danger')
        else:
            self.running = False
            self.bottom_save.configure(text='批量转存', bootstyle='primary', command=lambda: self.thread_it(self.main, ))
            self.bottom_share.configure(state="normal")

    @staticmethod
    def sanitize_link(url_code: str) -> str:
        """预处理链接格式，整理成标准格式。例如 http 转为 https，去除提取码，去除链接中的空格等"""
        return url_code.replace("http://", "https://").replace("?pwd=", " ").replace("&pwd=", " ").replace("share/init?surl=", "s/1").lstrip()

    def check_condition(self, condition: bool, message: str) -> None:
        """输入或返回检查，如果条件 condition 为 True，则直接终止流程。用于主函数。单个链接处理出错直接调用 insert_logs 函数，不中断运行"""
        if condition:
            self.change_status('error')
            self.insert_logs(message)
            sys.exit()

    def insert_logs(self, message: str) -> None:
        """在结果文本框末尾插入内容"""
        self.text_logs.insert(ttk.END, f'{message}\n')

    def update_cookie(self, bdclnd: str) -> None:
        """更新 cookie，用于处理带提取码链接。每次请求都会生成新的 bdclnd，需要更新到 cookie 中"""
        if 'BDCLND=' in self.headers['Cookie']:
            self.headers['Cookie'] = re.sub(r'BDCLND=(\S+);?', f'BDCLND={bdclnd};', self.headers['Cookie'])
        else:
            self.headers['Cookie'] += f';BDCLND={bdclnd}'

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

    @retry(stop_max_attempt_number=3, wait_fixed=1000)
    def get_bdstoken(self) -> Union[str, int]:
        """获取 bdstoken"""
        url = f'{BASE_URL}/api/gettemplatevariable'
        params = {'clienttype': '0', 'app_id': '38824127', 'web': '1', 'fields': '["bdstoken","token","uk","isdocuser","servertime"]'}
        r = self.s.get(url=url, params=params, headers=self.headers, timeout=20, allow_redirects=False, verify=False)
        return r.json()['errno'] if r.json()['errno'] != 0 else r.json()['result']['bdstoken']

    @retry(stop_max_attempt_number=3, wait_fixed=1000)
    def get_dir_list(self) -> Union[list, int]:
        """获取用户网盘中目录列表"""
        url = f'{BASE_URL}/api/list'
        params = {'order': 'time', 'desc': '1', 'showempty': '0', 'web': '1', 'page': '1', 'num': '1000', 'dir': '/', 'bdstoken': self.bdstoken, }
        r = self.s.get(url=url, params=params, headers=self.headers, timeout=15, allow_redirects=False, verify=False)
        return r.json()['errno'] if r.json()['errno'] != 0 else r.json()['list']

    @retry(stop_max_attempt_number=3, wait_fixed=1000)
    def create_dir(self, folder_name: str) -> int:
        """新建目录"""
        url = f'{BASE_URL}/api/create'
        params = {'a': 'commit', 'bdstoken': self.bdstoken}
        data = {'path': folder_name, 'isdir': '1', 'block_list': '[]', }
        r = self.s.post(url=url, params=params, headers=self.headers, data=data, timeout=15, allow_redirects=False, verify=False)
        return r.json()['errno']

    @retry(stop_max_attempt_number=3, wait_fixed=1489)
    def verify_pass_code(self, link_url: str, pass_code: str) -> Union[str, int]:
        """验证提取码"""
        url = f'{BASE_URL}/share/verify'
        params = {'surl': link_url[25:48], 'bdstoken': self.bdstoken, 't': str(int(round(time.time() * 1000))), 'channel': 'chunlei', 'web': '1', 'clienttype': '0', }
        data = {'pwd': pass_code, 'vcode': '', 'vcode_str': '', }
        r = self.s.post(url=url, params=params, headers=self.headers, data=data, timeout=10, allow_redirects=False, verify=False)
        return r.json()['errno'] if r.json()['errno'] != 0 else r.json()['randsk']

    @retry(stop_max_attempt_number=3, wait_fixed=1100)
    def request_link(self, url: str) -> str:
        """请求网盘链接，获取响应"""
        r = self.s.get(url=url, headers=self.headers, timeout=15, verify=False)
        return r.content.decode("utf-8")

    @retry(stop_max_attempt_number=5, wait_fixed=1351)
    def transfer_file(self, verify_links_reason: list, folder_name: str) -> int:
        """转存文件"""
        url = f'{BASE_URL}/share/transfer'
        params = {'shareid': verify_links_reason[0], 'from': verify_links_reason[1], 'bdstoken': self.bdstoken, 'channel': 'chunlei', 'web': '1', 'clienttype': '0', }
        data = {'fsidlist': f'[{",".join(i for i in verify_links_reason[2])}]', 'path': f'/{folder_name}', }
        r = self.s.post(url=url, params=params, headers=self.headers, data=data, timeout=15, allow_redirects=False, verify=False)
        return r.json()['errno']

    @staticmethod
    def parse_url_and_code(url_code: str) -> Tuple[str, str]:
        """解析 URL 和提取码"""
        url, passwd = re.sub(r'提取码*[：:](.*)', r'\1', url_code).split(' ', maxsplit=1)
        return url.strip()[:47], passwd.strip()[-4:]

    def verify_link(self, link_url: str, pass_code: str) -> Union[list, str, int]:
        """验证链接有效性"""
        # 对于有提取码的链接，先验证提取码，获取 bdclnd 并更新 cookie
        if pass_code:
            bdclnd = self.verify_pass_code(link_url, pass_code)
            if isinstance(bdclnd, int):
                return bdclnd
            self.update_cookie(bdclnd)

        # 请求网盘链接，获取必要参数
        return self.parse_response(self.request_link(link_url))

    def process_link(self, url_code: str, folder_name: str) -> None:
        """验证和转存链接，输出最终结果"""
        # 检查链接有效性
        reason = self.verify_link(*self.parse_url_and_code(url_code))
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
        """加入暂停检测逻辑，并尝试处理链接"""
        while not self.running:
            time.sleep(DELAY_SECONDS)
        self.process_link(url_code, self.folder_name)
        time.sleep(DELAY_SECONDS)

    def prepare_run(self) -> None:
        """初始化变量，准备运行"""
        self.cookie = "".join(self.entry_cookie.get().split())
        self.folder_name = "".join(self.entry_folder_name.get().split())
        self.link_list = list(dict.fromkeys([self.sanitize_link(f'{link} ') for link in self.text_links.get(1.0, ttk.END).split('\n') if link]))
        self.total_task_count = len(self.link_list)
        self.headers['Cookie'] = self.cookie
        self.s.trust_env = self.var_trust_env.get()
        self.safe_mode = self.var_safe_mode.get()
        self.completed_task_count = 0
        # 初始化 ui，写入配置
        self.change_status('init')
        self.change_status('running')
        self.write_config(f'{self.cookie}\n{self.folder_name}')

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

    def handle_process_links(self) -> None:
        """执行转存"""
        for url_code in self.link_list:
            self.insert_logs(f'不支持的链接：{url_code}') if not url_code.startswith('https://pan.baidu.com/') else self.pause_detection(url_code)
            self.completed_task_count += 1
            self.change_status('update')

    def main(self) -> None:
        """转存主函数"""
        try:
            self.prepare_run()
            self.handle_input()
            self.handle_bdstoken()
            self.handle_create_dir()
            self.handle_process_links()
        except Exception as e:
            self.insert_logs(f'运行出错，请重新运行本程序。错误信息如下：\n{e}\n{traceback.format_exc()}')
            self.change_status('error')
        finally:
            self.s.close()
            self.change_status('stopped')

    def run(self) -> None:
        """运行程序"""
        self.root.mainloop()


if __name__ == '__main__':
    BaiduPanFilesTransfers().run()
