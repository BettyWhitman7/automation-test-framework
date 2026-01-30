"""
Fluent Dialog 组件演示

运行方式:
    python demo_dialog.py
"""

import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fluent_dialog import (
    FluentConfirmDialog,
    FluentInputDialog,
    FluentMessageBox,
    FluentProgressDialog,
)
from theme import FluentTheme


class DemoWindow(QMainWindow):
    """演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluent Dialog 演示")
        self.setMinimumSize(600, 500)
        
        # 主题管理
        self.theme = FluentTheme()
        
        # 创建中心部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel("🎨 Fluent Dialog 组件演示")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 主题切换
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        
        self.dark_mode_cb = QCheckBox("暗色模式")
        self.dark_mode_cb.setFont(QFont("Segoe UI", 11))
        self.dark_mode_cb.stateChanged.connect(self.toggle_theme)
        theme_layout.addWidget(self.dark_mode_cb)
        
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        # MessageBox 演示区域
        self._add_section(layout, "📢 MessageBox 消息框", [
            ("信息提示", self.show_info),
            ("警告消息", self.show_warning),
            ("确认对话", self.show_question),
            ("错误消息", self.show_error),
        ])
        
        # InputDialog 演示区域
        self._add_section(layout, "✏️ InputDialog 输入框", [
            ("文本输入", self.show_text_input),
            ("多行输入", self.show_multiline_input),
            ("数字输入", self.show_int_input),
        ])
        
        # ConfirmDialog 演示区域
        self._add_section(layout, "⚠️ ConfirmDialog 确认框", [
            ("普通确认", self.show_confirm),
            ("危险操作确认", self.show_danger_confirm),
        ])
        
        # ProgressDialog 演示区域
        self._add_section(layout, "⏳ ProgressDialog 进度框", [
            ("进度展示", self.show_progress),
            ("不确定进度", self.show_indeterminate),
        ])
        
        layout.addStretch()
        
        # 结果显示
        self.result_label = QLabel("点击按钮查看对话框效果")
        self.result_label.setFont(QFont("Segoe UI", 11))
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)
        
        # 应用主题
        self.theme.apply(self, dark=False)
    
    def _add_section(self, layout, title, buttons):
        """添加演示区域"""
        section_label = QLabel(title)
        section_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        layout.addWidget(section_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(36)
            btn.setMinimumWidth(100)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(callback)
            btn_layout.addWidget(btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def toggle_theme(self, state):
        """切换主题"""
        dark = state == Qt.CheckState.Checked.value
        self.theme.apply(self, dark=dark)
    
    def set_result(self, text):
        """设置结果显示"""
        self.result_label.setText(f"结果: {text}")
    
    # ========== MessageBox 演示 ==========
    
    def show_info(self):
        result = FluentMessageBox.information(
            self, "信息提示", 
            "这是一条Fluent风格的信息提示消息。\n支持多行文本显示。"
        )
        self.set_result(f"信息框 - 确定: {result}")
    
    def show_warning(self):
        result = FluentMessageBox.warning(
            self, "警告",
            "请注意！此操作可能会影响系统性能。"
        )
        self.set_result(f"警告框 - 确定: {result}")
    
    def show_question(self):
        result = FluentMessageBox.question(
            self, "确认操作",
            "您确定要保存当前更改吗？",
            ok_text="保存",
            cancel_text="不保存"
        )
        self.set_result(f"确认框 - 保存: {result}")
    
    def show_error(self):
        result = FluentMessageBox.critical(
            self, "错误",
            "操作失败！无法连接到服务器，请检查网络设置后重试。"
        )
        self.set_result(f"错误框 - 确定: {result}")
    
    # ========== InputDialog 演示 ==========
    
    def show_text_input(self):
        text, ok = FluentInputDialog.getText(
            self, "输入名称",
            "请输入您的用户名:",
            default="User",
            placeholder="在此输入..."
        )
        self.set_result(f"文本输入 - 确定: {ok}, 内容: '{text}'")
    
    def show_multiline_input(self):
        text, ok = FluentInputDialog.getMultiLineText(
            self, "输入描述",
            "请输入项目描述信息:",
            default="这是一个示例项目",
            placeholder="请在此输入详细描述..."
        )
        self.set_result(f"多行输入 - 确定: {ok}, 行数: {len(text.splitlines())}")
    
    def show_int_input(self):
        num, ok = FluentInputDialog.getInt(
            self, "输入数量",
            "请输入商品数量 (1-100):",
            value=10,
            min_val=1,
            max_val=100
        )
        self.set_result(f"数字输入 - 确定: {ok}, 数值: {num}")
    
    # ========== ConfirmDialog 演示 ==========
    
    def show_confirm(self):
        result = FluentConfirmDialog.confirm(
            self, "确认",
            "确定要应用这些设置吗？",
            confirm_text="应用",
            cancel_text="取消"
        )
        self.set_result(f"确认框 - 确认: {result}")
    
    def show_danger_confirm(self):
        result = FluentConfirmDialog.confirm(
            self, "删除文件",
            "确定要永久删除此文件吗？\n此操作无法撤销！",
            confirm_text="删除",
            cancel_text="取消",
            danger=True
        )
        self.set_result(f"危险确认 - 删除: {result}")
    
    # ========== ProgressDialog 演示 ==========
    
    def show_progress(self):
        """显示确定进度对话框"""
        dialog = FluentProgressDialog(
            self, "下载中",
            "正在下载文件...",
            cancelable=True
        )
        dialog.show()
        
        # 模拟进度
        self.progress_value = 0
        self.progress_dialog = dialog
        
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_timer.start(50)
    
    def _update_progress(self):
        """更新进度"""
        if self.progress_dialog.is_canceled():
            self.progress_timer.stop()
            self.set_result("进度框 - 已取消")
            return
        
        self.progress_value += 2
        self.progress_dialog.set_progress(self.progress_value)
        self.progress_dialog.set_message(f"正在下载: {self.progress_value}%")
        
        if self.progress_value >= 100:
            self.progress_timer.stop()
            self.progress_dialog.close()
            self.set_result("进度框 - 下载完成!")
    
    def show_indeterminate(self):
        """显示不确定进度对话框"""
        dialog = FluentProgressDialog(
            self, "处理中",
            "正在处理数据，请稍候...",
            cancelable=True
        )
        dialog.set_indeterminate(True)
        dialog.show()
        
        self.indeterminate_dialog = dialog
        
        # 3秒后自动关闭
        QTimer.singleShot(3000, self._close_indeterminate)
    
    def _close_indeterminate(self):
        """关闭不确定进度框"""
        if hasattr(self, 'indeterminate_dialog'):
            if not self.indeterminate_dialog.is_canceled():
                self.indeterminate_dialog.close()
                self.set_result("不确定进度框 - 处理完成!")
            else:
                self.set_result("不确定进度框 - 已取消")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Fluent Dialog Demo")
    app.setOrganizationName("FluentQSS")
    
    # 创建并显示窗口
    window = DemoWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
