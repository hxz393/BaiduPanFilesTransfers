import base64
import tempfile
import threading
import webbrowser
import zlib
from tkinter import *

import requests
import urllib3
from retrying import retry

'''
软件名: BaiduPanFilesTransfers
版本: 1.0
更新时间: 2020.6.16
打包命令: pyinstaller -F -w -i bpftUI.ico bpftUI.py
'''

# 实例化TK
root = Tk()

# 运行时替换图标
ICON = zlib.decompress(base64.b64decode('eJxjYGAEQgEBBiDJwZDBysAgxsDAoAHEQCEGBQaIOAg4sDIgACMUj4JRMApGwQgF/ykEAFXxQRc='))
_, ICON_PATH = tempfile.mkstemp()
with open(ICON_PATH, 'wb') as icon_file:
    icon_file.write(ICON)
root.iconbitmap(default=ICON_PATH)

# 主窗口配置
root.wm_title("度盘转存 1.0 by Alice & Asu")
root.wm_geometry('350x426+240+240')
root.wm_attributes("-alpha", 0.98)
root.resizable(width=False, height=True)

# 定义标签和文本框
Label(root, text='1.下面填入百度Cookies,以BAIDUID=开头到结尾,不带引号').grid(row=1, column=0, sticky=W)
entry_cookie = Entry(root, width=48, )
entry_cookie.grid(row=2, column=0, sticky=W, padx=4)
Label(root, text='2.下面填入文件保存位置(默认根目录),不能包含<,>,|,*,?,,/').grid(row=3, column=0, sticky=W)
entry_folder_name = Entry(root, width=48, )
entry_folder_name.grid(row=4, column=0, sticky=W, padx=4)
Label(root, text='3.下面粘贴链接,每行一个,支持秒传.格式为:链接 提取码').grid(row=5, sticky=W)

# 链接输入框
text_links = Text(root, width=48, height=10, wrap=NONE)
text_links.grid(row=6, column=0, sticky=W, padx=4, )
scrollbar_links = Scrollbar(root, width=5)
scrollbar_links.grid(row=6, column=0, sticky=S + N + E, )
scrollbar_links.configure(command=text_links.yview)
text_links.configure(yscrollcommand=scrollbar_links.set)

# 日志输出框
text_logs = Text(root, width=48, height=10, wrap=NONE)
text_logs.grid(row=8, column=0, sticky=W, padx=4, )
scrollbar_logs = Scrollbar(root, width=5)
scrollbar_logs.grid(row=8, column=0, sticky=S + N + E, )
scrollbar_logs.configure(command=text_logs.yview)
text_logs.configure(yscrollcommand=scrollbar_logs.set)

# 定义按钮和状态标签
bottom_run = Button(root, text='4.点击运行', command=lambda: thread_it(main, ), width=10, height=1, relief='solid')
bottom_run.grid(row=7, pady=6, sticky=W, padx=4)
label_state = Label(root, text='点击访问项目GitHub主页', font=('Arial', 9, 'underline'), foreground="#0000ff", cursor='heart')
label_state.grid(row=7, sticky=E, padx=4)
label_state.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/hxz393/BaiduPanFilesTransfers", new=0))

# 公共请求头
request_header = {
    'Host': 'pan.baidu.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
    'Sec-Fetch-Dest': 'document',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'navigate',
    'Referer': 'https://pan.baidu.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}
urllib3.disable_warnings()


# 获取bdstoken函数
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def get_bdstoken():
    url = 'https://pan.baidu.com/disk/home'
    response = requests.get(url=url, headers=request_header, timeout=20, allow_redirects=True)
    bdstoken_list = re.findall('"bdstoken":"(\\S+?)",', response.text)
    return bdstoken_list[0] if bdstoken_list else 1


# 获取目录列表函数
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def get_dir_list(bdstoken):
    url = 'https://pan.baidu.com/api/list?order=time&desc=1&showempty=0&web=1&page=1&num=1000&dir=%2F&bdstoken=' + bdstoken
    response = requests.get(url=url, headers=request_header, timeout=15, allow_redirects=False)
    return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['list']


# 新建目录函数
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def create_dir(dir_name, bdstoken):
    url = 'https://pan.baidu.com/api/create?a=commit&bdstoken=' + bdstoken
    post_data = {'path': dir_name, 'isdir': '1', 'block_list': '[]', }
    response = requests.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False)
    return response.json()['errno']


