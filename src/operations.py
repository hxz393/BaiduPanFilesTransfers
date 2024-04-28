"""
主要功能实现逻辑，包括批量转存和分享。

:author: assassing
:contact: https://github.com/hxz393
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""

import sys
import time
import traceback
from typing import Union, List, Dict, Any

import ttkbootstrap as ttk

from src.constants import EXP_MAP, DELAY_SECONDS, INVALID_CHARS, ERROR_CODES, SAVE_LIMIT, COLOR_MAP
from src.network import Network
from src.ui import CustomDialog
from src.utils import thread_it, write_config, parse_response, normalize_link, parse_url_and_code, format_filename_and_msg, update_cookie


class Operations:
    """
    包括主功能实现流程，涉及部分对 UI 的操作。
    日志文字不额外提取到映射字典，方便定位错误。

    :param root: 主窗口
    """

    def __init__(self, root):
        self.root = root
        self.network = Network()

    def save(self) -> None:
        """转存主函数"""
        try:
            self.prepare_run()
            self.setup_save()
            self.handle_input()
            self.handle_bdstoken()
            self.handle_list_dir(folder_name='/')
            self.handle_create_dir()
            self.handle_process_save()
        except Exception as e:
            self.check_condition(True, message=f'运行批量转存出错，信息如下：\n{e}\n{traceback.format_exc()}')
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
                self.handle_input(task_count_check=False)
                self.handle_bdstoken()
                self.handle_list_dir(folder_name=f'/{self.folder_name}')
                self.setup_share()
                self.handle_process_share()
        except Exception as e:
            self.check_condition(True, message=f'运行批量分享出错，信息如下：\n{e}\n{traceback.format_exc()}')
        finally:
            self.network.s.close()
            self.change_status('stopped')

    # noinspection PyArgumentList
    def change_status(self, status: str) -> None:
        """运行状态变化更新函数"""
        if status == 'init':
            self.root.label_status.config(text='准备就绪！', font=('', 10), bootstyle='primary', cursor="arrow")
            self.root.label_status.unbind("<Button-1>")
            self.root.text_logs.config(fg=COLOR_MAP['text'])
            self.root.text_logs.delete(1.0, ttk.END)
        elif status == 'running':
            self.running = True
            self.root.bottom_share.config(state="disabled")
            self.root.bottom_save.config(text='点击暂停', bootstyle='danger', command=lambda: self.change_status('paused'))
        elif status == 'paused':
            self.running = False
            self.root.bottom_save.config(text='点击继续', bootstyle='success', command=lambda: self.change_status('running'))
        elif status == 'update':
            self.completed_task_count += 1
            self.root.label_status.config(text=f'总进度：{self.completed_task_count}/{self.total_task_count}', bootstyle='success')
        elif status == 'sharing':
            self.root.text_links.delete(1.0, ttk.END)
            self.root.bottom_share.config(state="disabled")
            self.root.bottom_save.config(state="disabled")
        elif status == 'error':
            self.root.label_status.config(text='发生错误：', bootstyle='danger')
        else:
            self.running = False
            self.root.bottom_save.config(text='批量转存', state="normal", bootstyle='primary', command=lambda: thread_it(self.save, ))
            self.root.bottom_share.config(state="normal")

    def prepare_run(self) -> None:
        """获取变量，准备运行。转存和分享共用逻辑"""
        # 从输入框获取 cookie 和目录名
        self.cookie = "".join(self.root.entry_cookie.get().split())
        self.folder_name = "".join(self.root.entry_folder_name.get().split())

        # 更新 cookie 到请求头中
        self.network.headers['Cookie'] = self.cookie

        # 获取三个设置的复选框状态
        self.network.s.trust_env = self.root.var_trust_env.get()
        self.safe_mode = self.root.var_safe_mode.get()
        self.check_mode = self.root.var_check_mode.get()

        # 初始化任务总数为 0
        self.completed_task_count = 0

        # 修改主窗口状态栏文字，清空日志输出框
        self.change_status('init')

        # 写入配置文件
        write_config(f'{self.cookie}\n{self.folder_name}')

    def setup_save(self) -> None:
        """准备转存，初始化界面"""
        # 从文本链接控件获取全部链接，并以换行符分割。
        raw_links = self.root.text_links.get(1.0, ttk.END).splitlines()

        # 清洗并标准化链接。注意链接后拼接一个空格，是为了后面能统一处理带与不带提取码的链接
        normalized_links = [normalize_link(f'{link} ') for link in raw_links if link]

        # 转为字典的方式来去除重复项
        self.link_list = list(dict.fromkeys(normalized_links))

        # 更新任务总数
        self.total_task_count = len(self.link_list)

        # 更新主窗口两个按钮的状态
        self.change_status('running')

    def setup_share(self) -> None:
        """准备分享，初始化界面"""
        self.expiry, self.password = self.dialog_result.result
        self.total_task_count = len(self.dir_list_all)
        self.change_status('sharing')

    def check_condition(self,
                        condition: bool,
                        message: str) -> None:
        """
        用户输入或函数返回检查。
        如果条件 condition 为 True，表示错误不可恢复，终止当前批量任务。
        单个链接处理出错，应该直接调用 insert_logs 函数记录错误，不中断任务。

        :param condition: 条件表达式
        :param message: 插入到日志框的内容
        """
        if condition:
            self.change_status('error')
            self.insert_logs(message)
            sys.exit()

    def insert_logs(self,
                    message: str,
                    insert_input: bool = False) -> None:
        """
        在文本框末尾插入内容

        :param message: 插入到日志框的内容
        :param insert_input: 如果为 True，插入到链接输入框，用于批量分享时记录文件名
        """
        if insert_input:
            self.root.text_links.insert('end', f'{message}\n')

        self.root.text_logs.insert('end', f'{message}\n')

    def verify_link(self, link_url: str, pass_code: str) -> Union[List[str], int]:
        """验证链接有效性，验证通过返回转存所需参数列表"""
        # 对于有提取码的链接先验证提取码，试图获取更新 bdclnd
        if pass_code:
            bdclnd = self.network.verify_pass_code(link_url, pass_code)
            # 如果返回的 bdclnd 是数字错误代码，直接返回
            if isinstance(bdclnd, int):
                return bdclnd

            # 更新 bdclnd 进 cookie
            self.network.headers['Cookie'] = update_cookie(bdclnd, self.network.headers['Cookie'])

        # 直接访问没有提取码的链接，或更新 bdclnd 后再次访问，获取转存必须的 3 个参数
        response = self.network.get_transfer_params(link_url)
        # 这里不考虑网络异常了，假设请求一定会返回页面内容，对其进行解析
        result = parse_response(response)
        return result

    def process_link(self, url_code: str, folder_name: str) -> None:
        """验证和转存链接，输出最终结果"""
        # 分割提取码
        url_code_tuple = parse_url_and_code(url_code)
        # 验证链接是否有效，返回的数字为错误代码，字典为正确参数
        result = self.verify_link(*url_code_tuple)
        # 如果开启检查模式，插入检查结果，然后结束
        if self.check_mode:
            self.check_only(result, url_code)
        else:
            r = self.save_file(result, folder_name)
            self.report_result(r, url_code)

    def check_only(self, result: Union[List[str], int], url_code: str) -> None:
        """开启检查模式时，只管判断返回值类型，并输出结果到日志"""
        if isinstance(result, list):
            self.insert_logs(f'链接有效：{url_code}')
        else:
            self.insert_logs(f'链接无效：{url_code} 原因：{ERROR_CODES.get(result, result)}')
        return

    def save_file(self, result: Union[List[str], int], folder_name: str) -> int:
        """转存文件"""
        # 返回结果为列表时，执行转存文件，返回转存结果；否则跳过转存，返回原始 result 参数
        if isinstance(result, list):
            # 如果开启安全转存模式，对每个转存链接建立目录
            if self.safe_mode:
                folder_name = f'{folder_name}/{self.completed_task_count + 1}'
                self.network.create_dir(folder_name)

            # 终于轮到发送转存请求
            result = self.network.transfer_file(result, folder_name)

        return result

    def report_result(self, result: int, url_code: str) -> None:
        """插入转存结果到日志框"""
        if result in ERROR_CODES:
            self.insert_logs(f'{ERROR_CODES[result]}：{url_code}')
        else:
            self.insert_logs(f'转存失败，错误代码（{result}）：{url_code}')

    def pause_detection(self, url_code: str) -> None:
        """加入暂停检测逻辑，并插入等待时间"""
        # 只要 self.running 状态没变，会一直等待。而状态变化由用户点击按钮控制
        while not self.running:
            time.sleep(DELAY_SECONDS * 10)

        # 执行转存顺序流程
        self.process_link(url_code, self.folder_name)
        # 转存完毕等待一小段时间。如果要转存超过 1000 个链接，可以增加 DELAY_SECONDS 到 3 以上。
        time.sleep(DELAY_SECONDS)

    def handle_bdstoken(self) -> None:
        """获取 bdstoken 相关逻辑"""
        self.network.bdstoken = self.network.get_bdstoken()
        self.check_condition(isinstance(self.network.bdstoken, int),
                             message=f'没获取到 bdstoken，错误代码：{self.network.bdstoken}')

    def handle_input(self, task_count_check: bool = True) -> None:
        """输入检查，如链接数限制和 cookie 格式"""
        # 转存时才检查输入链接数量
        if task_count_check:
            self.check_condition(self.total_task_count == 0,
                                 message='无有效链接。')
            self.check_condition(self.total_task_count > SAVE_LIMIT,
                                 message=f'转存链接数一次不能超过 {SAVE_LIMIT}，请减少链接数。当前连接数：{self.total_task_count}')

        # cookie 带非 ascii 字符，或不包含 BAIDUID 时，铁定不对
        self.check_condition(not self.cookie.isascii() or self.cookie.find('BAIDUID') == -1,
                             message='百度网盘 cookie 输入不正确，请修正 cookie 后重试。')
        # 非法字符由官方规定的。符号 / 可以使用，作为子目录的分隔符
        self.check_condition(any(char in self.folder_name for char in INVALID_CHARS),
                             message=r'转存目录名有非法字符，不能包含 < > | * ? \ :，请改正目录名后重试。')

    def handle_list_dir(self, folder_name: str) -> None:
        """获取目标目录下的文件和目录列表。如果返回的是数字，代表没有获取到文件列表"""
        self.dir_list_all = self.network.get_dir_list(folder_name=folder_name)
        self.check_condition(isinstance(self.dir_list_all, int) or not self.dir_list_all,
                             message=f'{folder_name} 中，没获取到任何要分享的文件或目录。')

    def handle_create_dir(self) -> None:
        """新建目录。如果目录已存在则不新建（转存目录带子目录时无法判断），否则会建立一个带时间戳的空目录"""
        if self.folder_name and self.folder_name not in [dir_json['server_filename'] for dir_json in self.dir_list_all]:
            r = self.network.create_dir(self.folder_name)
            self.check_condition(r != 0,
                                 message=f'创建目录失败，错误代码：{r}')

    def handle_process_save(self) -> None:
        """执行批量转存"""
        for url_code in self.link_list:
            # 跳过非网盘链接
            if not url_code.startswith('https://pan.baidu.com/'):
                self.insert_logs(f'不支持的链接：{url_code}')
            else:
                # 执行转存过程，通过简单的循环判断是否要暂停
                self.pause_detection(url_code)

            # 转存完毕一个链接，更新状态栏任务计数
            self.change_status('update')

    def handle_process_share(self) -> None:
        """执行批量分享"""
        for info in self.dir_list_all:
            msg = format_filename_and_msg(info)
            self.insert_logs(msg, insert_input=True)  # 日志记录待分享的文件或目录

            # 执行分享操作并记录结果
            self.process_share(info)

            # 更新状态
            self.change_status('update')

    def process_share(self, info: Dict[str, Any]) -> None:
        """处理分享操作并记录日志"""
        filename = info['server_filename']

        # 发送创建分享请求
        r = self.network.create_share(info['fs_id'], EXP_MAP[self.expiry], self.password)
        if isinstance(r, str):
            message = f'分享成功：{r}?pwd={self.password}，名称：{filename}'
        else:
            message = f'分享失败：错误代码（{r}），文件名：{filename}'
        self.insert_logs(message)
