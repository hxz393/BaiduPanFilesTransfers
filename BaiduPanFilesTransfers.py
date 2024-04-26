"""
打包命令：pyinstaller -F -w -i BaiduPanFilesTransfers.ico --hidden-import=tkinter -n BaiduPanFilesTransfers BaiduPanFilesTransfers.py

:title: BaiduPanFilesTransfers
:site: https://github.com/hxz393/BaiduPanFilesTransfers
:author: assassing
:contact: hxz393@gmail.com
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""

import re
import sys
import time
import traceback
import webbrowser
from typing import Union, Tuple, Callable

import ttkbootstrap as ttk

from src.constants import *
from src.network import Network
from src.ui import ToolTip, CustomDialog, TextEditor, RightClickMenu
from src.utils import thread_it, write_config, read_config, create_icon, normalize_link


class BaiduPanFilesTransfers:
    """本程序旨在提供一个简单 GUI 界面，用于批量转存、分享、检查百度网盘链接。尽可能地压缩代码（失败了）"""

    def __init__(self):
        """初始化 UI 元素"""
        self.setup_window()
        self.setup_ui()
        self.init_config()

    def setup_window(self) -> None:
        """主窗口配置"""
        self.root = ttk.Window()
        self.root.style.theme_use(COLOR_THEME)
        self.root.iconbitmap(create_icon())
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
        self.text_logs = editor.create_text(init_row + 7, LABEL_MAP['logs'], LABEL_MAP['logs_tip'])
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
        rcm = RightClickMenu(entry)
        entry.bind("<Button-3>", rcm.show_menu)
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
        button = ttk.Button(self.frame_bottom, text=text, width=10, padding="17 17 17 17", command=lambda: thread_it(command))
        button.grid(row=0, column=column, padx=MW_PADDING)
        return button

    def init_config(self) -> None:
        """初始化配置"""
        self.network = Network()
        self.config = read_config()
        self.entry_cookie.insert(0, self.config[0].strip() if self.config else '')
        self.entry_folder_name.insert(0, self.config[1].strip() if len(self.config) > 1 else '')

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
            self.bottom_save.config(text='批量转存', state="normal", bootstyle='primary', command=lambda: thread_it(self.save, ))
            self.bottom_share.config(state="normal")

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
        cookies_dict = dict(map(lambda item: item.split('=', 1), filter(None, self.network.headers['Cookie'].split(';'))))
        cookies_dict['BDCLND'] = bdclnd
        self.network.headers['Cookie'] = ';'.join([f'{key}={value}' for key, value in cookies_dict.items()])

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
        url, passwd = url_code.split(' ', maxsplit=1)
        return url.strip()[:47], passwd.strip()[-4:]

    def verify_link(self, link_url: str, pass_code: str) -> Union[list, str, int]:
        """验证链接有效性，验证通过返回转存所需参数列表"""
        # 对于有提取码的链接先验证提取码，试图获取更新 bdclnd。如果返回的 bdclnd 是数字错误代码，直接中断
        if pass_code:
            bdclnd_or_err = self.network.verify_pass_code(link_url, pass_code)
            if isinstance(bdclnd_or_err, int):
                return bdclnd_or_err
            self.update_cookie(bdclnd_or_err)
        # 请求网盘链接，获取转存必须的 3 个参数
        return self.parse_response(self.network.get_transfer_params(link_url))

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
                self.network.create_dir(folder_name)
            reason = self.network.transfer_file(reason, folder_name)
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
        self.network.headers['Cookie'] = self.cookie
        self.network.s.trust_env = self.var_trust_env.get()
        self.safe_mode = self.var_safe_mode.get()
        self.check_mode = self.var_check_mode.get()
        self.completed_task_count = 0
        self.change_status('init')
        write_config(f'{self.cookie}\n{self.folder_name}')

    def setup_save(self) -> None:
        """准备转存，初始化界面"""
        self.link_list = list(dict.fromkeys([normalize_link(f'{link} ') for link in self.text_links.get(1.0, ttk.END).split('\n') if link]))
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
        self.check_condition(any(char in self.folder_name for char in INVALID_CHARS), r'转存文件夹名有非法字符，不能包含 < > | * ? \ :，请改正目录名后重试。')

    def handle_bdstoken(self) -> None:
        """获取 bdstoken 相关逻辑"""
        self.network.bdstoken = self.network.get_bdstoken()
        self.check_condition(isinstance(self.network.bdstoken, int), f'没获取到 bdstoken，错误代码：{self.network.bdstoken}')

    def handle_create_dir(self) -> None:
        """新建目录。如果目录已存在则不新建，否则会建立一个带时间戳的目录"""
        if self.folder_name and self.folder_name not in [dir_json['server_filename'] for dir_json in self.network.get_dir_list()]:
            result = self.network.create_dir(self.folder_name)
            self.check_condition(result != 0, f'创建目录失败，错误代码：{result}')

    def handle_list_dir(self) -> None:
        """获取目标目录下的文件和目录列表。如果返回的是数字，代表没有获取到文件列表"""
        self.dir_list_all = self.network.get_dir_list(folder_name=f'/{self.folder_name}')
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
            share_link = self.network.create_share(info['fs_id'], EXP_MAP[self.expiry], self.password)
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
            self.network.s.close()
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
            self.network.s.close()
            self.change_status('stopped')

    def run(self) -> None:
        """运行程序"""
        self.root.mainloop()


if __name__ == '__main__':
    BaiduPanFilesTransfers().run()