# 修剪链接
def fix_input(link_list_line):
    if link_list_line[:24] == 'https://pan.baidu.com/s/':
        link_type = '/s/'
    elif link_list_line.count('#') == 3:
        link_type = 'rapid'
    else:
        link_type = 'unknown'
    return link_type, link_list_line


# 验证链接函数
@retry(stop_max_attempt_number=5, wait_fixed=2000)
def check_links(link_url, pass_code):
    post_data = {'pwd': pass_code, 'vcode': '', 'vcode_str': '', }
    response = requests.post(url=link_url, headers=request_header, data=post_data, timeout=15, allow_redirects=False)
    shareid_list = re.findall('"shareid":(\\S+?),"', response.text)
    oper_id_list = re.findall('"oper_id":"(\\S+?)","', response.text)
    fs_id_list = re.findall('"fs_id":(\\S+?),"', response.text)
    return [shareid_list[0], oper_id_list[0], fs_id_list[0]] if shareid_list and oper_id_list and fs_id_list else 1


# 转存文件函数
@retry(stop_max_attempt_number=200, wait_fixed=2000)
def transfer_files(check_links_reason, dir_name):
    url = 'https://pan.baidu.com/share/transfer?shareid=' + check_links_reason[0] + '&from=' + check_links_reason[1]
    post_data = {'fsidlist': '[' + check_links_reason[2] + ']', 'path': '/' + dir_name, }
    response = requests.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False)
    return response.json()['errno']


# 转存秒传链接函数
@retry(stop_max_attempt_number=100, wait_fixed=1000)
def transfer_files_rapid(rapid_data, dir_name, bdstoken):
    url = 'https://pan.baidu.com/api/rapidupload?bdstoken=' + bdstoken
    post_data = {'path': dir_name + '/' + rapid_data[3], 'content-md5': rapid_data[0], 'slice-md5': rapid_data[1],
                 'content-length': rapid_data[2]}
    response = requests.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False)
    return response.json()['errno']


# 状态标签变化函数
def label_state_change(state, task_count=0, task_total_count=0):
    label_state.unbind("<Button-1>")
    label_state['font'] = ('Arial', 9)
    label_state['foreground'] = "#000000"
    label_state['cursor'] = "arrow"
    if state == 'error':
        label_state['text'] = '发生错误,错误日志如下:'
    elif state == 'running':
        label_state['text'] = '下面为转存结果,进度:' + str(task_count) + '/' + str(task_total_count)


# 多线程
def thread_it(func, *args):
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()
    # t.join()


