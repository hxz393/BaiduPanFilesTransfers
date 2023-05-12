import base64
import tempfile
import threading
import time
import webbrowser
import zlib
import os
import sys
import re
from tkinter import Tk, Entry, Label, Text, Scrollbar, Button, W, S, N, E, END, NONE

import requests
import urllib3
from retrying import retry

# 检测链接种类
def check_link_type(link_list_line):
    link_type = 'unknown'
    if 'https://pan.baidu.com/s/' in link_list_line:
        link_type = '/s/'
    elif re.search(r'(bdlink=|bdpan://|BaiduPCS-Go|#.*#)', link_list_line, re.IGNORECASE):
        link_type = 'rapid'
    return link_type

# 写配置文件函数
def write_config(cookie, user_agent):
    with open('config.ini', 'w') as config_write:
        config_write.write(cookie + '\n' + user_agent)

# 处理链接格式函数
def sanitize_link(url_code):
    # 处理 http 链接
    url_code = url_code.replace("http://", "https://")
    # 处理(https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg?pwd=123w)格式链接
    url_code = url_code.replace("?pwd=", " ")
    # 处理旧格式链接
    url_code = url_code.replace("https://pan.baidu.com/share/init?surl=", "https://pan.baidu.com/s/1")
    return url_code


class BaiduPanFilesTransfers:
    """
    软件名：BaiduPanFilesTransfers
    版本：1.14
    更新时间：2023.05.12
    打包命令：pyinstaller -F -w -i bpftUI.ico bpftUI.py
    """

    # 请求变量
    BASE_URL = 'https://pan.baidu.com'
    REQUEST_HEADER = {
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
    }

    def __init__(self):
        # 会话配置
        self.session = requests.Session()
        urllib3.disable_warnings()
        self.bdstoken = None
        # 设为 False 来使用 IDE 中配置的代理
        # self.session.trust_env = False

        # 实例化 TK
        self.root = Tk()

        # 运行时替换图标
        self.ICON = zlib.decompress(base64.b64decode('eJyFUw1MU1cUvjgyfa+vr++1WGw3FTKDtHVLQDPCtojLFlpKKY4pLE0EDAaEMuKyOBWmI8ZMZ5T6Ax2xpgKKCs5kGtT9KA5B/GFxAUpBES1TZ0Z0kWQZLMZ9O6+um1tIdl6+d+79vvPdd25eDmNR9EgSo3ccWx3NmJ4xlkggipinvBJLotn/RdQrsU16i9aXY5Z9HsonzNr9Jy06354F8r7cxJh6A2OImspoZq3PJ2rrckxab7dJ9k6YtJ9DgSWmHmZlLXsnTXJdz3xpr2vu3AMznvXOY7unWwyeNeX5bQ/ffesIEmQPFsZ5Ufn+t2htCqB2+xWkLzpAfA3Mes+jtxftr9y5s5uL9Byv2bLc/rrvl+vBMRS7WmCe9Rn83qu4cjGEuppOdJ0fQfeFEApyjuDYwV4MDYyNj49PrAQwbbZurXG2Zt3VLR+fppoRWOZUw/FmLYKB+7Cn7QFpSH15G3qv3cGDsV/xzZkBVBQfRklBY3+21RNnEN0uo1Qx2XLoMur3noNBLEd+bj2u9YRgiluHWLUbBk05mvydGA09wGtJ1cSVQa8ufawXi1fr1Ct9sZoifNFyCTu2nYROKET6ks0YvnEfmemfhvfz5rhxsXMIYz+P441Xq6AV8sOQVSuOSULueUnIQ13tKTT4z0JWv4cXZhXgxJeX8X3PTXz4gR8HG9sxGPwRP917CLt1E0TVsgh+UPPOCwKfjZLi3ejqCuBFowsC70RyUimOH+/E8PBddHT0ku7Bjet3YU1fDxWfFYbAZ/XxvP0QAcnJJQgEbiMjYz2UvYKYmHeQkJAPo3E5Fi9eQ2fdQ0qKm7SMMDguo43j7CU8b3ssSVnw+8/g6NF2zJy5lHTbv1BYSP+g9ybi410R7gmd8ZEo2l6i9ZDCpaa60d9/C2Vlu6BW2//2ajQONDR8hcbGr2mdGeFDKlXmAsY+maZSWSto/5sg2LFq1Q4MDIRQVLSd+l8KUcyE01mFwcFROBwb/vJaJ+nblYylhSdKp3Oqid9FmJAkB0pLPejrG0Fb2yU0N59FMDiKrVubIctOxfs7x9n2UR/yszOg1dpE0tbSGbep9ycpKWXYuNGPmppW5OVtpl6y/yD9Dumb/uv9J9KilTtRTRWh/ekdbaOUOzjOWk05KdJzJELTGfvuOcaqp5zqqUOpVTyK90+HRLty'))
        _, self.ICON_PATH = tempfile.mkstemp()
        with open(self.ICON_PATH, 'wb') as icon_file:
            icon_file.write(self.ICON)
        self.root.iconbitmap(default=self.ICON_PATH)

        # 主窗口配置
        self.root.wm_title("度盘转存 1.14 by assassing")
        self.root.wm_geometry('360x480+240+240')
        self.root.minsize(360, 480)
        self.root.wm_attributes("-alpha", 0.88)

        # 定义窗口元素
        self.entry_cookie = self.create_label_entry(1, '1.下面填入百度 Cookies，不带引号：')
        self.entry_ua = self.create_label_entry(3, '2.下面填入浏览器 User-Agent：')
        self.entry_folder_name = self.create_label_entry(5, '3.下面填入文件保存位置（默认根目录），不能包含<,>,|,*,?,,/：')
        Label(self.root, text='4.下面粘贴链接，每行一个。格式为：链接 提取码 或 秒传格式。').grid(row=7, sticky=W)
        self.text_links = self.create_text_scrollbar(8)
        self.text_logs = self.create_text_scrollbar(10)
        self.bottom_run = Button(self.root, text='5.点击运行', command=lambda: self.thread_it(self.main, ), width=10, height=1, relief='solid')
        self.bottom_run.grid(row=9, pady=6, sticky=W, padx=4)
        self.label_state = Label(self.root, text='检查新版', font=('Arial', 10, 'underline'), foreground="#0000ff", cursor='heart')
        self.label_state.grid(row=9, sticky=E, padx=4)
        self.label_state.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/hxz393/BaiduPanFilesTransfers", new=0))

        # 读取配置
        if os.path.exists('config.ini'):
            with open('config.ini') as config_read:
                config_cookie, config_user_agent = config_read.readlines()
            self.entry_cookie.insert(0, config_cookie)
            self.entry_ua.insert(0, config_user_agent.strip())

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
        scrollbar.grid(row=row, column=1, sticky=S + N, rowspan=2)
        scrollbar.configure(command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        self.root.grid_rowconfigure(row, weight=1)
        return text

    # 状态标签变化函数
    def label_state_change(self, state, task_count=0, task_total_count=0):
        self.label_state.config(font=('Arial', 9), foreground="#000000", cursor="arrow")
        self.label_state.unbind("<Button-1>")

        if state == 'error':
            self.label_state['text'] = '发生错误，错误日志如下：'
        elif state == 'running':
            self.label_state['text'] = f'下面为转存结果，进度：{task_count}/{task_total_count}'

    # 获取bdstoken函数
    @retry(stop_max_attempt_number=3, wait_fixed=1000)
    def get_bdstoken(self):
        url = f'{self.BASE_URL}/api/gettemplatevariable?clienttype=0&app_id=250528&web=1&fields=[%22bdstoken%22,%22token%22,%22uk%22,%22isdocuser%22,%22servertime%22]'
        response = self.session.get(url=url, headers=self.REQUEST_HEADER, timeout=20, allow_redirects=True, verify=False)
        if response.json()['errno'] != 0:
            return response.json()['errno']
        else:
            self.bdstoken = response.json()['result']['bdstoken']
            return self.bdstoken

    # 获取目录列表函数
    @retry(stop_max_attempt_number=5, wait_fixed=1000)
    def get_dir_list(self):
        url = f'{self.BASE_URL}/api/list?order=time&desc=1&showempty=0&web=1&page=1&num=1000&dir=%2F&bdstoken={self.bdstoken}'
        response = self.session.get(url=url, headers=self.REQUEST_HEADER, timeout=15, allow_redirects=False, verify=False)
        print(response)
        return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['list']

    # 新建目录函数
    @retry(stop_max_attempt_number=5, wait_fixed=1000)
    def create_dir(self, dir_name):
        url = f'{self.BASE_URL}/api/create?a=commit&bdstoken={self.bdstoken}'
        post_data = {'path': dir_name, 'isdir': '1', 'block_list': '[]', }
        response = self.session.post(url=url, headers=self.REQUEST_HEADER, data=post_data, timeout=15, allow_redirects=False, verify=False)
        return response.json()['errno']

    # 验证链接函数
    @retry(stop_max_attempt_number=12, wait_fixed=1700)
    def check_links(self, link_url, pass_code):
        # 验证提取码
        if pass_code:
            # 生成时间戳
            t_str = str(int(round(time.time() * 1000)))
            check_url = f'{self.BASE_URL}/share/verify?surl={link_url[25:48]}&bdstoken={self.bdstoken}&t={t_str}&channel=chunlei&web=1&clienttype=0'
            post_data = {'pwd': pass_code, 'vcode': '', 'vcode_str': '', }
            response_post = self.session.post(url=check_url, headers=self.REQUEST_HEADER, data=post_data, timeout=10, allow_redirects=False, verify=False)
            # 在 cookie 中加入 bdclnd 参数
            if response_post.json()['errno'] == 0:
                bdclnd = response_post.json()['randsk']
            else:
                return response_post.json()['errno']
            if 'BDCLND=' in self.REQUEST_HEADER['Cookie']:
                self.REQUEST_HEADER['Cookie'] = re.sub(r'BDCLND=(\S+);?', f'BDCLND={bdclnd};', self.REQUEST_HEADER['Cookie'])
            else:
                self.REQUEST_HEADER['Cookie'] += f';BDCLND={bdclnd}'
        # 获取文件信息
        response = self.session.get(url=link_url, headers=self.REQUEST_HEADER, timeout=15, allow_redirects=True, verify=False).content.decode("utf-8")
        shareid_list = re.findall('"shareid":(\\d+?),"', response)
        user_id_list = re.findall('"share_uk":"(\\d+?)","', response)
        fs_id_list = re.findall('"fs_id":(\\d+?),"', response)
        info_title_list = re.findall('<title>(.+)</title>', response)
        if not shareid_list:
            return 1
        elif not user_id_list:
            return 2
        elif not fs_id_list:
            return info_title_list[0] if info_title_list else 3
        else:
            return [shareid_list[0], user_id_list[0], fs_id_list]

    # 转存文件函数
    @retry(stop_max_attempt_number=20, wait_fixed=1853)
    def transfer_files(self, check_links_reason, dir_name):
        url = f'{self.BASE_URL}/share/transfer?shareid={check_links_reason[0]}&from={check_links_reason[1]}&bdstoken={self.bdstoken}&channel=chunlei&web=1&clienttype=0'
        fs_id = ','.join(i for i in check_links_reason[2])
        post_data = {'fsidlist': f'[{fs_id}]', 'path': f'/{dir_name}', }
        response = self.session.post(url=url, headers=self.REQUEST_HEADER, data=post_data, timeout=15, allow_redirects=False, verify=False)
        return response.json()['errno']

    # 转存秒传链接函数
    @retry(stop_max_attempt_number=10, wait_fixed=1000)
    def transfer_files_rapid(self, rapid_data, dir_name):
        user_agent = self.REQUEST_HEADER['User-Agent']
        self.REQUEST_HEADER['User-Agent'] = 'netdisk;2.2.51.6;netdisk;10.0.63;PC;android-android;QTP/1.0.32.2'
        url = f'{self.BASE_URL}/api/create&bdstoken={self.bdstoken}'
        # post_data = {'path': dir_name + '/' + rapid_data[3], 'content-md5': rapid_data[0], 'slice-md5': rapid_data[1], 'content-length': rapid_data[2]}
        post_data = f'&block_list=["{rapid_data[0]}"]&path=/{dir_name.replace("&","%26")}/{rapid_data[3].replace("&","%26")}&size={rapid_data[2]}&isdir=0&rtype=0'
        response = self.session.post(url=url, headers=self.REQUEST_HEADER, data=post_data.encode("utf-8"), timeout=15, allow_redirects=False, verify=False)
        if response.json()['errno'] == 404:
            post_data = f'&block_list=["{rapid_data[0].lower()}"]&path=/{dir_name.replace("&", "%26")}/{rapid_data[3].replace("&", "%26")}&size={rapid_data[2]}&isdir=0&rtype=0'
            response = self.session.post(url=url, headers=self.REQUEST_HEADER, data=post_data, timeout=15, allow_redirects=False, verify=False)
        elif response.json()['errno'] == 2:
            time.sleep(1)
            return self.transfer_files_rapid(rapid_data, dir_name)
        self.REQUEST_HEADER['User-Agent'] = user_agent
        return response.json()['errno']

    def main(self):
        # 获取和初始化数据
        self.text_logs.delete(1.0, END)
        dir_name = "".join(self.entry_folder_name.get().split())
        cookie = "".join(self.entry_cookie.get().split())
        self.REQUEST_HEADER['Cookie'] = cookie
        user_agent = self.entry_ua.get()
        self.REQUEST_HEADER['User-Agent'] = user_agent
        write_config(cookie, user_agent)
        text_input = self.text_links.get(1.0, END).split('\n')
        link_list = [sanitize_link(link + ' ') for link in text_input if link]
        task_count = 0
        task_total_count = len(link_list)
        self.bottom_run['state'] = 'disabled'
        self.bottom_run['relief'] = 'groove'
        self.bottom_run['text'] = '运行中...'

        # 开始运行函数
        try:
            # 检查 cookie 输入是否正确
            if any([ord(word) not in range(256) for word in cookie]) or cookie.find('BAIDUID=') == -1:
                self.label_state_change(state='error')
                self.text_logs.insert(END, '百度网盘 cookie 输入不正确，请检查 cookie 后重试。' + '\n')
                sys.exit()

            # 执行获取 bdstoken
            self.bdstoken = self.get_bdstoken()
            if isinstance(self.bdstoken, int):
                self.label_state_change(state='error')
                self.text_logs.insert(END, '没获取到bdstoken，错误代码：' + str(self.bdstoken) + '\n')
                sys.exit()

            # 执行获取目录列表
            dir_list_json = self.get_dir_list()
            if type(dir_list_json) != list:
                self.label_state_change(state='error')
                self.text_logs.insert(END, '没获取到网盘目录列表，请检查cookie和网络后重试。' + '\n')
                sys.exit()

            # 执行新建目录
            dir_list = [dir_json['server_filename'] for dir_json in dir_list_json]
            if dir_name and dir_name not in dir_list:
                create_dir_reason = self.create_dir(dir_name)
                if create_dir_reason != 0:
                    self.label_state_change(state='error')
                    self.text_logs.insert(END, '文件夹名带非法字符，请改正文件夹名称后重试。' + '\n')
                    sys.exit()

            # 执行转存
            for url_code in link_list:
                # 判断连接类型
                link_type = check_link_type(url_code)

                # 处理(https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg 123w)格式链接
                if link_type == '/s/':
                    link_url_org, pass_code_org = re.sub(r'提取码*[：:](.*)', r'\1', url_code.lstrip()).split(' ', maxsplit=1)
                    [link_url, pass_code] = [link_url_org.strip()[:47], pass_code_org.strip()[:4]]
                    # 执行检查链接有效性
                    check_links_reason = self.check_links(link_url, pass_code)
                    if check_links_reason == 1:
                        self.text_logs.insert(END, '链接失效，没获取到 shareid：' + url_code + '\n')
                    elif check_links_reason == 2:
                        self.text_logs.insert(END, '链接失效，没获取到 user_id：' + url_code + '\n')
                    elif check_links_reason == 3:
                        self.text_logs.insert(END, '链接失效，没获取到 fs_id：' + url_code + '\n')
                    elif check_links_reason == '百度网盘-链接不存在':
                        self.text_logs.insert(END, '链接失效，文件已经被删除或取消分享：' + url_code + '\n')
                    elif check_links_reason == '百度网盘 请输入提取码':
                        self.text_logs.insert(END, '链接错误，缺少提取码：' + url_code + '\n')
                    elif check_links_reason == -9:
                        self.text_logs.insert(END, '链接错误，提取码错误：' + url_code + '\n')
                    elif check_links_reason == -62:
                        self.text_logs.insert(END, '链接错误尝试次数过多，请手动转存或稍后再试：' + url_code + '\n')
                    elif check_links_reason == 105:
                        self.text_logs.insert(END, '链接错误，链接格式不正确：' + url_code + '\n')
                    elif isinstance(check_links_reason, list):
                        # 执行转存文件
                        transfer_files_reason = self.transfer_files(check_links_reason, dir_name)
                        if transfer_files_reason == 0:
                            self.text_logs.insert(END, '转存成功：' + url_code + '\n')
                        elif transfer_files_reason == -4:
                            self.text_logs.insert(END, '转存失败，无效登录。请退出账号在其他地方的登录：' + url_code + '\n')
                        elif transfer_files_reason == 4 or transfer_files_reason == -8:
                            self.text_logs.insert(END, '转存失败，目录中已有同名文件或文件夹存在：' + url_code + '\n')
                        elif transfer_files_reason == 12:
                            self.text_logs.insert(END, '转存失败，转存文件数超过限制：' + url_code + '\n')
                        else:
                            self.text_logs.insert(END, '转存失败，错误代码（' + str(transfer_files_reason) + '）：' + url_code + '\n')
                    else:
                        self.text_logs.insert(END, '访问链接返回错误代码（' + str(check_links_reason) + '）：' + url_code + '\n')
                # 处理秒传格式链接
                elif link_type == 'rapid':
                    # 处理梦姬标准(4FFB5BC751CC3B7A354436F85FF865EE#797B1FFF9526F8B5759663EC0460F40E#21247774#秒传.rar)
                    if url_code.count('#') > 2:
                        rapid_data = url_code.split('#', maxsplit=3)
                    elif url_code.count('#') == 2:
                        rapid_data = url_code.split('#', maxsplit=2)
                        rapid_data.insert(1, '')
                    # 处理游侠 v1标准(bdlink=)
                    elif bool(re.search('bdlink=', url_code, re.IGNORECASE)):
                        rapid_data = base64.b64decode(re.findall(r'bdlink=(.+)', url_code)[0]).decode("utf-8").strip().split('#', maxsplit=3)
                    # 处理PanDL标准(bdpan://)
                    elif bool(re.search('bdpan://', url_code, re.IGNORECASE)):
                        bdpan_data = base64.b64decode(re.findall(r'bdpan://(.+)', url_code)[0]).decode("utf-8").strip().split('|')
                        rapid_data = [bdpan_data[2], bdpan_data[3], bdpan_data[1], bdpan_data[0]]
                    # 处理PCS-Go标准(BaiduPCS-Go)
                    elif bool(re.search('BaiduPCS-Go', url_code, re.IGNORECASE)):
                        go_md5 = re.findall(r'-md5=(\S+)', url_code)[0]
                        go_md5s = re.findall(r'-slicemd5=(\S+)', url_code)[0]
                        go_len = re.findall(r'-length=(\S+)', url_code)[0]
                        # go_name = re.findall(r'-crc32=\d+\s(.+)', url_code)[0].replace('"', '').replace('/', '\\').strip()
                        go_name = re.findall(r'"(.*)"', url_code)[0].replace('"', '').replace('/', '\\').strip()
                        rapid_data = [go_md5, go_md5s, go_len, go_name]
                    else:
                        rapid_data = []
                    transfer_files_reason = self.transfer_files_rapid(rapid_data, dir_name)
                    if transfer_files_reason == 0:
                        self.text_logs.insert(END, '转存成功：' + url_code + '\n')
                    elif transfer_files_reason == -8:
                        self.text_logs.insert(END, '转存失败，目录中已有同名文件或文件夹存在：' + url_code + '\n')
                    elif transfer_files_reason == -9:
                        self.text_logs.insert(END, '验证已过期，请重新获取 cookie：' + url_code + '\n')
                    elif transfer_files_reason == 404:
                        self.text_logs.insert(END, '转存失败，秒传无效：' + url_code + '\n')
                    elif transfer_files_reason == -10:
                        self.text_logs.insert(END, '转存失败，容量不足：' + url_code + '\n')
                    elif transfer_files_reason == 2:
                        self.text_logs.insert(END, '转存失败，请重试：' + url_code + '\n')
                    else:
                        self.text_logs.insert(END, '转存失败，错误代码（' + str(transfer_files_reason) + '）：' + url_code + '\n')
                elif link_type == 'unknown':
                    self.text_logs.insert(END, '不支持链接:' + url_code + '\n')

            task_count = task_count + 1
            self.label_state_change(state='running', task_count=task_count, task_total_count=task_total_count)
        except Exception as e:
            self.text_logs.insert(END, '运行出错，请重新运行本程序。错误信息如下：' + '\n')
            self.text_logs.insert(END, str(e) + '\n\n')
            for link in link_list:
                self.text_logs.insert(END, link + '\n')
            self.label_state_change(state='error')

        # 恢复按钮状态
        finally:
            self.bottom_run['state'] = 'normal'
            self.bottom_run['relief'] = 'solid'
            self.bottom_run['text'] = '4.点击运行'

    # 定义多线程运行主函数
    def thread_it(self, func, *args):
        t = threading.Thread(target=func, args=args)
        t.start()

    # 启动Tkinter
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = BaiduPanFilesTransfers()
    app.run()