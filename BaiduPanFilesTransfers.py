"""
打包命令：pyinstaller -F -w -i BaiduPanFilesTransfers.ico -n BaiduPanFilesTransfers BaiduPanFilesTransfers.py

:title: BaiduPanFilesTransfers
:site: https://github.com/hxz393/BaiduPanFilesTransfers
:author: assassing
:contact: hxz393@gmail.com
:copyright: Copyright 2023, hxz393. 保留所有权利。
"""

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
from tkinter import Tk, Entry, Label, Text, Scrollbar, Button, Checkbutton, W, S, N, E, END, NONE, BooleanVar
from typing import Any, Union

import requests
from retrying import retry

requests.packages.urllib3.disable_warnings()

# 静态变量
BASE_URL = 'https://pan.baidu.com'
ERROR_CODES = {
    -1: '链接失效，没获取到 shareid',
    -2: '链接失效，没获取到 user_id',
    -3: '链接失效，没获取到 fs_id',
    '百度网盘-链接不存在': '链接失效，文件已经被删除或取消分享',
    '百度网盘 请输入提取码': '链接错误，缺少提取码',
    -9: '链接错误，提取码错误或验证已过期',
    -62: '链接错误尝试次数过多，请手动转存或稍后再试',
    105: '链接错误，链接格式不正确',
    -4: '转存失败，无效登录。请退出账号在其他地方的登录',
    -6: '转存失败，请用浏览器无痕模式获取 Cookie',
    4: '转存失败，目录中已有同名文件或文件夹存在',
    -8: '转存失败，目录中已有同名文件或文件夹存在',
    12: '转存失败，转存文件数超过限制',
    -7: '转存失败，秒传文件名有非法字符',
    404: '转存失败，秒传无效',
    -10: '转存失败，容量不足',
    20: '转存失败，容量不足',
    0: '转存成功',
}
# noinspection LongLine
ICON_BASE64 = 'eJyFUw1MU1cUvjgyfa+vr++1WGw3FTKDtHVLQDPCtojLFlpKKY4pLE0EDAaEMuKyOBWmI8ZMZ5T6Ax2xpgKKCs5kGtT9KA5B/GFxAUpBES1TZ0Z0kWQZLMZ9O6+um1tIdl6+d+79vvPdd25eDmNR9EgSo3ccWx3NmJ4xlkggipinvBJLotn/RdQrsU16i9aXY5Z9HsonzNr9Jy06354F8r7cxJh6A2OImspoZq3PJ2rrckxab7dJ9k6YtJ9DgSWmHmZlLXsnTXJdz3xpr2vu3AMznvXOY7unWwyeNeX5bQ/ffesIEmQPFsZ5Ufn+t2htCqB2+xWkLzpAfA3Mes+jtxftr9y5s5uL9Byv2bLc/rrvl+vBMRS7WmCe9Rn83qu4cjGEuppOdJ0fQfeFEApyjuDYwV4MDYyNj49PrAQwbbZurXG2Zt3VLR+fppoRWOZUw/FmLYKB+7Cn7QFpSH15G3qv3cGDsV/xzZkBVBQfRklBY3+21RNnEN0uo1Qx2XLoMur3noNBLEd+bj2u9YRgiluHWLUbBk05mvydGA09wGtJ1cSVQa8ufawXi1fr1Ct9sZoifNFyCTu2nYROKET6ks0YvnEfmemfhvfz5rhxsXMIYz+P441Xq6AV8sOQVSuOSULueUnIQ13tKTT4z0JWv4cXZhXgxJeX8X3PTXz4gR8HG9sxGPwRP917CLt1E0TVsgh+UPPOCwKfjZLi3ejqCuBFowsC70RyUimOH+/E8PBddHT0ku7Bjet3YU1fDxWfFYbAZ/XxvP0QAcnJJQgEbiMjYz2UvYKYmHeQkJAPo3E5Fi9eQ2fdQ0qKm7SMMDguo43j7CU8b3ssSVnw+8/g6NF2zJy5lHTbv1BYSP+g9ybi410R7gmd8ZEo2l6i9ZDCpaa60d9/C2Vlu6BW2//2ajQONDR8hcbGr2mdGeFDKlXmAsY+maZSWSto/5sg2LFq1Q4MDIRQVLSd+l8KUcyE01mFwcFROBwb/vJaJ+nblYylhSdKp3Oqid9FmJAkB0pLPejrG0Fb2yU0N59FMDiKrVubIctOxfs7x9n2UR/yszOg1dpE0tbSGbep9ycpKWXYuNGPmppW5OVtpl6y/yD9Dumb/uv9J9KilTtRTRWh/ekdbaOUOzjOWk05KdJzJELTGfvuOcaqp5zqqUOpVTyK90+HRLty'
MAIN_TITLE = 'BaiduPanFilesTransfers'
MAIN_VERSION = '2.4.0'
CONFIG_PATH = 'config.ini'


