import base64
import tempfile
import threading
import webbrowser
import zlib
import os
# noinspection PyCompatibility
from tkinter import *

import requests
import urllib3
from retrying import retry

'''
软件名: BaiduPanFilesTransfers
版本: 1.7
更新时间: 2020.11.01
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
root.wm_title("度盘转存 1.7 by Alice & Asu")
root.wm_geometry('350x473+240+240')
root.wm_attributes("-alpha", 0.9)
root.resizable(width=False, height=False)

# 定义标签和文本框
Label(root, text='1.下面填入百度Cookies,以BAIDUID=开头到结尾,不带引号').grid(row=1, column=0, sticky=W)
entry_cookie = Entry(root, width=48, )
entry_cookie.grid(row=2, column=0, sticky=W, padx=4)
Label(root, text='2.下面填入浏览器User-Agent').grid(row=3, column=0, sticky=W)
entry_ua = Entry(root, width=48, )
entry_ua.grid(row=4, column=0, sticky=W, padx=4)
Label(root, text='3.下面填入文件保存位置(默认根目录),不能包含<,>,|,*,?,,/').grid(row=5, column=0, sticky=W)
entry_folder_name = Entry(root, width=48, )
entry_folder_name.grid(row=6, column=0, sticky=W, padx=4)
Label(root, text='4.下面粘贴链接,每行一个,支持秒传.格式为:链接 提取码').grid(row=7, sticky=W)

# 链接输入框
text_links = Text(root, width=48, height=10, wrap=NONE)
text_links.grid(row=8, column=0, sticky=W, padx=4, )
scrollbar_links = Scrollbar(root, width=5)
scrollbar_links.grid(row=8, column=0, sticky=S + N + E, )
scrollbar_links.configure(command=text_links.yview)
text_links.configure(yscrollcommand=scrollbar_links.set)

# 日志输出框
text_logs = Text(root, width=48, height=10, wrap=NONE)
text_logs.grid(row=10, column=0, sticky=W, padx=4, )
scrollbar_logs = Scrollbar(root, width=5)
scrollbar_logs.grid(row=10, column=0, sticky=S + N + E, )
scrollbar_logs.configure(command=text_logs.yview)
text_logs.configure(yscrollcommand=scrollbar_logs.set)

# 定义按钮和状态标签
bottom_run = Button(root, text='4.点击运行', command=lambda: thread_it(main, ), width=10, height=1, relief='solid')
bottom_run.grid(row=9, pady=6, sticky=W, padx=4)
label_state = Label(root, text='检查更新', font=('Arial', 9, 'underline'), foreground="#0000ff", cursor='heart')
label_state.grid(row=9, sticky=E, padx=4)
label_state.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/hxz393/BaiduPanFilesTransfers", new=0))

# 读取配置
if os.path.exists('config.ini'):
    with open('config.ini') as config_read:
        [config_cookie, config_user_agent] = config_read.readlines()
    entry_cookie.insert(0, config_cookie)
    entry_ua.insert(0, config_user_agent)

# 公共请求头
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
    'Accept-Language': 'zh-CN,zh;q=0.9',
}
urllib3.disable_warnings()
s = requests.session()


# 获取bdstoken函数
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def get_bdstoken():
    """
    Returns a list of all bstoken.

    Args:
    """
    url = 'https://pan.baidu.com/disk/home'
    response = s.get(url=url, headers=request_header, timeout=20, allow_redirects=True, verify=False)
    bdstoken_list = re.findall("'bdstoken',\\s'(\\S+?)'", response.text)
    return bdstoken_list[0] if bdstoken_list else 1


# 获取目录列表函数
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def get_dir_list(bdstoken):
    """
    Retrieve a list of directories in a directory.

    Args:
        bdstoken: (str): write your description
    """
    url = 'https://pan.baidu.com/api/list?order=time&desc=1&showempty=0&web=1&page=1&num=1000&dir=%2F&bdstoken=' + bdstoken
    response = s.get(url=url, headers=request_header, timeout=15, allow_redirects=False, verify=False)
    return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['list']


# 新建目录函数
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def create_dir(dir_name, bdstoken):
    """
    Create a directory.

    Args:
        dir_name: (str): write your description
        bdstoken: (str): write your description
    """
    url = 'https://pan.baidu.com/api/create?a=commit&bdstoken=' + bdstoken
    post_data = {'path': dir_name, 'isdir': '1', 'block_list': '[]', }
    response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
    return response.json()['errno']


# 检测链接种类
def check_link_type(link_list_line):
    """
    Check if link_list_line_line_line_line is valid

    Args:
        link_list_line: (list): write your description
    """
    if link_list_line.find('https://pan.baidu.com/s/') >= 0:
        link_type = '/s/'
    elif bool(re.search('(bdlink=|bdpan://|BaiduPCS-Go)', link_list_line, re.IGNORECASE)):
        link_type = 'rapid'
    elif link_list_line.count('#') > 2:
        link_type = 'rapid'
    else:
        link_type = 'unknown'
    return link_type


# 验证链接函数
@retry(stop_max_attempt_number=20, wait_fixed=2000)
def check_links(link_url, pass_code, bdstoken):
    """
    Check link links.

    Args:
        link_url: (str): write your description
        pass_code: (str): write your description
        bdstoken: (str): write your description
    """
    # 验证提取码
    if pass_code:
        check_url = 'https://pan.baidu.com/share/verify?surl=' + link_url[25:48] + '&bdstoken=' + bdstoken
        post_data = {'pwd': pass_code, 'vcode': '', 'vcode_str': '', }
        response_post = s.post(url=check_url, headers=request_header, data=post_data, timeout=10, allow_redirects=False,
                               verify=False)
        # 在cookie中加入bdclnd参数
        if response_post.json()['errno'] == 0:
            bdclnd = response_post.json()['randsk']
            request_header['Cookie'] = re.sub(r'BDCLND=(\S+?);', r'BDCLND=' + bdclnd + ';', request_header['Cookie'])
            # request_header['Cookie'] += '; BDCLND=' + bdclnd
        else:
            return response_post.json()['errno']
    # 获取文件信息
    response = s.get(url=link_url, headers=request_header, timeout=15, allow_redirects=True,
                     verify=False).content.decode("utf-8")
    shareid_list = re.findall('"shareid":(\\d+?),"', response)
    user_id_list = re.findall('"uk":(\\d+?),"', response)
    fs_id_list = re.findall('"fs_id":(\\d+?),"', response)
    if not shareid_list:
        return 1
    elif not user_id_list:
        return 2
    elif not fs_id_list:
        return 3
    else:
        return [shareid_list[0], user_id_list[0], fs_id_list]


# 转存文件函数
@retry(stop_max_attempt_number=200, wait_fixed=2000)
def transfer_files(check_links_reason, dir_name, bdstoken):
    """
    Transfer link files.

    Args:
        check_links_reason: (bool): write your description
        dir_name: (str): write your description
        bdstoken: (str): write your description
    """
    url = 'https://pan.baidu.com/share/transfer?shareid=' + check_links_reason[0] + '&from=' + check_links_reason[
        1] + '&bdstoken=' + bdstoken
    fs_id = ','.join(i for i in check_links_reason[2])
    post_data = {'fsidlist': '[' + fs_id + ']', 'path': '/' + dir_name, }
    response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False,
                      verify=False)
    return response.json()


# 转存秒传链接函数
@retry(stop_max_attempt_number=100, wait_fixed=1000)
def transfer_files_rapid(rapid_data, dir_name, bdstoken):
    """
    Transfer files to a new recording

    Args:
        rapid_data: (todo): write your description
        dir_name: (str): write your description
        bdstoken: (str): write your description
    """
    url = 'https://pan.baidu.com/api/rapidupload?bdstoken=' + bdstoken
    post_data = {'path': dir_name + '/' + rapid_data[3], 'content-md5': rapid_data[0],
                 'slice-md5': rapid_data[1], 'content-length': rapid_data[2]}
    response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
    if response.json()['errno'] == 404:
        post_data = {'path': dir_name + '/' + rapid_data[3], 'content-md5': rapid_data[0].lower(),
                     'slice-md5': rapid_data[1].lower(), 'content-length': rapid_data[2]}
        response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False,
                          verify=False)
    return response.json()['errno']


# 状态标签变化函数
def label_state_change(state, task_count=0, task_total_count=0):
    """
    Label a task label

    Args:
        state: (todo): write your description
        task_count: (int): write your description
        task_total_count: (int): write your description
    """
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
    """
    Run a new thread.

    Args:
        func: (todo): write your description
    """
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()
    # t.join()


# 主程序
def main():
    """
    Main entry point.

    Args:
    """
    # 获取和初始化数据
    text_logs.delete(1.0, END)
    dir_name = "".join(entry_folder_name.get().split())
    cookie = "".join(entry_cookie.get().split())
    request_header['Cookie'] = cookie
    user_agent = entry_ua.get()
    request_header['User-Agent'] = user_agent
    with open('config.ini', 'w') as config_write:
        config_write.write(cookie + '\n' + user_agent)
    text_input = text_links.get(1.0, END).split('\n')
    link_list = [link for link in text_input if link]
    link_list = [link + ' ' for link in link_list]
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
            text_logs.insert(END, '百度网盘cookie输入不正确,请检查cookie后重试.' + '\n')
            sys.exit()

        # 执行获取bdstoken
        bdstoken = get_bdstoken()
        if bdstoken == 1:
            label_state_change(state='error')
            text_logs.insert(END, '没获取到bdstoken,请检查cookie和网络后重试.' + '\n')
            sys.exit()

        # 执行获取目录列表
        dir_list_json = get_dir_list(bdstoken)
        if type(dir_list_json) != list:
            label_state_change(state='error')
            text_logs.insert(END, '没获取到网盘目录列表,请检查cookie和网络后重试.' + '\n')
            sys.exit()

        # 执行新建目录
        dir_list = [dir_json['server_filename'] for dir_json in dir_list_json]
        if dir_name and dir_name not in dir_list:
            create_dir_reason = create_dir(dir_name, bdstoken)
            if create_dir_reason != 0:
                label_state_change(state='error')
                text_logs.insert(END, '文件夹名带非法字符,请改正文件夹名称后重试.' + '\n')
                sys.exit()

        # 执行转存
        for url_code in link_list:
            # 处理用户输入
            link_type = check_link_type(url_code)
            # 处理(https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg lice)格式链接
            if link_type == '/s/':
                link_url, pass_code = re.sub(r'提取码*[：:](.*)', r'\1', url_code.lstrip()).split(' ', maxsplit=1)
                pass_code = pass_code.strip()[:4]
                # 执行检查链接有效性
                check_links_reason = check_links(link_url, pass_code, bdstoken)
                if check_links_reason == 1:
                    text_logs.insert(END, '链接失效,没获取到shareid:' + url_code + '\n')
                elif check_links_reason == 2:
                    text_logs.insert(END, '链接失效,没获取到user_id:' + url_code + '\n')
                elif check_links_reason == 3 or check_links_reason == -9:
                    text_logs.insert(END, '链接失效,文件已经被删除或取消分享:' + url_code + '\n')
                elif check_links_reason == -12:
                    text_logs.insert(END, '提取码错误:' + url_code + '\n')
                elif check_links_reason == -62:
                    text_logs.insert(END, '错误尝试次数过多,请稍后再试:' + url_code + '\n')
                elif isinstance(check_links_reason, list):
                    # 执行转存文件
                    transfer_files_reason = transfer_files(check_links_reason, dir_name, bdstoken)
                    if transfer_files_reason['errno'] == 0:
                        text_logs.insert(END, '转存成功:' + url_code + '\n')
                    elif transfer_files_reason['errno'] == 12 and transfer_files_reason['info'][0]['errno'] == -30:
                        text_logs.insert(END, '转存失败,目录中已有同名文件存在:' + url_code + '\n')
                    elif transfer_files_reason['errno'] == 12 and transfer_files_reason['info'][0]['errno'] == 120:
                        text_logs.insert(END, '转存失败,转存文件数超过限制:' + url_code + '\n')
                    else:
                        text_logs.insert(END,
                                         '转存失败,错误代码(' + str(transfer_files_reason['errno']) + '):' + url_code + '\n')
                else:
                    text_logs.insert(END, '访问链接返回错误代码(' + str(check_links_reason) + '):' + url_code + '\n')
            # 处理秒传格式链接
            elif link_type == 'rapid':
                # 处理梦姬标准(4FFB5BC751CC3B7A354436F85FF865EE#797B1FFF9526F8B5759663EC0460F40E#21247774#秒传.rar)
                if url_code.count('#') > 2:
                    rapid_data = url_code.split('#', maxsplit=3)
                # 处理游侠 v1标准(bdlink=)
                elif bool(re.search('bdlink=', url_code, re.IGNORECASE)):
                    rapid_data = base64.b64decode(re.findall(r'bdlink=(.+)', url_code)[0]).decode(
                        "utf-8").strip().split('#', maxsplit=3)
                # 处理PanDL标准(bdpan://)
                elif bool(re.search('bdpan://', url_code, re.IGNORECASE)):
                    bdpan_data = base64.b64decode(re.findall(r'bdpan://(.+)', url_code)[0]).decode(
                        "utf-8").strip().split('|')
                    rapid_data = [bdpan_data[2], bdpan_data[3], bdpan_data[1], bdpan_data[0]]
                # 处理PCS-Go标准(BaiduPCS-Go)
                elif bool(re.search('BaiduPCS-Go', url_code, re.IGNORECASE)):
                    go_md5 = re.findall(r'-md5=(\S+)', url_code)[0]
                    go_md5s = re.findall(r'-slicemd5=(\S+)', url_code)[0]
                    go_len = re.findall(r'-length=(\S+)', url_code)[0]
                    go_name = re.findall(r'-crc32=\d+\s(.+)', url_code)[0].replace('"', '').replace('/', '\\').strip()
                    rapid_data = [go_md5, go_md5s, go_len, go_name]
                else:
                    rapid_data = []
                transfer_files_reason = transfer_files_rapid(rapid_data, dir_name, bdstoken)
                if transfer_files_reason == 0:
                    text_logs.insert(END, '转存成功:' + url_code + '\n')
                elif transfer_files_reason == -8:
                    text_logs.insert(END, '转存失败,目录中已有同名文件存在:' + url_code + '\n')
                elif transfer_files_reason == 404:
                    text_logs.insert(END, '转存失败,秒传无效:' + url_code + '\n')
                elif transfer_files_reason == 2:
                    text_logs.insert(END, '转存失败,非法路径:' + url_code + '\n')
                elif transfer_files_reason == -7:
                    text_logs.insert(END, '转存失败,非法文件名:' + url_code + '\n')
                elif transfer_files_reason == -10:
                    text_logs.insert(END, '转存失败,容量不足:' + url_code + '\n')
                elif transfer_files_reason == 114514:
                    text_logs.insert(END, '转存失败,接口调用失败:' + url_code + '\n')
                else:
                    text_logs.insert(END, '转存失败,错误代码(' + str(transfer_files_reason) + '):' + url_code + '\n')
            elif link_type == 'unknown':
                text_logs.insert(END, '不支持链接:' + url_code + '\n')
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
