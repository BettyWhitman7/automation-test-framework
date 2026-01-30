"""
Fluent QSS - PySide6/PyQt6 的 Fluent Design 风格工具库

提供 Microsoft Fluent Design 风格的 UI 组件和主题样式。

主要功能:
- FluentTheme: 主题管理器，支持亮色/暗色主题切换
- FluentToast: Toast 通知组件
- FluentSideMenu: 可折叠侧边菜单
- FluentLogPanel: 可折叠日志面板
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
    theme.apply(app)  # 应用亮色主题到 QApplication
    theme.apply(app, dark=True)  # 切换到暗色主题
    theme.apply(widget)  # 也可以应用到单个 widget
    theme.is_dark #是否是暗色主题
    theme.toggle(QApplication.instance()) #切换主题

    # 显示 Toast 通知
    show_toast("操作成功!", parent=window)

    # 创建侧边菜单
    menu = FluentSideMenu()
    menu.add_item("🏠", "首页", 0)
    menu.add_item("⚙", "设置", 1)
    
    # 显示消息框
    FluentMessageBox.information(parent, "提示", "操作成功!")
    FluentMessageBox.warning(parent, "警告", "操作失败!")
    FluentMessageBox.critical(parent, "错误", "操作失败!")
    result = FluentMessageBox.question(parent, "确认", "是否继续?")
    
    # 显示输入框
    text, ok = FluentInputDialog.getText(parent, "输入", "请输入名称:")
    multiLineText, ok = FluentInputDialog.getMultiLineText(parent, "输入", "请输入多行文本:")
    int, ok = FluentInputDialog.getInt(parent, "输入", "请输入数字:")
    
    # 确认对话框
    FluentConfirmDialog.confirm(parent, "确认", "是否继续?")

    # 进度对话框
    FluentProgressDialog(parent, "处理中", "请稍候...")
    
    # 可停靠日志面板 (在 QMainWindow 中使用)
    from fluent_qss import FluentDockLogPanel
    log_dock = FluentDockLogPanel(self, title="📋 日志")
    self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, log_dock)
    log_dock.append_log("程序启动", "INFO")   # 级别: INFO, WARN, ERROR, DEBUG
    log_dock.append_log("警告信息", "WARN")
    log_dock.append_log("错误信息", "ERROR")
    log_dock.clear_log()  # 清空日志
"""

__version__ = "1.1.0"
__author__ = "zhuang jinpo"
__license__ = "MIT"

from pathlib import Path

from .fluent_dialog import (
    DialogButtonRole,
    FluentConfirmDialog,
    FluentInputDialog,
    FluentMessageBox,
    FluentProgressDialog,
    MessageBoxType,
)
from .fluent_dock_log_panel import FluentDockLogPanel
from .fluent_sideMenu import FluentSideMenu, FluentSideMenuItem
from .fluent_toast import FluentToast, show_toast
from .theme import FluentTheme, get_theme_path, load_theme

# 获取资源目录路径
RESOURCE_DIR = Path(__file__).parent

# 导入核心组件


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
    
    # UI 组件 - LogPanel
    "FluentDockLogPanel",
    
    # UI 组件 - Dialog
    "FluentMessageBox",
    "FluentInputDialog", 
    "FluentConfirmDialog",
    "FluentProgressDialog",
    "DialogButtonRole",
    "MessageBoxType",
]
