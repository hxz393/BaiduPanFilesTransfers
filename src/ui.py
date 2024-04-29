"""
把 UI 相关类集中在一起。

:author: assassing
:contact: https://github.com/hxz393
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""

import re
import webbrowser
from typing import Callable

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from src.constants import COLOR_THEME, LABEL_MAP, EXP_MAP, MW_PADDING, MAIN_TITLE, MAIN_VERSION, HOME_PAGE, TOOLTIP_PADDING, TOOLTIP_DELAY, COLOR_MAP
from src.utils import thread_it, read_config, create_icon


class MainWindow(ttk.Window):
    """
    程序主窗口，继承自 ttk.Window。

    :param op: 主逻辑功能类的实例
    """

    def __init__(self, op):
        """初始化 UI 元素"""
        super().__init__()
        self.op = op
        self.icon_path = create_icon()
        self._setup_window()
        self._create_widgets()
        self._init_config()

    def _setup_window(self) -> None:
        """主窗口配置"""
        self.style.theme_use(COLOR_THEME)
        self.iconbitmap(self.icon_path)
        self.title(f"{MAIN_TITLE} {MAIN_VERSION}")
        self.grid_columnconfigure(0, weight=1)
        self.place_window_center()

    def _create_widgets(self) -> None:
        """定义窗口控件和元素布局"""
        init_row = 1
        # Cookie 输入框、目标路径输入框
        self.entry_cookie = self._create_entry(init_row, LABEL_MAP['cookie'])
        self.entry_folder_name = self._create_entry(init_row + 2, LABEL_MAP['folder_name'])
        # 链接输入文本框、日志输出文本框
        self.text_links = TextEditor(self).create_text(init_row + 4, LABEL_MAP['links'], LABEL_MAP['links_tip'])
        self.text_logs = TextEditor(self).create_text(init_row + 7, LABEL_MAP['logs'], LABEL_MAP['logs_tip'])
        # 创建选项容器和三个选项复选框
        self.frame_options = ttk.LabelFrame(self, text=LABEL_MAP['options'], padding="10 10 0 9")
        self.frame_options.grid(row=init_row + 6, sticky='w', padx=MW_PADDING)
        self.var_trust_env = self._create_checkbutton(LABEL_MAP['trust'], LABEL_MAP['trust_tip'], 0)
        self.var_safe_mode = self._create_checkbutton(LABEL_MAP['safe'], LABEL_MAP['safe_tip'], 1)
        self.var_check_mode = self._create_checkbutton(LABEL_MAP['check'], LABEL_MAP['check_tip'], 2)
        # 创建按钮容器和两个功能按钮
        self.frame_bottom = ttk.Frame(self)
        self.frame_bottom.grid(row=init_row + 6, sticky='e', padx=MW_PADDING)
        self.bottom_save = self._create_button(LABEL_MAP['save'], self._save_button_click, 1)
        self.bottom_share = self._create_button(LABEL_MAP['share'], self._share_button_click, 0)
        # 状态标签
        # noinspection PyArgumentList
        self.label_status = ttk.Label(self, text=LABEL_MAP['help'], font=('', 10, 'underline'), bootstyle='primary', cursor='heart')
        self.label_status.grid(row=init_row + 7, sticky='e', padx=MW_PADDING, pady=MW_PADDING)
        self.label_status.bind("<Button-1>", lambda e: webbrowser.open(HOME_PAGE))

    def _create_entry(self, row: int, label_text: str) -> ttk.Entry:
        """建立标签和输入框函数"""
        ttk.Label(self, text=label_text).grid(row=row, sticky='w', padx=MW_PADDING, pady=MW_PADDING)
        entry = ttk.Entry(self)
        entry.bind("<Button-3>", RightClickMenu(entry).show_menu)
        entry.grid(row=row + 1, sticky='we', padx=MW_PADDING, pady=MW_PADDING)
        return entry

    def _create_checkbutton(self, text: str, tooltip: str, column: int) -> ttk.BooleanVar:
        """建立设置复选框"""
        var = ttk.BooleanVar()
        checkbutton = ttk.Checkbutton(self.frame_options, text=text, variable=var)
        checkbutton.grid(row=0, column=column, padx=(0, 10))
        ToolTip(widget=checkbutton, text=tooltip)
        return var

    def _create_button(self, text: str, command: Callable, column: int) -> ttk.Button:
        """建立功能按钮"""
        button = ttk.Button(self.frame_bottom, text=text, width=10, padding="17 17 17 17", command=lambda: thread_it(command))
        button.grid(row=0, column=column, padx=MW_PADDING)
        return button

    def _init_config(self) -> None:
        """初始化配置"""
        config = read_config()
        self.entry_cookie.insert(0, config[0].strip() if config else '')
        self.entry_folder_name.insert(0, config[1].strip() if len(config) > 1 else '')

    def _save_button_click(self) -> None:
        """当按钮被点击时，调用逻辑处理对象的批量转存方法"""
        self.op.save()

    def _share_button_click(self) -> None:
        """当按钮被点击时，调用逻辑处理对象的批量分享方法"""
        self.op.share()

    def run(self) -> None:
        """运行程序"""
        self.mainloop()


class TextEditor:
    """
    文本编辑框，加入提示文字、滚动条。

    :param root: 主窗口
    """

    def __init__(self, root):
        self.root = root

    def create_text(self,
                    row: int,
                    label_text: str,
                    placeholder: str = '') -> ttk.Text:
        """
        建立文本框，建立与文本框绑定的标签和滚动条。

        :param row: 放置行数
        :param label_text: 文本框前的标签文字
        :param placeholder: 用户友好的提示文字
        :return: 返回文本框对象
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
        text = ttk.Text(self.root, undo=True, font=("", 10), wrap='none', height=10)
        text.grid(row=row, column=0, sticky='wens', padx=MW_PADDING, pady=(10, 10))
        text.bind("<Button-3>", RightClickMenu(text).show_menu)
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
            text.config(fg=COLOR_MAP['placeholder'])
            text.bind("<FocusIn>", lambda event, t=text, p=placeholder: self._on_focus_in(t, p))
            text.bind("<FocusOut>", lambda event, t=text, p=placeholder: self._on_focus_out(t, p))

    @staticmethod
    def _on_focus_in(text: ttk.Text, placeholder: str) -> None:
        """文本框获得焦点时，清除提示文字"""
        if text.get("1.0", "end-1c") == placeholder:
            text.delete("1.0", "end")
            text.config(fg=COLOR_MAP['text'])

    @staticmethod
    def _on_focus_out(text: ttk.Text, placeholder: str) -> None:
        """文本框失去焦点时，添加提示文字"""
        if not text.get("1.0", "end-1c"):
            text.insert("1.0", placeholder)
            text.config(fg=COLOR_MAP['placeholder'])


