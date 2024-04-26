"""
把 UI 相关类集中在一起。

:author: assassing
:contact: https://github.com/hxz393
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""

import atexit
import base64
import os
import re
import sys
import tempfile
import time
import traceback
import webbrowser
import zlib
from typing import Union, Tuple, Callable

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from src.constants import COLOR_THEME, LABEL_MAP, EXP_MAP, MW_PADDING
from src.network import Network
from src.utils import thread_it, write_config, read_config


class CustomDialog(ttk.Toplevel):
    """弹出对话框，用于设置分享链接参数"""

    def __init__(self, parent):
        super().__init__(parent)
        self.style.theme_use(COLOR_THEME)
        self.place_window_center()
        self.title(LABEL_MAP['settings_title'])
        self.resizable(width=False, height=False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self._create_widgets()
        self.wait_window(self)

    # noinspection PyArgumentList
    def _create_widgets(self) -> None:
        """创建控件元素"""
        master = ttk.Frame(self)
        master.pack(padx=10, pady=10, fill="both", expand=True)
        # 有效期下拉选择框
        self.var_expiry = ttk.StringVar(self, value=list(EXP_MAP.keys())[-1])
        ttk.Label(master, text=LABEL_MAP['expiry_title']).grid(row=0, column=0, sticky='e')
        ttk.Combobox(master, textvariable=self.var_expiry, values=list(EXP_MAP.keys()), state="readonly", bootstyle='primary').grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        # 提取码输入框
        self.var_password = ttk.StringVar(self, value="1234")
        ttk.Label(master, text=LABEL_MAP['password_title']).grid(row=1, column=0, sticky='e')
        ttk.Entry(master, textvariable=self.var_password, bootstyle="info").grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        # 在两个 frame 之间插入分割线
        ttk.Separator(self, orient='horizontal').pack(fill="x")
        # 底部按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text=LABEL_MAP['ok'], command=self._validate, bootstyle='primary').pack(side='right', padx=5)
        ttk.Button(button_frame, text=LABEL_MAP['cancel'], command=self.destroy, bootstyle='danger').pack(side='right', padx=5)

    def _validate(self) -> bool:
        """验证输入提取码有效性"""
        if not re.match("^[a-zA-Z0-9]{4}$", self.var_password.get()):
            Messagebox.show_warning(title=LABEL_MAP['validate_title'], message=LABEL_MAP['validate_msg'], master=self)
            return False
        self.result = (self.var_expiry.get(), self.var_password.get())
        self.destroy()
        return True


class ToolTip(object):
    """手动实现提示气泡"""

    def __init__(self, widget, text: str = ''):
        self.widget = widget
        self.text = text
        self.tips = None
        self.tooltip_id = None
        self.tooltip_color = '#ffffe0'
        self.x = self.y = 0
        self._binding()

    def _binding(self) -> None:
        """配置鼠标绑定事件"""
        self.widget.bind("<Enter>", self._enter)
        self.widget.bind("<Leave>", self._leave)
        self.widget.bind("<ButtonPress>", self._leave)

    def _enter(self, _: object = None) -> None:
        """鼠标进入事件"""
        self._schedule()

    def _leave(self, _: object = None) -> None:
        """鼠标离开事件"""
        self._unschedule()
        self._hide()

    def _schedule(self) -> None:
        """设置定时器"""
        self._unschedule()
        self.tooltip_id = self.widget.after(100, self._show)

    def _unschedule(self) -> None:
        """取消定时器"""
        if self.tooltip_id:
            self.widget.after_cancel(self.tooltip_id)
            self.tooltip_id = None

    def _show(self) -> None:
        """显示气泡提示"""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() - 25
        # 创建一个悬浮窗口
        self.tips = tw = ttk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(tw, text=self.text, background=self.tooltip_color, relief='solid', borderwidth=1)
        label.pack(ipadx=1)

    def _hide(self) -> None:
        """隐藏气泡提示"""
        if self.tips:
            self.tips.destroy()
            self.tips = None


class TextEditor:
    """文本编辑框，加入提示文字、滚动条"""

    def __init__(self, root):
        self.root = root
        self.default_font = ("", 10)
        self.placeholder_color = 'grey'
        self.text_color = 'black'

    def create_text(self,
                    row: int,
                    label_text: str,
                    placeholder: str = '') -> ttk.Text:
        """
        建立标签、文本框和滚动条。

        :param row: 放置行数
        :param label_text: 文本框前的标签文字
        :param placeholder: 用户友好的提示文字
        :return: 返回 ttk.Text 对象
        """
        self._create_label(row, label_text)
        text = self._create_text_widget(row + 1)
        self._config_scrollbar(text, row + 1)
        self._manage_placeholder(text, placeholder)
        return text

    def _create_label(self, row: int, label_text: str) -> None:
        """建立配套标签"""
        ttk.Label(self.root, text=label_text).grid(row=row, column=0, sticky='w', padx=MW_PADDING, pady=MW_PADDING)

    def _create_text_widget(self, row: int) -> ttk.Text:
        """建立文本框"""
        text = ttk.Text(self.root, undo=True, font=self.default_font, wrap='none', height=10)
        text.grid(row=row, column=0, sticky='wens', padx=MW_PADDING, pady=(10, 10))
        rcm = RightClickMenu(text)
        text.bind("<Button-3>", rcm.show_menu)
        self.root.grid_rowconfigure(row, weight=1)
        return text

    def _config_scrollbar(self, text: ttk.Text, row: int) -> None:
        """建立配置文本框滚动条"""
        scrollbar = ttk.Scrollbar(self.root)
        scrollbar.grid(row=row, column=1, sticky='ns')
        scrollbar.config(command=text.yview)
        text.config(yscrollcommand=scrollbar.set)

    def _manage_placeholder(self, text: ttk.Text, placeholder: str) -> None:
        """管理文本框提示文字占位符"""
        if placeholder:
            text.insert("1.0", placeholder)
            text.config(fg=self.placeholder_color)
            text.bind("<FocusIn>", lambda event, t=text, p=placeholder: self._on_focus_in(t, p))
            text.bind("<FocusOut>", lambda event, t=text, p=placeholder: self._on_focus_out(t, p))

    def _on_focus_in(self, text: ttk.Text, placeholder: str) -> None:
        """文本框获得焦点时，清除提示文字"""
        if text.get("1.0", "end-1c") == placeholder:
            text.delete("1.0", "end")
            text.config(fg=self.text_color)

    def _on_focus_out(self, text: ttk.Text, placeholder: str) -> None:
        """文本框失去焦点时，添加提示文字"""
        if not text.get("1.0", "end-1c"):
            text.insert("1.0", placeholder)
            text.config(fg=self.placeholder_color)


class RightClickMenu:
    """输入框右键菜单类"""

    def __init__(self, widget):
        self.widget = widget
        self.menu = ttk.Menu(self.widget, tearoff=0)
        self.make_menu()

    def make_menu(self):
        """配置输入框右键菜单"""
        self.menu.add_command(label=LABEL_MAP['undo'], command=lambda: self.widget.event_generate('<<Undo>>'))
        self.menu.add_command(label=LABEL_MAP['redo'], command=lambda: self.widget.event_generate('<<Redo>>'))
        self.menu.add_separator()
        self.menu.add_command(label=LABEL_MAP['cut'], command=lambda: self.widget.event_generate('<<Cut>>'))
        self.menu.add_command(label=LABEL_MAP['copy'], command=lambda: self.widget.event_generate('<<Copy>>'))
        self.menu.add_command(label=LABEL_MAP['paste'], command=lambda: self.widget.event_generate('<<Paste>>'))
        self.menu.add_separator()
        self.menu.add_command(label=LABEL_MAP['select_all'], command=lambda: self.widget.event_generate('<<SelectAll>>'))
        self.menu.add_command(label=LABEL_MAP['clear'], command=lambda: self.widget.event_generate('<<Clear>>'))

    def show_menu(self, e) -> None:
        """显示右键菜单"""
        self.menu.tk_popup(e.x_root, e.y_root)

