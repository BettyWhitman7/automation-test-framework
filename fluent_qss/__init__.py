"""
Fluent QSS - PySide6/PyQt6 的 Fluent Design 风格工具库

提供 Microsoft Fluent Design 风格的 UI 组件和主题样式。

主要功能:
- FluentTheme: 主题管理器，支持亮色/暗色主题切换
- FluentToast: Toast 通知组件
- FluentSideMenu: 可折叠侧边菜单
- FluentMessageBox: 消息框组件
- FluentInputDialog: 输入对话框组件
- FluentConfirmDialog: 确认对话框组件
- FluentProgressDialog: 进度对话框组件
- QSS 样式表: fluent_widgets.qss (亮色) / fluent_widgets_dark.qss (暗色)

使用示例:
    from fluent_qss import FluentTheme, FluentToast, FluentSideMenu, show_toast
    from fluent_qss import FluentMessageBox, FluentInputDialog

    # 应用主题
    theme = FluentTheme()
    theme.apply(app)  # 应用亮色主题
    theme.apply(app, dark=True)  # 应用暗色主题
    def _toggle_theme(self):   #切换主题
        self.theme.toggle(QApplication.instance())
        if self.theme.is_dark:
            print("☀️ 亮色模式")
        else:
            print("🌙 暗色模式")

    # 显示 Toast 通知
    show_toast("操作成功!", parent=window)

    # 创建侧边菜单
    menu = FluentSideMenu()
    menu.add_item("🏠", "首页", 0)
    menu.add_item("⚙", "设置", 1)
    
    # 显示消息框
    FluentMessageBox.information(parent, "提示", "操作成功!")
    result = FluentMessageBox.question(parent, "确认", "是否继续?")
    
    # 显示输入框
    text, ok = FluentInputDialog.getText(parent, "输入", "请输入名称:")
"""

__version__ = "1.1.0"
__author__ = "zhuang jinpo"
__license__ = "MIT"

from pathlib import Path

# 获取资源目录路径
RESOURCE_DIR = Path(__file__).parent

# 导入核心组件
from .fluent_toast import FluentToast, show_toast
from .fluent_sideMenu import FluentSideMenu, FluentSideMenuItem
from .theme import FluentTheme, load_theme, get_theme_path
from .fluent_dialog import (
    FluentMessageBox,
    FluentInputDialog,
    FluentConfirmDialog,
    FluentProgressDialog,
    DialogButtonRole,
    MessageBoxType
)

# 公开 API
__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__license__",
    
    # 资源路径
    "RESOURCE_DIR",
    
    # 主题管理
    "FluentTheme",
    "load_theme",
    "get_theme_path",
    
    # UI 组件 - Toast
    "FluentToast",
    "show_toast",
    
    # UI 组件 - SideMenu
    "FluentSideMenu",
    "FluentSideMenuItem",
    
    # UI 组件 - Dialog
    "FluentMessageBox",
    "FluentInputDialog", 
    "FluentConfirmDialog",
    "FluentProgressDialog",
    "DialogButtonRole",
    "MessageBoxType",
]
