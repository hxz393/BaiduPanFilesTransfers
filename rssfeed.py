import feedparser
from bpftUI import get_bdstoken, check_links,transfer_files, request_header,cloud_push_files,get_dir_list
import os
if not os.path.exists("saved_url.txt"):
    with open("saved_url.txt", "w+") as file:
        savedUrl = []
with open("saved_url.txt", "r") as file:
    savedUrl = file.readlines()
savedUrl1 = set(savedUrl)
from html.parser import HTMLParser
NewsFeed = feedparser.parse("https://rsshub-2xa7iyxou-diy.vercel.app/fanxinzhui")
urlKey = []
for entry in NewsFeed.entries:
    entry = entry['summary']
    start = entry.find("https://pan.baidu.com")
    end = entry[start:].find(" ")
    url = entry[start:start+end-1]
    if url+"\n" in savedUrl:
        continue
    start = entry.find("password")
    end = entry[start:].find(">") + start +1
    key = entry[end:end+4]
    urlKey.append((url, key))
with open("cookie.txt", "r") as file:
    cookie = file.readline()[:-1]
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
success_count = 0
for url, key in urlKey:
    request_header['Cookie'] = cookie
    request_header['User-Agent'] = user_agent
    bdstoken = get_bdstoken()
    if bdstoken == 1:
        print('没获取到bdstoken,请检查cookie和网络后重试.')
    url = url.replace("https://pan.baidu.com/share/init?surl=", "https://pan.baidu.com/s/1")
    check_links_reason = check_links(url, key, bdstoken)
    if check_links_reason == 1:
        print('链接失效,没获取到shareid:' + url)
    elif check_links_reason == 2:
        print('链接失效,没获取到user_id:' + url + '\n')
    elif check_links_reason == 3 or check_links_reason == -9:
        print( '链接失效,文件已经被删除或取消分享:' + url + '\n')
    elif check_links_reason == -12:
        print( '提取码错误:' + url + '\n')
    elif check_links_reason == -62:
        print( '错误尝试次数过多,请稍后再试:' + url + '\n')
    elif isinstance(check_links_reason, list):
        # 执行转存文件
        transfer_files_reason = transfer_files(check_links_reason, "", bdstoken)
        if transfer_files_reason['errno'] == 0:
            print( '转存成功:' + url + '\n')
            savedUrl.append(url +"\n")
            success_count += 1
        elif transfer_files_reason['errno'] == 12 and transfer_files_reason['info'][0]['errno'] == -30:
            print('转存失败,目录中已有同名文件存在:' + url + '\n')
        elif transfer_files_reason['errno'] == 12 and transfer_files_reason['info'][0]['errno'] == 120:
            print( '转存失败,转存文件数超过限制:' + url + '\n')
        else:
            print('转存失败,错误代码(' + str(transfer_files_reason['errno']) + '):' + url + '\n')
    else:
        print('访问链接返回错误代码(' + str(check_links_reason) + '):' + url + '\n')
with open("saved_url.txt", "w+") as file:
    if len(savedUrl) > 1000:
        savedUrl = savedUrl[-100:]
    file.write("".join(savedUrl))

request_header['Cookie'] = cookie
request_header['User-Agent'] = user_agent
bdstoken = get_bdstoken()
filelist = get_dir_list(bdstoken)[2:]
cloud_push_files(success_count, bdstoken)