class CustomDialog(ttk.Toplevel):
    """
    弹出对话框，用于自定义分享参数。

    :param parent: 父窗口，也就是主窗口
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.result = ()
        self.parent = parent
        # 纯 UI 建立函数，最后加上阻塞流程，等待窗口被销毁或关闭
        self._setup_window()
        self._create_widgets()
        self.wait_window(self)

    def _setup_window(self) -> None:
        """窗口配置"""
        self.style.theme_use(COLOR_THEME)
        self.title(LABEL_MAP['settings_title'])
        self.iconbitmap(self.parent.icon_path)
        self.resizable(width=False, height=False)
        self.place_window_center()
        # 在任务栏中不显示条目
        self.transient(self.parent)
        # 使窗口获得焦点，阻止与其他窗口交互
        self.grab_set()

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
        self.var_password = ttk.StringVar(self, value=LABEL_MAP['default_password'])
        ttk.Label(master, text=LABEL_MAP['password_title']).grid(row=1, column=0, sticky='e')
        ttk.Entry(master, textvariable=self.var_password, bootstyle="info").grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        # 在两个 frame 之间插入分割线
        ttk.Separator(self, orient='horizontal').pack(fill="x")
        # 底部按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text=LABEL_MAP['ok'], command=self.validate, bootstyle='primary').pack(side='right', padx=5)
        ttk.Button(button_frame, text=LABEL_MAP['cancel'], command=self.destroy, bootstyle='danger').pack(side='right', padx=5)

    def validate(self) -> bool:
        """验证输入提取码有效性"""
        expiry = self.var_expiry.get()
        password = self.var_password.get()
        # 用正则检查用户输入，为 False 时窗口继续停留
        if not re.match("^[a-zA-Z0-9]{4}$", password):
            Messagebox.show_warning(title=LABEL_MAP['validate_title'], message=LABEL_MAP['validate_msg'], master=self)
            return False

        # 结果被 share 函数直接获取
        self.result = (expiry, password)
        self.destroy()
        return True


class ToolTip:
    """
    为组件增加悬浮提示气泡。

    :param widget: 要增加悬浮提示的组件
    :param text: 提示信息内容
    """

    def __init__(self, widget, text: str = ''):
        self.widget = widget
        self.text = text
        self.tips = None
        self.id = None
        # 绑定光标移入、移出和点击事件
        self._binding()

    def _binding(self) -> None:
        """配置鼠标绑定事件"""
        self.widget.bind("<Enter>", lambda _: self._after(True))
        self.widget.bind("<Leave>", lambda _: self._after(False))
        self.widget.bind("<ButtonPress>", lambda _: self._after(False))

    def _after(self, enter: bool) -> None:
        """活用 enter 来判断是否要展示提示气泡"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

        if enter:
            self.id = self.widget.after(TOOLTIP_DELAY, self._show)
        else:
            self._hide()

    def _show(self) -> None:
        """显示气泡提示"""
        x = self.widget.winfo_rootx() + TOOLTIP_PADDING
        y = self.widget.winfo_rooty() - TOOLTIP_PADDING
        # 创建一个悬浮窗口
        self.tips = tw = ttk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        ttk.Label(tw, text=self.text, background=COLOR_MAP['tooltip'], relief='solid', borderwidth=1).pack(ipadx=1)

    def _hide(self) -> None:
        """隐藏气泡提示"""
        if self.tips:
            self.tips.destroy()
            self.tips = None


class RightClickMenu(ttk.Menu):
    """
    为组件增加右键菜单。

    :param widget: 只接收输入框（entry）和文本框（text）组件
    """

    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self._make_menu()

    def _make_menu(self):
        """配置输入框右键菜单"""
        self.add_command(label=LABEL_MAP['undo'], command=lambda: self.widget.event_generate('<<Undo>>'))
        self.add_command(label=LABEL_MAP['redo'], command=lambda: self.widget.event_generate('<<Redo>>'))
        self.add_separator()
        self.add_command(label=LABEL_MAP['cut'], command=lambda: self.widget.event_generate('<<Cut>>'))
        self.add_command(label=LABEL_MAP['copy'], command=lambda: self.widget.event_generate('<<Copy>>'))
        self.add_command(label=LABEL_MAP['paste'], command=lambda: self.widget.event_generate('<<Paste>>'))
        self.add_separator()
        self.add_command(label=LABEL_MAP['select_all'], command=lambda: self.widget.event_generate('<<SelectAll>>'))
        self.add_command(label=LABEL_MAP['clear'], command=lambda: self.widget.event_generate('<<Clear>>'))

    def show_menu(self, e) -> None:
        """显示右键菜单"""
        self.tk_popup(e.x_root, e.y_root)