# 主程序
def main():
    # 获取和初始化数据
    text_logs.delete(1.0, END)
    cookie = "".join(entry_cookie.get().split())
    request_header['Cookie'] = cookie
    dir_name = entry_folder_name.get()
    dir_name = "".join(dir_name.split())
    text_input = text_links.get(1.0, END).split('\n')
    link_list = [link for link in text_input if link]
    link_list = [link + ' ' for link in link_list if link[-1] != ' ']
    task_count = 0
    task_total_count = len(link_list)
    bottom_run['state'] = 'disabled'
    bottom_run['relief'] = 'groove'
    bottom_run['text'] = '运行中...'

    # 开始运行函数
    try:
        # 检查cookie输入是否正确
        if cookie[:8] != 'BAIDUID=':
            label_state_change(state='error')
            logs = '百度网盘cookie输入不正确,请检查cookie后重试.' + '\n'
            text_logs.insert(END, logs)
            sys.exit()

        # 执行获取bdstoken
        bdstoken = get_bdstoken()
        if bdstoken == 1:
            label_state_change(state='error')
            logs = '没获取到bdstoken,请检查cookie和网络后重试.' + '\n'
            text_logs.insert(END, logs)
            sys.exit()

        # 执行获取目录列表
        dir_list_json = get_dir_list(bdstoken)
        if type(dir_list_json) != list:
            label_state_change(state='error')
            logs = '没获取到网盘目录列表,请检查cookie和网络后重试.' + '\n'
            text_logs.insert(END, logs)
            sys.exit()

        # 执行新建目录
        dir_list = [dir_json['server_filename'] for dir_json in dir_list_json]
        if dir_name and dir_name not in dir_list:
            create_dir_reason = create_dir(dir_name, bdstoken)
            if create_dir_reason != 0:
                label_state_change(state='error')
                logs = '文件夹名带非法字符,请改正文件夹名称后重试.' + '\n'
                text_logs.insert(END, logs)
                sys.exit()

        # 执行转存
        for link_list_line in link_list:
            # 处理用户输入
            link_type, link_url_and_code = fix_input(link_list_line)
            # 处理(https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg alice)格式链接
            if link_type == '/s/':
                link_url, pass_code = link_url_and_code.split(' ', maxsplit=1)
                pass_code = pass_code.strip()
                # 执行检查链接有效性
                check_links_reason = check_links(link_url, pass_code)
                if check_links_reason == 1:
                    logs = '链接失效:' + link_url_and_code + '\n'
                    text_logs.insert(END, logs)
                else:
                    # 执行转存文件
                    transfer_files_reason = transfer_files(check_links_reason, dir_name)
                    if transfer_files_reason == 12:
                        logs = '转存失败,目录中已有同名文件存在:' + link_url_and_code + '\n'
                        text_logs.insert(END, logs)
                    elif transfer_files_reason == 0:
                        logs = '转存成功:' + link_url_and_code + '\n'
                        text_logs.insert(END, logs)
                    else:
                        logs = '转存失败,错误代码(' + str(transfer_files_reason) + '):' + link_url_and_code + '\n'
                        text_logs.insert(END, logs)
            # 处理(4FFB5BC751CC3B7A354436F85FF865EE#797B1FFF9526F8B5759663EC0460F40E#21247774#秒传.rar)格式链接
            elif link_type == 'rapid':
                rapid_data = link_url_and_code.split('#')
                transfer_files_reason = transfer_files_rapid(rapid_data, dir_name, bdstoken)
                if transfer_files_reason == 0:
                    logs = '转存成功:' + link_url_and_code + '\n'
                    text_logs.insert(END, logs)
                elif transfer_files_reason == -8:
                    logs = '转存失败,目录中已有同名文件存在:' + link_url_and_code + '\n'
                    text_logs.insert(END, logs)
                elif transfer_files_reason == 404:
                    logs = '转存失败,秒传无效:' + link_url_and_code + '\n'
                    text_logs.insert(END, logs)
                elif transfer_files_reason == 2:
                    logs = '转存失败,非法路径:' + link_url_and_code + '\n'
                    text_logs.insert(END, logs)
                elif transfer_files_reason == -10:
                    logs = '转存失败,容量不足:' + link_url_and_code + '\n'
                    text_logs.insert(END, logs)
                elif transfer_files_reason == 114514:
                    logs = '转存失败,接口调用失败:' + link_url_and_code + '\n'
                    text_logs.insert(END, logs)
                else:
                    logs = '转存失败,错误代码(' + str(transfer_files_reason) + '):' + link_url_and_code + '\n'
                    text_logs.insert(END, logs)
            elif link_type == 'unknown':
                logs = '不支持链接:' + link_url_and_code + '\n'
                text_logs.insert(END, logs)
                task_count = task_count + 1
                label_state_change(state='running', task_count=task_count, task_total_count=task_total_count)
                continue
            task_count = task_count + 1
            label_state_change(state='running', task_count=task_count, task_total_count=task_total_count)
    except Exception as e:
        text_logs.insert(END, '运行出错,请重新运行本程序.错误信息如下:' + '\n')
        text_logs.insert(END, str(e) + '\n\n')
        text_logs.insert(END, '用户输入内容:' + '\n')
        text_logs.insert(END, '百度Cookies:' + cookie + '\n')
        text_logs.insert(END, '文件夹名:' + dir_name + '\n')
        text_logs.insert(END, '链接输入:' + '\n' + str(text_input))
    # 恢复按钮状态
    finally:
        bottom_run['state'] = 'normal'
        bottom_run['relief'] = 'solid'
        bottom_run['text'] = '4.点击运行'


root.mainloop()
