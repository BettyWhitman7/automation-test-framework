"""
Fluent Design 风格可停靠日志面板组件

基于 QDockWidget 实现的可拖动、可停靠日志面板。

使用示例:
    from fluent_qss import FluentDockLogPanel
    
    # 在 QMainWindow 中使用
    log_dock = FluentDockLogPanel(self)
    self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, log_dock)
    
    # 添加日志
    log_dock.append_log("操作成功", "INFO")
    log_dock.append_log("警告信息", "WARN")
    log_dock.append_log("错误信息", "ERROR")
"""

from datetime import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
)


class FluentDockLogPanel(QDockWidget):
    """
    Fluent Design 风格可停靠日志面板
    
    Features:
        - 可拖动停靠到主窗口的四个方向
        - 可浮动成独立窗口
        - 支持多级别日志（INFO, WARN, ERROR, DEBUG）
        - 自动时间戳
        - 日志级别颜色标记
        - 一键清空日志
    
    Signals:
        log_added(str, str): 添加日志时触发，参数为(消息, 级别)
    
    Example:
        # 在 QMainWindow 中使用
        log_dock = FluentDockLogPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, log_dock)
        
        log_dock.append_log("程序启动", "INFO")
        log_dock.append_log("连接失败", "ERROR")
    """
    
    # 添加日志信号
    log_added = Signal(str, str)
    
    def __init__(
        self, 
        parent=None, 
        title: str = "📋 日志",
        allowed_areas: Qt.DockWidgetArea = Qt.DockWidgetArea.AllDockWidgetAreas
    ):
        """
        初始化可停靠日志面板
        
        Args:
            parent: 父窗口（通常是 QMainWindow）
            title: 面板标题
            allowed_areas: 允许停靠的区域
        """
        super().__init__(title, parent)
        
        self.setObjectName("FluentDockLogPanel")
        self.setAllowedAreas(allowed_areas)
        
        # 设置特性：可移动、可浮动、可关闭
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """设置UI"""
        # 主容器
        container = QWidget()
        container.setObjectName("FluentDockLogPanelContent")
        self.setWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        
        # 日志级别指示
        self._level_label = QLabel("日志记录")
        self._level_label.setObjectName("FluentDockLogPanelLabel")
        toolbar.addWidget(self._level_label)
        
        toolbar.addStretch()
        
        # 清空按钮
        clear_btn = QPushButton("🗑 清空")
        clear_btn.setObjectName("FluentDockLogPanelClearBtn")
        clear_btn.setFixedHeight(24)
        clear_btn.setToolTip("清空日志")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_log)
        toolbar.addWidget(clear_btn)
        
        layout.addLayout(toolbar)
        
        # 日志文本区域
        self._log_text = QTextEdit()
        self._log_text.setObjectName("FluentDockLogPanelText")
        self._log_text.setReadOnly(True)
        self._log_text.setPlaceholderText("暂无日志...")
        layout.addWidget(self._log_text)
        
        # 设置默认尺寸（不设置过小的最小值，以便可以调整大小）
        self.setMinimumWidth(150)
        self.setMinimumHeight(100)
    
    def append_log(self, message: str, level: str = "INFO") -> None:
        """
        添加日志条目
        
        Args:
            message: 日志消息
            level: 日志级别，可选值：INFO, WARN, ERROR, DEBUG
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据级别设置颜色（Fluent Design 调色板）
        color_map = {
            "INFO": "#0078D4",    # Fluent 蓝色
            "WARN": "#CA5010",    # Fluent 橙色
            "ERROR": "#D13438",   # Fluent 红色
            "DEBUG": "#6D6D6D",   # 灰色
        }
        color = color_map.get(level.upper(), "#323130")
        
        # 格式化日志条目
        html = f'<span style="color: #888;">[{timestamp}]</span> '
        html += f'<span style="color: {color};">{message}</span><br>'
        
        self._log_text.insertHtml(html)
        
        # 滚动到底部
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 发射信号
        self.log_added.emit(message, level)
    
    def clear_log(self) -> None:
        """清空日志"""
        self._log_text.clear()
    
    def get_log_text(self) -> str:
        """获取所有日志文本（纯文本格式）"""
        return self._log_text.toPlainText()
    
    def set_allowed_areas(self, areas: Qt.DockWidgetArea) -> None:
        """设置允许停靠的区域"""
        self.setAllowedAreas(areas)
    
    def set_floatable(self, floatable: bool) -> None:
        """设置是否可浮动"""
        features = self.features()
        if floatable:
            features |= QDockWidget.DockWidgetFeature.DockWidgetFloatable
        else:
            features &= ~QDockWidget.DockWidgetFeature.DockWidgetFloatable
        self.setFeatures(features)
    
    def set_closable(self, closable: bool) -> None:
        """设置是否可关闭"""
        features = self.features()
        if closable:
            features |= QDockWidget.DockWidgetFeature.DockWidgetClosable
        else:
            features &= ~QDockWidget.DockWidgetFeature.DockWidgetClosable
        self.setFeatures(features)
