"""
一些简单测试
"""

import pytest

from src.utils import *


@pytest.mark.parametrize("url_code, expected", [
    # 原样返回正常没有提取码的链接
    ("https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg ", "https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg "),
    # 原样返回正常有提取码的链接
    ("https://pan.baidu.com/s/1jeDvKgas8-xUss7BUFpifQ uftv ", "https://pan.baidu.com/s/1jeDvKgas8-xUss7BUFpifQ uftv "),
    # 原样返回企业版链接
    ("https://pan.baidu.com/e/1X5j-baPwZHmcXioKQPxb_w rsyf ", "https://pan.baidu.com/e/1X5j-baPwZHmcXioKQPxb_w rsyf "),
    # 测试替换 ?pwd= 为空格
    ("https://pan.baidu.com/s/1gFqh-WGW2LdNqKpHbwtZ9Q?pwd=1234 ", "https://pan.baidu.com/s/1gFqh-WGW2LdNqKpHbwtZ9Q 1234 "),
    # 测试替换 share/init?surl= 为 s/1
    ("https://pan.baidu.com/share/init?surl=7M-O0-SskRPdoZ0emZrd5w&pwd=1234 ", "https://pan.baidu.com/s/17M-O0-SskRPdoZ0emZrd5w 1234 "),
    # 测试替换开头 http 为 https
    ("http://pan.baidu.com/s/1_evfkiTrEZvOkC2hb-NiKw ju9a ", "https://pan.baidu.com/s/1_evfkiTrEZvOkC2hb-NiKw ju9a "),
    # 测试替换开头 http 为 https，包含多个 http
    ("http://pan.baidu.com/s/1_evfkiTrEZvOkC2hb-http http ", "https://pan.baidu.com/s/1_evfkiTrEZvOkC2hb-http http "),
    # 测试替换 提取码： 为空格
    ("https://pan.baidu.com/s/1kO3Yp3Q-opIFuY7GRPtd2A 提取码：qm3h ", "https://pan.baidu.com/s/1kO3Yp3Q-opIFuY7GRPtd2A qm3h "),
    # 测试替换 提取码: 为空格
    ("https://pan.baidu.com/s/1kO3Yp3Q-opIFuY7GRPtd2A 提取码: qm3h ", "https://pan.baidu.com/s/1kO3Yp3Q-opIFuY7GRPtd2A qm3h "),
    # 测试替换 提取: 为空格
    ("https://pan.baidu.com/s/1kO3Yp3Q-opIFuY7GRPtd2A 提取: qm3h ", "https://pan.baidu.com/s/1kO3Yp3Q-opIFuY7GRPtd2A qm3h "),
    # 测试替换 提取： 为空格
    ("https://pan.baidu.com/s/1kO3Yp3Q-opIFuY7GRPtd2A 提取： qm3h ", "https://pan.baidu.com/s/1kO3Yp3Q-opIFuY7GRPtd2A qm3h "),
    # 测试删除链接开头多余文字
    ("文件名 https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA fm9k ", "https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA fm9k "),
    # 测试删除链接开头多余文字，没有空格
    ("文件名https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA fm9k ", "https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA fm9k "),
    # 测试保留有效链接之后的无用文字
    ("https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA?pwd=abcd efgh ", "https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA abcd efgh "),
    # 综合测试
    ("1中文4abhttp://pan.baidu.com/share/init?surl=82A8FJ02gCq1MWYyrm_emA?pwd=abcd 提取码: efgh ", "https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA abcd efgh "),
])
def test_normalize_link(url_code, expected):
    """测试正则表达式清洗输入链接"""
    assert normalize_link(url_code) == expected


@pytest.mark.parametrize("url_code, expected", [
    # 正常链接
    ("https://pan.baidu.com/s/1o8_qk1W4c7y8sXyJ4ZnWfQ A1B2 ", ("https://pan.baidu.com/s/1o8_qk1W4c7y8sXyJ4ZnWfQ", "A1B2")),
    # 空白提取码
    ("https://pan.baidu.com/s/1o8_qk1W4c7y8sXyJ4ZnWfQ ", ("https://pan.baidu.com/s/1o8_qk1W4c7y8sXyJ4ZnWfQ", "")),
    # 链接带多个空格，取到错误提取码
    ("https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA abcd 解压密码为：5201314 ", ("https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA", "1314")),
    # 链接错误，长度过长
    ("https://pan.baidu.com/s/1o8_qk1W4c7y8sXyJ4ZnWfQA1B2 A1B2 ", ("https://pan.baidu.com/s/1o8_qk1W4c7y8sXyJ4ZnWfQ", "A1B2")),
    # 链接错误，长度过短
    ("https://pan.baidu.com/s/1o8_qk1W4c7y8s A1B2 ", ("https://pan.baidu.com/s/1o8_qk1W4c7y8s", "A1B2")),
    # 提取码错误，超过4位
    ("https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA 12345 ", ("https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA", "2345")),
    # 提取码错误，不足4位
    ("https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA 123 ", ("https://pan.baidu.com/s/182A8FJ02gCq1MWYyrm_emA", "123")),
])
def test_parse_url_and_code(url_code, expected):
    """测试把链接分割为 URL 和提取码"""
    assert parse_url_and_code(url_code) == expected


@pytest.mark.parametrize("response, expected", [
    # 测试包含所有必需参数的情况
    ('"shareid":12345,"share_uk":"67890","fs_id":111,"code":---091,"fs_id":222,"', ["12345", "67890", ["111", "222"]]),
    # 测试缺少一个参数的情况
    ('"shareid":12345,"fs_id":111,"fs_id":222,"', -1),
    # 测试没有任何参数的情况
    ('"some_other_data":100,"another_field":200,"', -1),
    # 测试包含额外字符的情况
    ('some random data "shareid":12345,"share_uk":"67890","fs_id":111,""more random data "code":---091,"fs_id":222," end of response', ["12345", "67890", ["111", "222"]]),
    # 测试空字符串的情况
    ('', -1)
])
def test_parse_response(response, expected):
    assert parse_response(response) == expected


@pytest.mark.parametrize("bdclnd, cookie, expected", [
    # 测试添加 BDCLND 到 cookie 字符串
    ("newBDCLNDvalue", "SL=0:NR=10:FG=1;csrfToken=CJgzy", "SL=0:NR=10:FG=1;csrfToken=CJgzy;BDCLND=newBDCLNDvalue"),
    # 测试更新已存在的 BDCLND 值
    ("updatedBDCLNDvalue", "SL=0:NR=10:FG=1;csrfToken=CJgzy;BDCLND=oldBDCLNDvalue;SID=12345", "SL=0:NR=10:FG=1;csrfToken=CJgzy;BDCLND=updatedBDCLNDvalue;SID=12345"),
    # 测试不正确的 cookie 字符串
    ("anotherBDCLND", "110085_287281_287977", "ValueError")
])
def test_update_cookie(bdclnd, cookie, expected):
    assert update_cookie(bdclnd, cookie) == expected
