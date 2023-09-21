import base64
import os
import random
import re
import sys
import tempfile
import traceback
import threading
import time
import webbrowser
import zlib
from tkinter import Tk, Entry, Label, Text, Scrollbar, Button, Checkbutton, W, S, N, E, END, NONE, BooleanVar
from urllib.parse import quote

import requests
from retrying import retry

requests.packages.urllib3.disable_warnings()

# 静态变量
CLIENT_ID = 'PMzkf1TT0hoWvfNFViVmGRiGZ7HdDKjM'
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
    9019: '转存失败，请输入有效 access_token',
    404: '转存失败，秒传无效',
    31190: '转存失败，秒传未生效',
    31039: '转存失败，秒传文件名冲突',
    -10: '转存失败，容量不足',
    20: '转存失败，容量不足',
    0: '转存成功',
}


# 检测链接种类
def check_link_type(link_list_line):
    link_type = 'unknown'
    if link_list_line[:24] == 'https://pan.baidu.com/s/':
        link_type = '/s/'
    elif re.search(r'(bdlink=|bdpan://|BaiduPCS-Go|#.*#)', link_list_line, re.IGNORECASE):
        link_type = 'rapid'
    return link_type


# 写配置文件函数
def write_config(config):
    with open('config.ini', 'w') as config_write:
        config_write.write(config)


# 处理链接格式函数
def sanitize_link(url_code):
    # 处理 http 链接
    url_code = url_code.replace("http://", "https://")
    # 处理(https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg?pwd=123w)格式链接
    url_code = url_code.replace("?pwd=", " ").replace("&pwd=", " ")
    # 处理旧格式链接
    url_code = url_code.replace("https://pan.baidu.com/share/init?surl=", "https://pan.baidu.com/s/1")
    return url_code


# 字节码转字符串
def decode_with_multiple_encodings(encoded_data):
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'gb18030', 'shift_jis', 'euc-jp', 'euc-kr', 'iso-2022-kr']

    for encoding in encodings:
        try:
            decoded_string = encoded_data.strip().decode(encoding)
            return decoded_string
        except UnicodeDecodeError:
            continue

    return ''


# 定义多线程运行主函数
def thread_it(func, *args):
    t = threading.Thread(target=func, args=args)
    t.start()


