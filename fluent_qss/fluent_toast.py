"""
Toast 通知组件 - Fluent Design风格
用于显示临时通知消息
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, QRect
from PySide6.QtGui import QFont


class FluentToast(QWidget):
    """Fluent Design 风格的 Toast 通知"""
    
    def __init__(self, message: str, duration: int = 3000, parent=None):
        """
        初始化 Toast 通知
        
        Args:
            message: 显示的消息文本
            duration: 显示时长（毫秒），默认3000ms
            parent: 父窗口
        """
        super().__init__(parent)
        self.message = message
        self.duration = duration
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 创建UI
        self.setup_ui()
        
        # 创建计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.fadeOut)
    
    def setup_ui(self):
        """设置UI"""
        # 创建布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签
        self.label = QLabel(self.message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont("Segoe UI", 10))
        self.label.setWordWrap(True)  # 允许文本换行
        self.label.setFixedWidth(250)  # 固定标签宽度
        self.label.setMinimumHeight(45)  # 最小高度
        self.label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: #323130;
                border-radius: 4px;
                padding: 12px 20px;
            }
        """)
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # 设置窗口大小
        self.adjustSize()
    
    def show_at_bottom(self, parent=None):
        """在窗口底部显示"""
        if parent is None:
            parent = self.parent()
        
        if parent and isinstance(parent, QWidget):
            # 获取父窗口客户区的实际大小
            parent_width = parent.width()
            parent_height = parent.height()
            
            # 调整 toast 高度以适应内容（宽度已固定）
            self.adjustSize()
            
            # 计算 toast 位置（父窗口底部居中）
            toast_width = self.width()
            toast_height = self.height()
            
            # 基础位置：水平居中，底部向上20px
            # 注意：这里先计算相对于父窗口左上角的偏移量
            offset_x = (parent_width - toast_width) // 2
            offset_y = parent_height - toast_height - 20
            
            # 边界限制（相对于父窗口）
            # 确保不超出左右边界（留10px边距）
            min_x = 10
            max_x = parent_width - toast_width - 10
            if max_x < min_x:
                offset_x = (parent_width - toast_width) // 2 # 窗口太小，直接居中
            else:
                offset_x = max(min_x, min(offset_x, max_x))
                
            # 确保不超出上下边界
            min_y = 10
            max_y = parent_height - toast_height - 10
            if max_y < min_y:
                offset_y = (parent_height - toast_height) // 2 # 窗口太小，垂直居中
            else:
                offset_y = max(min_y, min(offset_y, max_y))

            # 根据是否为顶级窗口决定最终坐标
            if self.isWindow() and isinstance(parent, QWidget):
                # 顶级窗口使用全局坐标
                parent_global_pos = parent.mapToGlobal(QPoint(0, 0))
                self.move(parent_global_pos.x() + offset_x, parent_global_pos.y() + offset_y)
            else:
                # 子窗口使用相对坐标
                self.move(offset_x, offset_y)
        
        self.show()
        self.timer.start(self.duration)
        
        # 创建淡入动画
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_in_animation.start()
    
    def fadeOut(self):
        """淡出动画"""
        self.timer.stop()
        
        # 创建淡出动画
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_animation.finished.connect(self.close)
        self.fade_out_animation.start()


def show_toast(message: str, duration: int = 3000, parent=None):
    """
    显示 Toast 通知的便捷函数
    
    Args:
        message: 消息文本
        duration: 显示时长（毫秒）
        parent: 父窗口
    """
    toast = FluentToast(message, duration, parent)
    toast.show_at_bottom(parent)
    return toast
