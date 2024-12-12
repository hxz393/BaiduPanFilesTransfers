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
from src.utils import thread_it, write_config, parse_response, normalize_link, parse_url_and_code, update_cookie, generate_code


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
        """
        转存主函数，流程为：
        1.获取用户输入，更新按钮和标签状态；
        2.检查用户输入，有问题则终止并发送日志；
        3.获取 bdstoken，如果获取失败则终止；
        4.获取根目录文件列表，建立转存目录；
        5.批量转存链接。先验证链接有效性，再转存文件，插入结果到日志框。
        """
        try:
            self.prepare_run()
            self.setup_save()
            self.handle_input()
            self.handle_bdstoken()
            self.handle_create_dir(folder_name=self.folder_name)
            self.handle_process_save()
        except Exception as e:
            self.insert_logs(f'程序出现未预料错误，信息如下：\n{e}\n{traceback.format_exc()}')
        finally:
            self.network.s.close()
            self.change_status('stopped')

    def share(self) -> None:
        """
        分享主函数，流程为：
        0.弹出设置窗口，设置分享参数；
        1.获取用户输入，更新按钮和标签状态；
        2.检查用户输入，有问题则终止并发送日志；
        3.获取 bdstoken，如果获取失败则终止；
        4.获取目标目录文件列表，如果为空则终止；
        5.批量分享文件。先向链接框插入文件名，再创建分享，插入结果到日志框。
        """
        try:
            # 创建对话框实例，如果对话框没有返回输入值，则忽略
            self.dialog_result = CustomDialog(self.root)
            if self.dialog_result.result:
                self.prepare_run()
                self.handle_input(task_count_check=False)
                self.handle_bdstoken()
                self.handle_list_dir()
                self.setup_share()
                self.handle_process_share()
        except Exception as e:
            self.insert_logs(f'程序出现未预料错误，信息如下：\n{e}\n{traceback.format_exc()}')
        finally:
            self.network.s.close()
            self.change_status('stopped')

    def prepare_run(self) -> None:
        """获取变量，准备运行。转存和分享共用逻辑"""
        # 从用户输入获取变量
        self.cookie = "".join(self.root.entry_cookie.get().split())
        self.folder_name = "".join(self.root.entry_folder_name.get().split())
        self.network.s.trust_env = self.root.var_trust_env.get()
        self.custom_mode = self.root.var_custom_mode.get()
        self.check_mode = self.root.var_check_mode.get()

        # 更新 cookie、初始化任务总数、更改状态、写入配置文件
        self.completed_task_count = 0
        self.network.headers['Cookie'] = self.cookie
        self.change_status('init')
        write_config(f'{self.cookie}\n{self.folder_name}')

    def setup_save(self) -> None:
        """准备链接，更新状态"""
        # 从文本链接控件获取全部链接，清洗并标准化链接。注意链接后拼接一个空格，是为了后面能统一处理带与不带提取码的链接
        raw_links = self.root.text_links.get(1.0, ttk.END).splitlines()
        self.link_list = [normalize_link(f'{link} ') for link in raw_links if link]
        self.link_list_org = list(dict.fromkeys(link for link in raw_links if link))
        # 更新任务总数和状态
        self.total_task_count = len(self.link_list)
        self.change_status('running')

    def setup_share(self) -> None:
        """准备参数，更新状态"""
        # 从设置对话框获取参数变量
        self.expiry, self.password, self.random_password = self.dialog_result.result
        # 更新任务总数和状态
        self.total_task_count = len(self.dir_list_all)
        self.change_status('sharing')

    def handle_input(self, task_count_check: bool = True) -> None:
        """输入检查，如链接数限制和 cookie 格式"""
        # 转存时才检查输入链接数量
        if task_count_check:
            self.check_condition(self.total_task_count == 0,
                                 message='无有效链接。')
            self.check_condition(self.total_task_count > SAVE_LIMIT,
                                 message=f'批量转存一次不能超过 {SAVE_LIMIT}，当前链接数：{self.total_task_count}')

        # cookie 带非 ascii 字符，或不包含 BAIDUID 时，铁定不对
        self.check_condition(not self.cookie.isascii() or self.cookie.find('BAIDUID') == -1,
                             message='百度网盘 cookie 输入不正确，请查看使用帮助。')
        # 非法字符由官方规定的。符号 / 可以使用，作为子目录的分隔符
        self.check_condition(any(char in self.folder_name for char in INVALID_CHARS),
                             message=r'转存目录名有非法字符，不能包含：< > | * ? \ :')

    def handle_bdstoken(self) -> None:
        """获取 bdstoken 相关逻辑"""
        self.network.bdstoken = self.network.get_bdstoken()
        self.check_condition(isinstance(self.network.bdstoken, int),
                             message=f'没获取到 bdstoken 参数，错误代码：{self.network.bdstoken}')

    def handle_list_dir(self) -> None:
        """获取目标目录下的文件和目录列表"""
        self.dir_list_all = self.network.get_dir_list(f'/{self.folder_name}')
        self.check_condition(isinstance(self.dir_list_all, int) or not self.dir_list_all,
                             message=f'目录 {self.folder_name} 中没获取到任何内容，请求返回：{self.dir_list_all}')

    def handle_create_dir(self, folder_name: str) -> None:
        """新建目录。如果目录已存在则不新建，否则会建立一个带时间戳的空目录"""
        result = self.network.get_dir_list(f'/{folder_name}')
        # 如果 result 为错误代码数字，代表目标目录不存在
        if self.folder_name and isinstance(result, int):
            return_code = self.network.create_dir(folder_name)
            self.check_condition(return_code != 0,
                                 message=f'创建目录失败，错误代码：{return_code}')

    def handle_process_save(self) -> None:
        """执行批量转存"""
        for url_code in self.link_list:
            self.process_save(url_code)

    def handle_process_share(self) -> None:
        """执行批量分享"""
        for info in self.dir_list_all:
            self.process_share(info)

    def process_save(self, url_code: str) -> None:
        """执行转存操作并记录结果"""
        # 跳过非网盘链接
        if 'https://pan.baidu.com/' not in url_code:
            self.insert_logs(f'不支持的链接：{url_code}')
        else:
            # 执行转存过程，通过简单的循环判断是否要暂停
            self.pause_detection(url_code)

        # 处理完毕一个链接，更新状态栏任务计数
        self.change_status('update')

    def process_share(self, info: Dict[str, Any]) -> None:
        """执行分享操作并记录结果"""
        # 插入要分享的文件或文件夹到链接输入框，对文件夹加入 "/" 标记来区别
        is_dir = "/" if info["isdir"] == 1 else ""
        filename = f"{info['server_filename']}{is_dir}"
        msg = f'目录：{filename}' if is_dir else f'文件：{filename}'
        self.insert_logs(msg, alt=True)

        # 处理提取码
        password = self.password if not self.random_password else generate_code()

        # 发送创建分享请求
        r = self.network.create_share(info['fs_id'], EXP_MAP[self.expiry], password)
        if isinstance(r, str):
            result = f'分享成功：{r}?pwd={password} {msg}'
        else:
            result = f'分享失败：错误代码（{r}） {msg}'

        # 记录日志，更改状态
        self.insert_logs(result)
        self.change_status('update')

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

    def check_condition(self, condition: bool, message: str) -> None:
        """
        用户输入或函数返回检查。
        如果条件 condition 为 True，表示错误不可恢复，中断当前任务流程。
        单个链接处理出错，应该直接调用 insert_logs 函数记录错误，不中断任务。

        :param condition: 条件表达式
        :param message: 插入到日志框的内容
        """
        if condition:
            self.change_status('error')
            self.insert_logs(message)
            sys.exit()

    def insert_logs(self, message: str, alt: bool = False) -> None:
        """
        在文本框末尾插入内容

        :param message: 插入到日志框的内容
        :param alt: 如果为 True，插入到链接输入框，用于批量分享时记录文件名
        """
        text_box = self.root.text_links if alt else self.root.text_logs
        text_box.insert('end', f'{message}\n')
        text_box.see(ttk.END)

    def pause_detection(self, url_code: str) -> None:
        """循环检测暂停逻辑，每个转存任务开始时都会检测"""
        # 只要 self.running 状态没变，会一直等待。而状态变化由用户点击按钮控制
        while not self.running:
            time.sleep(DELAY_SECONDS)

        # 执行验证链接和转存文件
        self.verify_and_save(url_code)
        # 转存完毕等待一小段时间。如果要转存超过 1000 个链接，可以增加 DELAY_SECONDS 到 3 以上。
        time.sleep(DELAY_SECONDS)

    def verify_and_save(self, url_code: str) -> None:
        """验证链接和转存文件"""
        # 验证链接是否有效，返回的数字为错误代码，反之返回参数列表
        result = self.verify_link(*parse_url_and_code(url_code))
        # 如果开启检查模式，插入检查结果，然后结束
        if self.check_mode:
            self.check_only(result, url_code)
        else:
            self.save_file(result, url_code, self.folder_name)

    def verify_link(self, url: str, password: str) -> Union[List[str], int]:
        """验证链接有效性，验证通过返回转存所需参数列表"""
        # 对于有提取码的链接先验证提取码，试图获取更新 bdclnd
        if password:
            bdclnd = self.network.verify_pass_code(url, password)
            # 如果 bdclnd 是错误代码，直接返回
            if isinstance(bdclnd, int):
                return bdclnd

            # 更新 bdclnd 到 cookie
            self.network.headers['Cookie'] = update_cookie(bdclnd, self.network.headers['Cookie'])

        # 直接访问没有提取码的链接，或更新 bdclnd 后再次访问，获取转存必须的 3 个参数
        response = self.network.get_transfer_params(url)
        # 这里不考虑网络异常了，假设请求一定会返回页面内容，对其进行解析
        return parse_response(response)

    def check_only(self, result: Union[List[str], int], url_code: str) -> None:
        """开启检查模式时，只管判断返回值类型，并输出结果到日志"""
        if isinstance(result, list):
            self.insert_logs(f'链接有效：{url_code} {"目录" if result[4] == ["1"] else "文件"}：{result[3]}')
        else:
            self.insert_logs(f'链接无效：{url_code} 原因：{ERROR_CODES.get(result, f"错误代码（{result}）")}')

    def creat_user_dir(self, folder_name: str) -> str:
        """建立用户指定目录，返回完整路径。目录名从原始输入取，函数为 custom_mode 专用"""
        self.check_condition(not folder_name, message='必须输入转存目录')
        # 对原始输入进行分割
        link_org_sep = self.link_list_org[self.completed_task_count].split()
        # 建立自定义目录，如果没有指定则用行数代替
        custom_folder = link_org_sep[0]
        folder_name = f'{folder_name}/{custom_folder}' if 'pan.baidu.com' not in custom_folder else f'{folder_name}/{self.completed_task_count + 1}'
        # 此处用替换处理目标目录名非法字符，不报错了
        folder_name = folder_name.translate(str.maketrans({char: '_' for char in INVALID_CHARS}))
        self.handle_create_dir(folder_name)

        return folder_name

    def save_file(self, result: Union[List[str], int], url_code: str, folder_name: str) -> None:
        """转存文件。返回结果为列表时，执行转存文件，否则跳过转存"""
        file_info = ""
        if isinstance(result, list):
            file_info = f'{"目录" if result[4] == ["1"] else "文件"}：{result[3]}'
            # 如果开启安全转存模式，对每个转存链接建立目录
            if self.custom_mode:
                folder_name = self.creat_user_dir(folder_name)
                result = self.network.transfer_file(result, folder_name)
                file_info = f'{file_info} 转存到：{folder_name}'
            # 改在这里检查链接重复，在日志中查找。链接有出现过不转存，直接赋值结果为错误代码 4
            elif url_code in self.root.text_logs.get('1.0', 'end'):
                result = 4
            # 正常转存
            else:
                result = self.network.transfer_file(result, folder_name)

        # 最后插入转存结果到日志框
        self.insert_logs(f'{ERROR_CODES.get(result, f"转存失败，错误代码（{result}）")}：{url_code} {file_info}')