class BaiduPanFilesTransfers:
    """
    名称：BaiduPanFilesTransfers
    版本：2.3.2
    作者：assassing（https://github.com/hxz393)
    参考：https://pan.baidu.com/union/doc/rksg0sa17
    打包：pyinstaller -F -w -i bpftUI.ico -n BaiduPanFilesTransfers bpftUI.py
    """

    # 请求变量
    request_header = {
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
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    def __init__(self):
        # 会话配置
        self.session = requests.Session()
        self.bdstoken = None
        self.access_token = None

        # 实例化 TK
        self.root = Tk()

        # 运行时替换图标
        # noinspection LongLine
        self.ICON = zlib.decompress(base64.b64decode(
            'eJyFUw1MU1cUvjgyfa+vr++1WGw3FTKDtHVLQDPCtojLFlpKKY4pLE0EDAaEMuKyOBWmI8ZMZ5T6Ax2xpgKKCs5kGtT9KA5B/GFxAUpBES1TZ0Z0kWQZLMZ9O6+um1tIdl6+d+79vvPdd25eDmNR9EgSo3ccWx3NmJ4xlkggipinvBJLotn/RdQrsU16i9aXY5Z9HsonzNr9Jy06354F8r7cxJh6A2OImspoZq3PJ2rrckxab7dJ9k6YtJ9DgSWmHmZlLXsnTXJdz3xpr2vu3AMznvXOY7unWwyeNeX5bQ/ffesIEmQPFsZ5Ufn+t2htCqB2+xWkLzpAfA3Mes+jtxftr9y5s5uL9Byv2bLc/rrvl+vBMRS7WmCe9Rn83qu4cjGEuppOdJ0fQfeFEApyjuDYwV4MDYyNj49PrAQwbbZurXG2Zt3VLR+fppoRWOZUw/FmLYKB+7Cn7QFpSH15G3qv3cGDsV/xzZkBVBQfRklBY3+21RNnEN0uo1Qx2XLoMur3noNBLEd+bj2u9YRgiluHWLUbBk05mvydGA09wGtJ1cSVQa8ufawXi1fr1Ct9sZoifNFyCTu2nYROKET6ks0YvnEfmemfhvfz5rhxsXMIYz+P441Xq6AV8sOQVSuOSULueUnIQ13tKTT4z0JWv4cXZhXgxJeX8X3PTXz4gR8HG9sxGPwRP917CLt1E0TVsgh+UPPOCwKfjZLi3ejqCuBFowsC70RyUimOH+/E8PBddHT0ku7Bjet3YU1fDxWfFYbAZ/XxvP0QAcnJJQgEbiMjYz2UvYKYmHeQkJAPo3E5Fi9eQ2fdQ0qKm7SMMDguo43j7CU8b3ssSVnw+8/g6NF2zJy5lHTbv1BYSP+g9ybi410R7gmd8ZEo2l6i9ZDCpaa60d9/C2Vlu6BW2//2ajQONDR8hcbGr2mdGeFDKlXmAsY+maZSWSto/5sg2LFq1Q4MDIRQVLSd+l8KUcyE01mFwcFROBwb/vJaJ+nblYylhSdKp3Oqid9FmJAkB0pLPejrG0Fb2yU0N59FMDiKrVubIctOxfs7x9n2UR/yszOg1dpE0tbSGbep9ycpKWXYuNGPmppW5OVtpl6y/yD9Dumb/uv9J9KilTtRTRWh/ekdbaOUOzjOWk05KdJzJELTGfvuOcaqp5zqqUOpVTyK90+HRLty'))
        _, self.ICON_PATH = tempfile.mkstemp()
        with open(self.ICON_PATH, 'wb') as icon_file:
            icon_file.write(self.ICON)
        self.root.iconbitmap(default=self.ICON_PATH)

        # 主窗口配置
        self.root.wm_title("BaiduPanFilesTransfers 2.3.2")
        self.root.wm_geometry('410x480+240+240')
        self.root.minsize(410, 480)
        self.root.wm_attributes("-alpha", 0.88)

        # 定义窗口元素
        self.entry_cookie = self.create_label_entry(1, '1.下面填入百度网盘 Cookies，不带引号：')
        self.entry_access_token = self.create_label_entry(3, '（可选）如果要转存秒存链接，下面填入百度网盘 access_token：')
        self.entry_folder_name = self.create_label_entry(5, '2.下面填入文件保存位置（默认根目录），不能包含<,>,|,*,?,,/：')
        Label(self.root, text='3.下面粘贴链接，每行一个。格式为：链接 提取码 或 秒传格式。').grid(row=7, sticky=W)
        self.text_links = self.create_text_scrollbar(8)
        self.text_logs = self.create_text_scrollbar(10)
        self.bottom_run = Button(self.root, text='4.点击运行', command=lambda: thread_it(self.main, ), width=10, height=1, relief='solid')
        self.bottom_run.grid(row=9, pady=6, sticky=W, padx=4)
        self.label_state = Label(self.root, text='使用帮助', font=('Arial', 9, 'underline'), foreground="#0000ff", cursor='heart')
        self.label_state.grid(row=9, sticky=E, padx=4)
        self.label_state.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/hxz393/BaiduPanFilesTransfers"))
        # 添加 trust_env 复选框
        self.trust_env_var = BooleanVar()
        self.trust_env_checkbutton = Checkbutton(self.root, text='使用系统代理', variable=self.trust_env_var)
        self.trust_env_checkbutton.grid(row=9, sticky=W, padx=84)

        # 读取配置
        if os.path.exists('config.ini'):
            with open('config.ini') as config_read:
                config_list = config_read.readlines()
                config_cookie = config_list[0] if config_list else ''
                config_access_token = config_list[1] if len(config_list) > 1 else ''
                config_target_directory_name = config_list[2] if len(config_list) > 2 else ''
            self.entry_cookie.insert(0, config_cookie)
            self.entry_access_token.insert(0, config_access_token)
            self.entry_folder_name.insert(0, config_target_directory_name)

    # 建立标签和输入框函数
    def create_label_entry(self, row, label_text):
        Label(self.root, text=label_text).grid(row=row, column=0, sticky=W)
        entry = Entry(self.root)
        entry.grid(row=row + 1, column=0, sticky=W + E, padx=(4, 1), pady=(5, 5))
        self.root.grid_columnconfigure(0, weight=1)
        return entry

    # 建立文本框和滚动条函数
    def create_text_scrollbar(self, row):
        text = Text(self.root, height=5, wrap=NONE)
        text.grid(row=row, column=0, sticky=W + E + N + S, padx=(4, 1), pady=(5, 5))
        scrollbar = Scrollbar(self.root, width=5)
        scrollbar.grid(row=row, column=1, sticky=S + N, rowspan=1)
        scrollbar.configure(command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        self.root.grid_rowconfigure(row, weight=1)
        return text

    # 建立状态标签变化函数
    def label_state_change(self, state, completed_task_count=0, total_task_count=0):
        self.label_state.config(font=('Arial', 9), foreground="#000000", cursor="arrow")
        self.label_state.unbind("<Button-1>")

        if state == 'error':
            self.label_state['text'] = '发生错误，错误日志如下：'
        elif state == 'running':
            self.label_state['text'] = f'下面为转存结果，进度：{completed_task_count}/{total_task_count}'

    # 获取bdstoken函数
    @retry(stop_max_attempt_number=3, wait_fixed=1000)
    def get_bdstoken(self):
        url = f'{BASE_URL}/api/gettemplatevariable?clienttype=0&app_id=38824127&web=1&fields=[%22bdstoken%22,%22token%22,%22uk%22,%22isdocuser%22,%22servertime%22]'
        response = self.session.get(url=url, headers=self.request_header, timeout=20, allow_redirects=True, verify=False)
        return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['result']['bdstoken']

    # 获取目录列表函数
    @retry(stop_max_attempt_number=5, wait_fixed=1000)
    def get_dir_list(self):
        url = f'{BASE_URL}/api/list?order=time&desc=1&showempty=0&web=1&page=1&num=1000&dir=%2F&bdstoken={self.bdstoken}'
        response = self.session.get(url=url, headers=self.request_header, timeout=15, allow_redirects=False, verify=False)
        return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['list']

    # 新建目录函数
    @retry(stop_max_attempt_number=5, wait_fixed=1000)
    def create_dir(self, target_directory_name):
        url = f'{BASE_URL}/api/create?a=commit&bdstoken={self.bdstoken}'
        post_data = {'path': target_directory_name, 'isdir': '1', 'block_list': '[]', }
        response = self.session.post(url=url, headers=self.request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
        return response.json()['errno']

    # 验证链接函数
    @retry(stop_max_attempt_number=12, wait_fixed=1700)
    def verify_links(self, link_url, pass_code):
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

    # 验证提取码函数
    @retry(stop_max_attempt_number=6, wait_fixed=1700)
    def verify_pass_code(self, link_url, pass_code):
        check_url = f'{BASE_URL}/share/verify?surl={link_url[25:48]}&bdstoken={self.bdstoken}&t={str(int(round(time.time() * 1000)))}&channel=chunlei&web=1&clienttype=0'
        post_data = {'pwd': pass_code, 'vcode': '', 'vcode_str': '', }
        response = self.session.post(url=check_url, headers=self.request_header, data=post_data, timeout=10, allow_redirects=False, verify=False)
        return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['randsk']

    # 更新 cookie 函数
    def update_cookie(self, bdclnd):
        if 'BDCLND=' in self.request_header['Cookie']:
            self.request_header['Cookie'] = re.sub(r'BDCLND=(\S+);?', f'BDCLND={bdclnd};', self.request_header['Cookie'])
        else:
            self.request_header['Cookie'] += f';BDCLND={bdclnd}'

    # 转存文件函数
    @retry(stop_max_attempt_number=9, wait_fixed=1553)
    def transfer_files(self, verify_links_reason, target_directory_name):
        url = f'{BASE_URL}/share/transfer?shareid={verify_links_reason[0]}&from={verify_links_reason[1]}&bdstoken={self.bdstoken}&channel=chunlei&web=1&clienttype=0'
        post_data = {'fsidlist': f'[{",".join(i for i in verify_links_reason[2])}]', 'path': f'/{target_directory_name}', }
        response = self.session.post(url=url, headers=self.request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
        return response.json()['errno']

    # 转存秒传链接函数
    @retry(stop_max_attempt_number=6, wait_fixed=1000)
    def transfer_files_rapid(self, rapid_data, target_directory_name):
        header = self.request_header.copy()
        header['User-Agent'] = 'netdisk;2.2.51.6;netdisk;10.0.63;PC;android-android;QTP/1.0.32.2'
        url = f'{BASE_URL}/rest/2.0/xpan/file?method=create&access_token={self.access_token}&bdstoken={self.bdstoken}'
        response_json = {'errno': None}

        for _ in range(10):
            rapid_data[0] = ''.join(random.choice([c.upper(), c.lower()]) for c in rapid_data[0])
            post_data = f'&block_list=["{rapid_data[0]}"]&path=/{quote(target_directory_name)}/{quote(rapid_data[3])}&size={rapid_data[2]}&isdir=0&rtype=2'
            response = self.session.post(url=url, headers=header, data=post_data, timeout=15, allow_redirects=False, verify=False)
            response_json = response.json()

            if response_json['errno'] in [31039]:
                rapid_data[3] += '1'
            elif response_json['errno'] not in [404, 2]:
                break
            else:
                time.sleep(0.1)

        return response_json['errno']

    # 检查状态函数
    def check_condition(self, condition, state, message):
        if condition:
            self.label_state_change(state=state)
            self.text_logs.insert(END, message + '\n')
            sys.exit()

    # 插入日志函数
    def insert_logs(self, message):
        self.text_logs.insert(END, message + '\n')

    # 处理链接函数
    def handle_file_transfer(self, url_code, target_directory_name):
        # 判断连接类型
        link_type = check_link_type(url_code)
        # 处理 https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg 123w 格式链接
        if link_type == '/s/':
            self.process_s_link(url_code, target_directory_name)
        # 处理秒传格式链接
        elif link_type == 'rapid':
            self.process_rapid_link(url_code, target_directory_name)
        elif link_type == 'unknown':
            self.insert_logs(f'不支持的链接：{url_code}')

    # 转存 /s/ 类型链接函数
    def process_s_link(self, url_code, target_directory_name):
        link_url_org, pass_code_org = re.sub(r'提取码*[：:](.*)', r'\1', url_code.lstrip()).split(' ', maxsplit=1)
        [link_url, pass_code] = [link_url_org.strip()[:47], pass_code_org.strip()[:4]]
        # 执行检查链接有效性
        verify_links_reason = self.verify_links(link_url, pass_code)
        if isinstance(verify_links_reason, list):
            # 执行转存文件
            transfer_files_reason = self.transfer_files(verify_links_reason, target_directory_name)
            self.check_transfer_files_reason(transfer_files_reason, url_code)
        elif verify_links_reason in ERROR_CODES:
            self.insert_logs(f'{ERROR_CODES[verify_links_reason]}：{url_code}')
        else:
            self.insert_logs(f'访问链接返回错误代码（{verify_links_reason}）：{url_code}')

    # 转存 rapid 类型链接函数
    def process_rapid_link(self, url_code, target_directory_name):
        rapid_data = []
        try:
            # 处理梦姬标准(4FFB5BC751CC3B7A354436F85FF865EE#797B1FFF9526F8B5759663EC0460F40E#21247774#秒传.rar)
            if url_code.count('#') > 2:
                rapid_data = url_code.split('#', maxsplit=3)
            elif url_code.count('#') == 2:
                rapid_data = url_code.split('#', maxsplit=2)
                rapid_data.insert(1, '')
            elif url_code.count('|') > 2:
                bdpan_data = url_code.split('|', maxsplit=3)
                rapid_data = [bdpan_data[2], bdpan_data[3], bdpan_data[1], bdpan_data[0]]
            elif url_code.count('|') == 2:
                bdpan_data = url_code.split('|', maxsplit=2)
                bdpan_data.insert(1, '')
                rapid_data = [bdpan_data[2], bdpan_data[3], bdpan_data[1], bdpan_data[0]]
            # 处理游侠标准(bdlink=)
            elif 'bdlink=' in url_code.lower():
                decoded_string_list = decode_with_multiple_encodings(base64.b64decode(re.findall(r'bdlink=(.+)', url_code)[0])).replace('\r\n', '\n').split('\n')
                for i in decoded_string_list:
                    self.process_rapid_link(i, target_directory_name)
                return
            # 处理PanDL标准(bdpan://)
            elif 'bdpan://' in url_code.lower():
                decoded_string_list = decode_with_multiple_encodings(base64.b64decode(re.findall(r'bdpan://(.+)', url_code)[0])).replace('\r\n', '\n').split('\n')
                for i in decoded_string_list:
                    self.process_rapid_link(i, target_directory_name)
                return
            # 处理PCS-Go标准(BaiduPCS-Go)
            elif 'baidupcs-go' in url_code.lower():
                go_md5 = re.findall(r'-md5=(\S+)', url_code)[0]
                go_md5s = re.findall(r'-slicemd5=(\S+)', url_code)[0]
                go_len = re.findall(r'-length=(\S+)', url_code)[0]
                # go_name = re.findall(r'-crc32=\d+\s(.+)', url_code)[0].replace('"', '').replace('/', '\\').strip()
                go_name = re.findall(r'"(.*)"', url_code)[0].replace('"', '').replace('/', '\\').strip()
                rapid_data = [go_md5, go_md5s, go_len, go_name]
        except Exception as e:
            self.insert_logs(f'{url_code}链接解码失败：{e}')
            return

        if rapid_data:
            # 执行转存文件
            transfer_files_reason = self.transfer_files_rapid(rapid_data, target_directory_name)
            self.check_transfer_files_reason(transfer_files_reason, url_code)
        else:
            self.check_transfer_files_reason(404, url_code)

    # 检查转存文件结果
    def check_transfer_files_reason(self, transfer_files_reason, url_code):
        if transfer_files_reason in ERROR_CODES:
            self.insert_logs(f'{ERROR_CODES[transfer_files_reason]}：{url_code}')
        else:
            self.insert_logs(f'转存失败，错误代码（{transfer_files_reason}）：{url_code}')

    # 主函数
    def main(self):
        # 获取和初始化数据
        self.text_logs.delete(1.0, END)
        cookie = "".join(self.entry_cookie.get().split())
        self.access_token = "".join(self.entry_access_token.get().split())
        target_directory_name = "".join(self.entry_folder_name.get().split())
        link_list = [sanitize_link(link + ' ') for link in self.text_links.get(1.0, END).split('\n') if link]
        self.session.trust_env = self.trust_env_var.get()
        completed_task_count = 0
        total_task_count = len(link_list)
        write_config(f'{cookie}\n{self.access_token}\n{target_directory_name}')

        self.request_header['Cookie'] = cookie
        self.bottom_run['state'] = 'disabled'
        self.bottom_run['relief'] = 'groove'
        self.bottom_run['text'] = '运行中...'

        # 开始运行函数
        try:
            # 检查链接数是否超限
            self.check_condition(total_task_count > 1000, 'error', '转存链接数一次不能超过 1000，请减少链接数。')

            # 检查 cookie 输入是否正确
            self.check_condition(any([ord(word) not in range(256) for word in cookie]) or cookie.find('BAIDUID=') == -1, 'error', '百度网盘 cookie 输入不正确，请检查 cookie 后重试。')

            # 执行获取 bdstoken
            self.bdstoken = self.get_bdstoken()
            self.check_condition(isinstance(self.bdstoken, int), 'error', f'没获取到bdstoken，错误代码：{str(self.bdstoken)}')

            # 执行获取目录列表
            dir_list_json = self.get_dir_list()
            self.check_condition(type(dir_list_json) != list, 'error', '没获取到网盘目录列表，请检查 cookie 和网络后重试。')

            # 执行新建目录
            if target_directory_name and target_directory_name not in [dir_json['server_filename'] for dir_json in dir_list_json]:
                create_dir_reason = self.create_dir(target_directory_name)
                self.check_condition(create_dir_reason != 0, 'error', '转存目录名带非法字符，请改正目录名后重试。')

            # 执行转存
            for url_code in link_list:
                self.handle_file_transfer(url_code, target_directory_name)
                completed_task_count += 1
                self.label_state_change(state='running', completed_task_count=completed_task_count, total_task_count=total_task_count)

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
    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = BaiduPanFilesTransfers()
    app.run()
