"""
打包命令：pyinstaller -F -w -i BaiduPanFilesTransfers.ico --hidden-import=tkinter -n BaiduPanFilesTransfers BaiduPanFilesTransfers.py

:title: BaiduPanFilesTransfers
:site: https://github.com/hxz393/BaiduPanFilesTransfers
:author: assassing
:contact: hxz393@gmail.com
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""

from src.operations import Operations
from src.ui import MainWindow


def main() -> None:
    """
    主函数，先创建主窗口实例，然后创建动作实例，更新主窗口实例中的动作对象引用，最后运行.

    :return: 无返回值
    """
    # 创建主窗口实例，先传入 None 占位
    root = MainWindow(None)
    # 创建逻辑处理对象并传递主窗口实例
    op = Operations(root)
    # 更新主窗口中的逻辑处理对象引用
    root.op = op
    root.run()


if __name__ == '__main__':
    main()
