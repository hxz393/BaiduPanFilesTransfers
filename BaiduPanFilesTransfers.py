"""
打包命令：pyinstaller -F -w -i BaiduPanFilesTransfers.ico --hidden-import=tkinter -n BaiduPanFilesTransfers BaiduPanFilesTransfers.py

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

from src.constants import *

# 忽略证书验证警告
requests.packages.urllib3.disable_warnings()


class BaiduPanFilesTransfers:
    """本程序旨在提供一个简单 GUI 界面，用于批量转存、分享、检查百度网盘链接。尽可能地压缩代码（失败了）"""

    def __init__(self):
        """初始化 UI 元素"""
        self.setup_window()
        self.setup_ui()
        self.init_session()
        self.read_config()

    def setup_window(self) -> None:
        """主窗口配置"""
        self.root = ttk.Window()
        self.root.style.theme_use(COLOR_THEME)
        self.root.iconbitmap(temp_file.name)
        self.root.title(f"{MAIN_TITLE} {MAIN_VERSION}")
        self.root.update_idletasks()
        self.root.grid_columnconfigure(0, weight=1)
        self.root.place_window_center()

    def setup_ui(self) -> None:
        """定义窗口元素和元素布局"""
        init_row = 1
        # Cookie 标签和输入框、目标路径标签和输入框
        self.entry_cookie = self.create_entry(init_row, LABEL_MAP['cookie'])
        self.entry_folder_name = self.create_entry(init_row + 2, LABEL_MAP['folder_name'])
        # 链接标签和输入框、结果标签和日志框
        editor = TextEditor(self.root)
        self.text_links = editor.create_text(init_row + 4, LABEL_MAP['links'], LABEL_MAP['links_tip'])
        self.text_links.bind("<Button-3>", lambda e: self.show_menu(e, self.make_menu(self.text_links)))
        self.text_logs = editor.create_text(init_row + 7, LABEL_MAP['logs'], LABEL_MAP['logs_tip'])
        self.text_logs.bind("<Button-3>", lambda e: self.show_menu(e, self.make_menu(self.text_logs)))
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
        entry.bind("<Button-3>", lambda e: self.show_menu(e, self.make_menu(entry)))
        entry.grid(row=row + 1, sticky='we', padx=MW_PADDING, pady=MW_PADDING)
        return entry

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

    @staticmethod
    def make_menu(w) -> ttk.Menu:
        """创建右键菜单"""
        the_menu = ttk.Menu(w, tearoff=0)
        the_menu.add_command(label="撤销", command=lambda: w.event_generate('<<Undo>>'))
        the_menu.add_command(label="重做", command=lambda: w.event_generate('<<Redo>>'))
        the_menu.add_separator()
        the_menu.add_command(label="剪切", command=lambda: w.event_generate('<<Cut>>'))
        the_menu.add_command(label="复制", command=lambda: w.event_generate('<<Copy>>'))
        the_menu.add_command(label="粘贴", command=lambda: w.event_generate('<<Paste>>'))
        the_menu.add_separator()
        the_menu.add_command(label="全选", command=lambda: w.event_generate('<<SelectAll>>'))
        the_menu.add_command(label="删除", command=lambda: w.event_generate('<<Clear>>'))
        return the_menu

    @staticmethod
    def show_menu(e, menu) -> None:
        """显示右键菜单"""
        menu.tk_popup(e.x_root, e.y_root)

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
            self.text_logs.config(fg='black')
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
            self.check_condition(True, f'运行批量转存出错，信息如下：\n{e}\n{traceback.format_exc()}')
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
            self.check_condition(True, f'运行批量分享出错，信息如下：\n{e}\n{traceback.format_exc()}')
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
        self.style.theme_use(COLOR_THEME)
        self.place_window_center()
        self.title(LABEL_MAP['settings_title'])
        self.iconbitmap(temp_file.name)
        self.resizable(width=False, height=False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self._create_widgets()
        self.wait_window(self)

    # noinspection PyArgumentList
    def _create_widgets(self) -> None:
        """创建控件元素"""
        master = ttk.Frame(self)
        master.pack(padx=10, pady=10, fill="both", expand=True)
        # 有效期下拉选择框
        self.var_expiry = ttk.StringVar(self, value=list(EXP_MAP.keys())[-1])
        ttk.Label(master, text=LABEL_MAP['expiry_title']).grid(row=0, column=0, sticky='e')
        ttk.Combobox(master, textvariable=self.var_expiry, values=list(EXP_MAP.keys()), state="readonly", bootstyle='primary').grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        # 提取码输入框
        self.var_password = ttk.StringVar(self, value="1234")
        ttk.Label(master, text=LABEL_MAP['password_title']).grid(row=1, column=0, sticky='e')
        ttk.Entry(master, textvariable=self.var_password, bootstyle="info").grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        # 在两个 frame 之间插入分割线
        ttk.Separator(self, orient='horizontal').pack(fill="x")
        # 底部按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text=LABEL_MAP['ok'], command=self._validate, bootstyle='primary').pack(side='right', padx=5)
        ttk.Button(button_frame, text=LABEL_MAP['cancel'], command=self.destroy, bootstyle='danger').pack(side='right', padx=5)

    def _validate(self) -> bool:
        """验证输入提取码有效性"""
        if not re.match("^[a-zA-Z0-9]{4}$", self.var_password.get()):
            Messagebox.show_warning(title=LABEL_MAP['validate_title'], message=LABEL_MAP['validate_msg'], master=self)
            return False
        self.result = (self.var_expiry.get(), self.var_password.get())
        self.destroy()
        return True


class ToolTip(object):
    """手动实现提示气泡"""

    def __init__(self, widget, text: str = ''):
        self.widget = widget
        self.text = text
        self.tips = None
        self.tooltip_id = None
        self.tooltip_color = '#ffffe0'
        self.x = self.y = 0
        self._binding()

    def _binding(self) -> None:
        """配置鼠标绑定事件"""
        self.widget.bind("<Enter>", self._enter)
        self.widget.bind("<Leave>", self._leave)
        self.widget.bind("<ButtonPress>", self._leave)

    def _enter(self, _: object = None) -> None:
        """鼠标进入事件"""
        self._schedule()

    def _leave(self, _: object = None) -> None:
        """鼠标离开事件"""
        self._unschedule()
        self._hide()

    def _schedule(self) -> None:
        """设置定时器"""
        self._unschedule()
        self.tooltip_id = self.widget.after(100, self._show)

    def _unschedule(self) -> None:
        """取消定时器"""
        if self.tooltip_id:
            self.widget.after_cancel(self.tooltip_id)
            self.tooltip_id = None

    def _show(self) -> None:
        """显示气泡提示"""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() - 25
        # 创建一个悬浮窗口
        self.tips = tw = ttk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(tw, text=self.text, background=self.tooltip_color, relief='solid', borderwidth=1)
        label.pack(ipadx=1)

    def _hide(self) -> None:
        """隐藏气泡提示"""
        if self.tips:
            self.tips.destroy()
            self.tips = None


class TextEditor:
    """文本编辑框，加入提示文字、滚动条"""

    def __init__(self, root):
        self.root = root
        self.default_font = ("", 10)
        self.placeholder_color = 'grey'
        self.text_color = 'black'

    def create_text(self, row: int, label_text: str, placeholder: str = '') -> ttk.Text:
        """建立标签、文本框和滚动条"""
        self._create_label(row, label_text)
        text = self._create_text_widget(row + 1)
        self._config_scrollbar(text, row + 1)
        self._manage_placeholder(text, placeholder)
        return text

    def _create_label(self, row: int, label_text: str) -> None:
        """建立配套标签"""
        ttk.Label(self.root, text=label_text).grid(row=row, column=0, sticky='w', padx=MW_PADDING, pady=MW_PADDING)

    def _create_text_widget(self, row: int) -> ttk.Text:
        """建立文本框"""
        text = ttk.Text(self.root, undo=True, font=self.default_font, wrap='none', height=10)
        text.grid(row=row, column=0, sticky='wens', padx=MW_PADDING, pady=(10, 10))
        self.root.grid_rowconfigure(row, weight=1)
        return text

    def _config_scrollbar(self, text: ttk.Text, row: int) -> None:
        """建立配置文本框滚动条"""
        scrollbar = ttk.Scrollbar(self.root)
        scrollbar.grid(row=row, column=1, sticky='ns')
        scrollbar.config(command=text.yview)
        text.config(yscrollcommand=scrollbar.set)

    def _manage_placeholder(self, text: ttk.Text, placeholder: str) -> None:
        """管理文本框提示文字占位符"""
        if placeholder:
            text.insert("1.0", placeholder)
            text.config(fg=self.placeholder_color)
            text.bind("<FocusIn>", lambda event, t=text, p=placeholder: self._on_focus_in(t, p))
            text.bind("<FocusOut>", lambda event, t=text, p=placeholder: self._on_focus_out(t, p))

    def _on_focus_in(self, text: ttk.Text, placeholder: str) -> None:
        """文本框获得焦点时，清除提示文字"""
        if text.get("1.0", "end-1c") == placeholder:
            text.delete("1.0", "end")
            text.config(fg=self.text_color)

    def _on_focus_out(self, text: ttk.Text, placeholder: str) -> None:
        """文本框失去焦点时，添加提示文字"""
        if not text.get("1.0", "end-1c"):
            text.insert("1.0", placeholder)
            text.config(fg=self.placeholder_color)


if __name__ == '__main__':
    # 生成图标
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ico') as temp_file:
        temp_file.write(zlib.decompress(base64.b64decode(ICON_BASE64)))
    atexit.register(os.remove, temp_file.name)
    BaiduPanFilesTransfers().run()
