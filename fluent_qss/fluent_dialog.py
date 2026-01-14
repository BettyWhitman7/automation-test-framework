"""
Fluent Design 弹框组件库
提供 MessageBox, Dialog, InputDialog 等弹框类
样式由外部 QSS 文件控制

使用示例:
    from fluent_qss import FluentMessageBox, FluentInputDialog
    
    # MessageBox
    FluentMessageBox.information(parent, "标题", "这是一条信息")
    FluentMessageBox.question(parent, "确认", "确认要执行此操作吗？")
    
    # InputDialog
    text, ok = FluentInputDialog.getText(parent, "输入", "请输入内容:")
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QLineEdit,
    QTextEdit, QApplication, QProgressBar, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPainter
from enum import Enum
from typing import Tuple


class DialogButtonRole(Enum):
    """对话框按钮角色"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DANGER = "danger"


class FluentDialogBase(QDialog):
    """Fluent Design 风格对话框基类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        
        # 创建主容器
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建对话框容器
        self._dialog_container = QFrame()
        self._dialog_container.setObjectName("FluentDialogContainer")
        self._add_shadow_effect()
        
        self._main_layout.addWidget(
            self._dialog_container, 
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        
        # 内部布局
        self._container_layout = QVBoxLayout(self._dialog_container)
        self._container_layout.setContentsMargins(24, 20, 24, 20)
        self._container_layout.setSpacing(16)
    
    def _add_shadow_effect(self):
        """添加阴影效果"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        self._dialog_container.setGraphicsEffect(shadow)
    
    def paintEvent(self, event):
        """绘制半透明遮罩背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))
        super().paintEvent(event)
    
    def _create_button(
        self, 
        text: str, 
        role: DialogButtonRole = DialogButtonRole.SECONDARY,
        min_width: int = 100
    ) -> QPushButton:
        """创建按钮，样式由外部QSS控制"""
        btn = QPushButton(text)
        btn.setMinimumWidth(min_width)
        btn.setMinimumHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置objectName，样式由QSS控制
        if role == DialogButtonRole.PRIMARY:
            btn.setObjectName("FluentDialogPrimaryBtn")
        elif role == DialogButtonRole.DANGER:
            btn.setObjectName("FluentDialogDangerBtn")
        else:
            btn.setObjectName("FluentDialogSecondaryBtn")
        
        return btn
    
    def showEvent(self, event):
        """显示时居中"""
        super().showEvent(event)
        self._center_on_parent()
    
    def _center_on_parent(self):
        """居中显示在父窗口上"""
        parent = self.parent()
        if parent and isinstance(parent, QWidget):
            # 获取父窗口的全局位置和尺寸
            parent_rect = parent.rect()
            global_pos = parent.mapToGlobal(parent_rect.topLeft())
            self.setGeometry(
                global_pos.x(), 
                global_pos.y(), 
                parent_rect.width(), 
                parent_rect.height()
            )
        else:
            screen = QApplication.primaryScreen().geometry()
            self.setGeometry(screen)


class MessageBoxType(Enum):
    """消息框类型"""
    INFORMATION = "information"
    WARNING = "warning"
    QUESTION = "question"
    ERROR = "error"


class FluentMessageBox(FluentDialogBase):
    """
    Fluent Design 风格消息框
    
    使用示例:
        FluentMessageBox.information(parent, "标题", "消息内容")
        result = FluentMessageBox.question(parent, "确认", "是否继续？")
    """
    
    ICONS = {
        MessageBoxType.INFORMATION: "ℹ️",
        MessageBoxType.WARNING: "⚠️",
        MessageBoxType.QUESTION: "❓",
        MessageBoxType.ERROR: "❌",
    }
    
    def __init__(
        self,
        parent=None,
        title: str = "",
        message: str = "",
        msg_type: MessageBoxType = MessageBoxType.INFORMATION,
        show_cancel: bool = False,
        ok_text: str = "确定",
        cancel_text: str = "取消"
    ):
        super().__init__(parent)
        
        self._title = title
        self._message = message
        self._msg_type = msg_type
        self._show_cancel = show_cancel
        self._ok_text = ok_text
        self._cancel_text = cancel_text
        self._result = False
        
        self._setup_ui()
        self._dialog_container.setMinimumWidth(360)
        self._dialog_container.setMaximumWidth(480)
    
    def _setup_ui(self):
        """设置UI"""
        # 图标和标题行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # 图标
        icon_label = QLabel(self.ICONS[self._msg_type])
        icon_label.setObjectName("FluentDialogIcon")
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # 标题
        title_label = QLabel(self._title)
        title_label.setObjectName("FluentDialogTitle")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)
        
        self._container_layout.addLayout(header_layout)
        
        # 消息内容
        message_label = QLabel(self._message)
        message_label.setObjectName("FluentDialogContent")
        message_label.setWordWrap(True)
        message_label.setContentsMargins(48, 0, 0, 0)
        self._container_layout.addWidget(message_label)
        
        self._container_layout.addSpacing(8)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch()
        
        if self._show_cancel:
            cancel_btn = self._create_button(self._cancel_text, DialogButtonRole.SECONDARY)
            cancel_btn.clicked.connect(self._on_cancel)
            btn_layout.addWidget(cancel_btn)
        
        ok_role = DialogButtonRole.DANGER if self._msg_type == MessageBoxType.ERROR else DialogButtonRole.PRIMARY
        ok_btn = self._create_button(self._ok_text, ok_role)
        ok_btn.clicked.connect(self._on_ok)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        self._container_layout.addLayout(btn_layout)
    
    def _on_ok(self):
        self._result = True
        self.accept()
    
    def _on_cancel(self):
        self._result = False
        self.reject()
    
    def get_result(self) -> bool:
        return self._result
    
    # ========== 静态便捷方法 ==========
    
    @staticmethod
    def information(parent=None, title: str = "提示", message: str = "") -> bool:
        dialog = FluentMessageBox(parent, title, message, MessageBoxType.INFORMATION)
        dialog.exec()
        return dialog.get_result()
    
    @staticmethod
    def warning(parent=None, title: str = "警告", message: str = "") -> bool:
        dialog = FluentMessageBox(parent, title, message, MessageBoxType.WARNING)
        dialog.exec()
        return dialog.get_result()
    
    @staticmethod
    def question(
        parent=None, title: str = "确认", message: str = "",
        ok_text: str = "确定", cancel_text: str = "取消"
    ) -> bool:
        dialog = FluentMessageBox(
            parent, title, message, MessageBoxType.QUESTION,
            show_cancel=True, ok_text=ok_text, cancel_text=cancel_text
        )
        dialog.exec()
        return dialog.get_result()
    
    @staticmethod
    def error(parent=None, title: str = "错误", message: str = "") -> bool:
        dialog = FluentMessageBox(parent, title, message, MessageBoxType.ERROR)
        dialog.exec()
        return dialog.get_result()


class FluentInputDialog(FluentDialogBase):
    """Fluent Design 风格输入对话框"""
    
    def __init__(
        self,
        parent=None,
        title: str = "",
        label: str = "",
        default_text: str = "",
        placeholder: str = "",
        multiline: bool = False,
        ok_text: str = "确定",
        cancel_text: str = "取消"
    ):
        super().__init__(parent)
        
        self._title = title
        self._label = label
        self._default_text = default_text
        self._placeholder = placeholder
        self._multiline = multiline
        self._ok_text = ok_text
        self._cancel_text = cancel_text
        self._result_text = ""
        self._accepted = False
        
        self._setup_ui()
        self._dialog_container.setMinimumWidth(400)
        self._dialog_container.setMaximumWidth(500)
    
    def _setup_ui(self):
        """设置UI"""
        # 标题
        title_label = QLabel(self._title)
        title_label.setObjectName("FluentDialogTitle")
        self._container_layout.addWidget(title_label)
        
        # 提示标签
        if self._label:
            label = QLabel(self._label)
            label.setObjectName("FluentDialogContent")
            label.setWordWrap(True)
            self._container_layout.addWidget(label)
        
        # 创建输入框
        if self._multiline:
            self._input = QTextEdit()
            self._input.setObjectName("FluentDialogTextEdit")
            self._input.setPlainText(self._default_text)
            self._input.setPlaceholderText(self._placeholder)
            self._input.setMinimumHeight(100)
            self._input.setMaximumHeight(200)
        else:
            self._input = QLineEdit()
            self._input.setObjectName("FluentDialogInput")
            self._input.setText(self._default_text)
            self._input.setPlaceholderText(self._placeholder)
            self._input.returnPressed.connect(self._on_ok)
        
        self._container_layout.addWidget(self._input)
        
        # 按钮区域
        self._container_layout.addSpacing(8)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch()
        
        cancel_btn = self._create_button(self._cancel_text, DialogButtonRole.SECONDARY)
        cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = self._create_button(self._ok_text, DialogButtonRole.PRIMARY)
        ok_btn.clicked.connect(self._on_ok)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        self._container_layout.addLayout(btn_layout)
    
    def _on_ok(self):
        if self._multiline:
            self._result_text = self._input.toPlainText() if isinstance(self._input, QTextEdit) else ""
        else:
            self._result_text = self._input.text() if isinstance(self._input, QLineEdit) else ""
        self._accepted = True
        self.accept()
    
    def _on_cancel(self):
        self._result_text = ""
        self._accepted = False
        self.reject()
    
    def get_text(self) -> str:
        return self._result_text
    
    def is_accepted(self) -> bool:
        return self._accepted
    
    def showEvent(self, event):
        super().showEvent(event)
        self._input.setFocus()
        if not self._multiline:
            self._input.selectAll()
    
    # ========== 静态便捷方法 ==========
    
    @staticmethod
    def getText(
        parent=None, title: str = "输入", label: str = "",
        default: str = "", placeholder: str = ""
    ) -> Tuple[str, bool]:
        dialog = FluentInputDialog(parent, title, label, default, placeholder, multiline=False)
        dialog.exec()
        return dialog.get_text(), dialog.is_accepted()
    
    @staticmethod
    def getMultiLineText(
        parent=None, title: str = "输入", label: str = "",
        default: str = "", placeholder: str = ""
    ) -> Tuple[str, bool]:
        dialog = FluentInputDialog(parent, title, label, default, placeholder, multiline=True)
        dialog.exec()
        return dialog.get_text(), dialog.is_accepted()
    
    @staticmethod
    def getInt(
        parent=None, title: str = "输入", label: str = "",
        value: int = 0, min_val: int = -2147483647, max_val: int = 2147483647
    ) -> Tuple[int, bool]:
        dialog = FluentInputDialog(parent, title, label, str(value), "", multiline=False)
        dialog.exec()
        if dialog.is_accepted():
            try:
                result = int(dialog.get_text())
                return max(min_val, min(max_val, result)), True
            except ValueError:
                return value, False
        return value, False


class FluentConfirmDialog(FluentDialogBase):
    """Fluent Design 风格确认对话框（用于危险操作）"""
    
    def __init__(
        self,
        parent=None,
        title: str = "",
        message: str = "",
        confirm_text: str = "确定",
        cancel_text: str = "取消",
        danger: bool = False
    ):
        super().__init__(parent)
        
        self._title = title
        self._message = message
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._danger = danger
        self._confirmed = False
        
        self._setup_ui()
        self._dialog_container.setMinimumWidth(380)
        self._dialog_container.setMaximumWidth(480)
    
    def _setup_ui(self):
        """设置UI"""
        if self._danger:
            icon_label = QLabel("⚠️")
            icon_label.setObjectName("FluentDialogIcon")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._container_layout.addWidget(icon_label)
        
        title_label = QLabel(self._title)
        title_label.setObjectName("FluentDialogTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._container_layout.addWidget(title_label)
        
        message_label = QLabel(self._message)
        message_label.setObjectName("FluentDialogContent")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._container_layout.addWidget(message_label)
        
        self._container_layout.addSpacing(12)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = self._create_button(self._cancel_text, DialogButtonRole.SECONDARY, 120)
        cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(cancel_btn)
        
        confirm_role = DialogButtonRole.DANGER if self._danger else DialogButtonRole.PRIMARY
        confirm_btn = self._create_button(self._confirm_text, confirm_role, 120)
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)
        
        self._container_layout.addLayout(btn_layout)
    
    def _on_confirm(self):
        self._confirmed = True
        self.accept()
    
    def _on_cancel(self):
        self._confirmed = False
        self.reject()
    
    def is_confirmed(self) -> bool:
        return self._confirmed
    
    @staticmethod
    def confirm(
        parent=None, title: str = "确认", message: str = "",
        confirm_text: str = "确定", cancel_text: str = "取消", danger: bool = False
    ) -> bool:
        dialog = FluentConfirmDialog(parent, title, message, confirm_text, cancel_text, danger)
        dialog.exec()
        return dialog.is_confirmed()


class FluentProgressDialog(FluentDialogBase):
    """Fluent Design 风格进度对话框"""
    
    canceled = Signal()
    
    def __init__(
        self,
        parent=None,
        title: str = "处理中",
        message: str = "",
        cancelable: bool = True
    ):
        super().__init__(parent)
        
        self._title = title
        self._message = message
        self._cancelable = cancelable
        self._progress = 0
        self._canceled = False
        
        self._setup_ui()
        self._dialog_container.setMinimumWidth(400)
        self._dialog_container.setMaximumWidth(480)
    
    def _setup_ui(self):
        """设置UI"""
        self._title_label = QLabel(self._title)
        self._title_label.setObjectName("FluentDialogTitle")
        self._container_layout.addWidget(self._title_label)
        
        self._message_label = QLabel(self._message)
        self._message_label.setObjectName("FluentDialogContent")
        self._message_label.setWordWrap(True)
        self._container_layout.addWidget(self._message_label)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("FluentDialogProgress")
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._container_layout.addWidget(self._progress_bar)
        
        if self._cancelable:
            self._container_layout.addSpacing(8)
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            cancel_btn = self._create_button("取消", DialogButtonRole.SECONDARY)
            cancel_btn.clicked.connect(self._on_cancel)
            btn_layout.addWidget(cancel_btn)
            btn_layout.addStretch()
            self._container_layout.addLayout(btn_layout)
    
    def set_progress(self, value: int):
        self._progress = max(0, min(100, value))
        self._progress_bar.setValue(self._progress)
        QApplication.processEvents()
    
    def set_message(self, message: str):
        self._message_label.setText(message)
        QApplication.processEvents()
    
    def set_title(self, title: str):
        self._title_label.setText(title)
        QApplication.processEvents()
    
    def set_indeterminate(self, indeterminate: bool):
        if indeterminate:
            self._progress_bar.setMaximum(0)
        else:
            self._progress_bar.setMaximum(100)
    
    def is_canceled(self) -> bool:
        return self._canceled
    
    def _on_cancel(self):
        self._canceled = True
        self.canceled.emit()
        self.reject()