class BaiduPanFilesTransfers:
    """
    本程序旨在提供一个简单 GUI 界面，用于批量转存百度网盘文件。尽可能地压缩代码。
    """

    def __init__(self):
        self.init_ui_elements()
        self.init_session()
        self.read_config()

    def init_ui_elements(self):
        """初始化UI元素"""
        # 实例化 TK
        self.root = Tk()
        self.setup_window()
        self.add_ui_elements()

    def setup_window(self):
        """主窗口配置"""
        _, icon_path = tempfile.mkstemp()
        with open(icon_path, 'wb') as icon_file:
            icon_file.write(zlib.decompress(base64.b64decode(ICON_BASE64)))
        self.root.iconbitmap(default=icon_path)
        self.root.title(f"{MAIN_TITLE} {MAIN_VERSION}")
        self.root.geometry('400x480+240+240')
        self.root.minsize(400, 480)
        self.root.attributes("-alpha", 0.88)

    def add_ui_elements(self):
        """定义窗口元素"""
        self.init_row = 1
        # Cookie 标签和输入框
        self.entry_cookie = self.create_label_entry(self.init_row, '1.下面填入百度网盘 Cookies，不带引号：')
        # 保存文件夹名称标签和输入框
        self.entry_folder_name = self.create_label_entry(self.init_row + 2, '2.下面填入文件保存位置（默认根目录），不能包含<,>,|,*,?,,/：')
        # 链接标签和输入框
        Label(self.root, text='3.下面粘贴链接，每行一个。格式为：链接 提取码').grid(row=self.init_row + 4, sticky=W)
        self.text_links = self.create_text_scrollbar(self.init_row + 5)
        # 运行按钮
        self.bottom_run = Button(self.root, text='4.点击运行', command=lambda: self.thread_it(self.main, ), width=10, height=1, relief='solid')
        self.bottom_run.grid(row=self.init_row + 6, pady=6, sticky=W, padx=4)
        # 结果文本框
        self.text_logs = self.create_text_scrollbar(self.init_row + 7)
        # 系统代理复选框
        self.trust_env_var = BooleanVar()
        self.trust_env_checkbutton = Checkbutton(self.root, text='系统代理', variable=self.trust_env_var)
        self.trust_env_checkbutton.grid(row=self.init_row + 6, sticky=E, padx=4)
        # 安全转存复选框
        self.safe_mode_var = BooleanVar()
        self.safe_mode_checkbutton = Checkbutton(self.root, text='安全转存', variable=self.safe_mode_var)
        self.safe_mode_checkbutton.grid(row=self.init_row + 6, sticky=E, padx=84)
        # 状态标签
        self.label_state = Label(self.root, text='使用帮助', font=('Arial', 9, 'underline'), foreground="#0000ff", cursor='heart')
        self.label_state.grid(row=self.init_row + 8, sticky=E, padx=4)
        self.label_state.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/hxz393/BaiduPanFilesTransfers"))

    def create_label_entry(self, row: int, label_text: str) -> Entry:
        """建立标签和输入框函数"""
        Label(self.root, text=label_text).grid(row=row, column=0, sticky=W)
        entry = Entry(self.root)
        entry.grid(row=row + 1, column=0, sticky=W + E, padx=(4, 1), pady=(5, 5))
        self.root.grid_columnconfigure(0, weight=1)
        return entry

    def create_text_scrollbar(self, row: int) -> Text:
        """建立文本框和滚动条"""
        text = Text(self.root, height=5, wrap=NONE)
        text.grid(row=row, column=0, sticky=W + E + N + S, padx=(4, 1), pady=(5, 5))
        scrollbar = Scrollbar(self.root, width=5)
        scrollbar.grid(row=row, column=1, sticky=S + N, rowspan=1)
        scrollbar.configure(command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        self.root.grid_rowconfigure(row, weight=1)
        return text

    def label_state_change(self, state: str, completed_task_count: int = 0, total_task_count: int = 0) -> None:
        """状态标签变化函数"""
        self.label_state.config(font=('Arial', 9), foreground="#000000", cursor="arrow")
        self.label_state.unbind("<Button-1>")

        if state == 'error':
            self.label_state['text'] = '发生错误，错误日志如上'
        elif state == 'running':
            self.label_state['text'] = f'进度：{completed_task_count}/{total_task_count}'

    def init_session(self):
        """初始化请求会话"""
        self.session = requests.Session()
        self.bdstoken = None
        self.request_header = {
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
        """读取配置文件，并填充输入框"""
        if not os.path.exists(CONFIG_PATH):
            return

        with open(CONFIG_PATH) as f:
            config_list = f.readlines()
            config_cookie = config_list[0] if config_list else ''
            config_folder_name = config_list[1] if len(config_list) > 1 else ''
        self.entry_cookie.insert(0, config_cookie)
        self.entry_folder_name.insert(0, config_folder_name)

    @staticmethod
    def thread_it(func: Any, *args: Any) -> None:
        """多线程运行主函数"""
        t = threading.Thread(target=func, args=args)
        t.start()

    def handle_file_transfer(self, url_code: str, folder_name: str) -> None:
        """处理 https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg 123w 格式链接"""
        if url_code.startswith('https://pan.baidu.com/s/'):
            self.process_link(url_code, folder_name)
        else:
            self.insert_logs(f'不支持的链接：{url_code}')

    @staticmethod
    def sanitize_link(url_code: str) -> str:
        """预处理链接格式"""
        # 处理 http 链接
        url_code = url_code.replace("http://", "https://")
        # 处理(https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg?pwd=123w)格式链接
        url_code = url_code.replace("?pwd=", " ").replace("&pwd=", " ")
        # 处理旧格式链接
        url_code = url_code.replace("https://pan.baidu.com/share/init?surl=", "https://pan.baidu.com/s/1")
        return url_code

    def check_condition(self, condition: bool, message: str) -> None:
        """用户输入检查，如果条件condition为True，则直接终止流程"""
        if condition:
            self.label_state_change(state='error')
            self.text_logs.insert(END, message + '\n')
            sys.exit()

    # 插入日志函数
    def insert_logs(self, message: str) -> None:
        """在日志框中插入内容"""
        self.text_logs.insert(END, message + '\n')

    def update_cookie(self, bdclnd: str) -> None:
        """更新 cookie"""
        if 'BDCLND=' in self.request_header['Cookie']:
            self.request_header['Cookie'] = re.sub(r'BDCLND=(\S+);?', f'BDCLND={bdclnd};', self.request_header['Cookie'])
        else:
            self.request_header['Cookie'] += f';BDCLND={bdclnd}'

    @retry(stop_max_attempt_number=3, wait_fixed=1000)
    def get_bdstoken(self) -> Union[str, int]:
        """获取bdstoken"""
        url = f'{BASE_URL}/api/gettemplatevariable?clienttype=0&app_id=38824127&web=1&fields=[%22bdstoken%22,%22token%22,%22uk%22,%22isdocuser%22,%22servertime%22]'
        response = self.session.get(url=url, headers=self.request_header, timeout=20, allow_redirects=True, verify=False)
        return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['result']['bdstoken']

    @retry(stop_max_attempt_number=5, wait_fixed=1000)
    def get_dir_list(self) -> Union[list, int]:
        """获取目录列表"""
        url = f'{BASE_URL}/api/list?order=time&desc=1&showempty=0&web=1&page=1&num=1000&dir=%2F&bdstoken={self.bdstoken}'
        response = self.session.get(url=url, headers=self.request_header, timeout=15, allow_redirects=False, verify=False)
        return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['list']

    @retry(stop_max_attempt_number=5, wait_fixed=1000)
    def create_dir(self, folder_name: str) -> int:
        """新建目录"""
        url = f'{BASE_URL}/api/create?a=commit&bdstoken={self.bdstoken}'
        post_data = {'path': folder_name, 'isdir': '1', 'block_list': '[]', }
        response = self.session.post(url=url, headers=self.request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
        return response.json()['errno']

    @retry(stop_max_attempt_number=6, wait_fixed=1700)
    def verify_pass_code(self, link_url: str, pass_code: str) -> Union[str, int]:
        """验证提取码"""
        url = f'{BASE_URL}/share/verify?surl={link_url[25:48]}&bdstoken={self.bdstoken}&t={str(int(round(time.time() * 1000)))}&channel=chunlei&web=1&clienttype=0'
        post_data = {'pwd': pass_code, 'vcode': '', 'vcode_str': '', }
        response = self.session.post(url=url, headers=self.request_header, data=post_data, timeout=10, allow_redirects=False, verify=False)
        return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['randsk']

    @retry(stop_max_attempt_number=12, wait_fixed=1700)
    def verify_link(self, link_url: str, pass_code: str) -> Union[list, str, int]:
        """验证链接有效性"""
        # 对于有提取码的链接，先验证提取码，获取 bdclnd 并更新 cookie
        if pass_code:
            bdclnd = self.verify_pass_code(link_url, pass_code)
            if isinstance(bdclnd, int):
                return bdclnd
            self.update_cookie(bdclnd)

        response = self.session.get(url=link_url, headers=self.request_header, timeout=15, allow_redirects=True, verify=False).content.decode("utf-8")

        shareid_list = re.findall('"shareid":(\\d+?),"', response)
        user_id_list = re.findall('"share_uk":"(\\d+?)","', response)
        fs_id_list = re.findall('"fs_id":(\\d+?),"', response)
        info_title_list = re.findall('<title>(.+)</title>', response)

        if not shareid_list:
            return -1
        elif not user_id_list:
            return -2
        elif not fs_id_list:
            return info_title_list[0] if info_title_list else -3
        else:
            return [shareid_list[0], user_id_list[0], fs_id_list]

    @retry(stop_max_attempt_number=9, wait_fixed=1553)
    def transfer_file(self, verify_links_reason: list, folder_name: str) -> int:
        """转存文件"""
        url = f'{BASE_URL}/share/transfer?shareid={verify_links_reason[0]}&from={verify_links_reason[1]}&bdstoken={self.bdstoken}&channel=chunlei&web=1&clienttype=0'
        post_data = {'fsidlist': f'[{",".join(i for i in verify_links_reason[2])}]', 'path': f'/{folder_name}', }
        response = self.session.post(url=url, headers=self.request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
        return response.json()['errno']

    def process_link(self, url_code: str, folder_name: str) -> None:
        """转存标准链接"""
        link_url_org, pass_code_org = re.sub(r'提取码*[：:](.*)', r'\1', url_code.lstrip()).split(' ', maxsplit=1)
        link_url = link_url_org.strip()[:47]
        pass_code = pass_code_org.strip()[:4]
        # 执行检查链接有效性
        verify_links_reason = self.verify_link(link_url, pass_code)
        # 返回结果为列表时，执行转存文件。否则提示错误
        if isinstance(verify_links_reason, list):
            # 开启安全转存模式
            if self.safe_mode:
                folder_name = f'{folder_name}/{self.completed_task_count}'
                self.create_dir(folder_name)
            # 执行转存，检查转存结果
            transfer_files_reason = self.transfer_file(verify_links_reason, folder_name)
            if transfer_files_reason in ERROR_CODES:
                self.insert_logs(f'{ERROR_CODES[transfer_files_reason]}：{url_code}')
            else:
                self.insert_logs(f'转存失败，错误代码（{transfer_files_reason}）：{url_code}')
        elif verify_links_reason in ERROR_CODES:
            self.insert_logs(f'{ERROR_CODES[verify_links_reason]}：{url_code}')
        else:
            self.insert_logs(f'访问链接返回错误代码 {verify_links_reason}：{url_code}')

    @staticmethod
    def write_config(config: str) -> None:
        """写入配置文件"""
        with open(CONFIG_PATH, 'w') as f:
            f.write(config)

    def main(self) -> None:
        """主函数"""
        # 获取和初始化数据
        self.text_logs.delete(1.0, END)
        cookie = "".join(self.entry_cookie.get().split())
        folder_name = "".join(self.entry_folder_name.get().split())
        link_list = [self.sanitize_link(link + ' ') for link in self.text_links.get(1.0, END).split('\n') if link]
        self.session.trust_env = self.trust_env_var.get()
        self.safe_mode = self.safe_mode_var.get()
        self.completed_task_count = 0
        total_task_count = len(link_list)

        # 写入配置，禁用按钮
        self.write_config(f'{cookie}\n{folder_name}')
        self.request_header['Cookie'] = cookie
        self.bottom_run['state'] = 'disabled'
        self.bottom_run['relief'] = 'groove'
        self.bottom_run['text'] = '运行中...'

        # 开始运行函数
        try:
            # 检查链接数是否超限
            self.check_condition(total_task_count > 1000, f'转存链接数一次不能超过 1000，请减少链接数。当前连接数：{total_task_count}')
            # 检查 cookie 输入是否正确
            self.check_condition(any([ord(word) not in range(256) for word in cookie]) or cookie.find('BAIDUID=') == -1, '百度网盘 cookie 输入不正确，请检查 cookie 后重试。')

            # 执行获取 bdstoken
            self.bdstoken = self.get_bdstoken()
            self.check_condition(isinstance(self.bdstoken, int), f'没获取到 bdstoken，错误代码：{self.bdstoken}')

            # 执行获取目录列表
            dir_list = self.get_dir_list()
            self.check_condition(isinstance(dir_list, int), f'没获取到网盘目录列表，请检查 cookie 和网络后重试。错误代码：{dir_list}')

            # 执行新建目录
            if folder_name and folder_name not in [dir_json['server_filename'] for dir_json in dir_list]:
                create_dir_reason = self.create_dir(folder_name)
                self.check_condition(create_dir_reason != 0, f'转存目录名带非法字符，请改正目录名后重试。错误代码：{create_dir_reason}')

            # 执行转存
            for url_code in link_list:
                self.completed_task_count += 1
                self.handle_file_transfer(url_code, folder_name)
                self.label_state_change(state='running', completed_task_count=self.completed_task_count, total_task_count=total_task_count)

        # 故障处理
        except Exception as e:
            self.insert_logs(f'运行出错，请重新运行本程序。错误信息如下：\n{e}\n{traceback.format_exc()}')
            self.label_state_change(state='error')

        # 恢复按钮状态
        finally:
            self.bottom_run['state'] = 'normal'
            self.bottom_run['relief'] = 'solid'
            self.bottom_run['text'] = '4.点击运行'

    # 启动Tkinter
    def run(self) -> None:
        """运行程序"""
        self.root.mainloop()


if __name__ == '__main__':
    BaiduPanFilesTransfers().run()
