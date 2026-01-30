from pathlib import Path
import sys

# 添加父目录到路径，以便导入 fluent_qss
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget
)

from fluent_qss import FluentSideMenu, FluentTheme


class BasePage(QWidget):
    """页面基类"""
    def __init__(self, title):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #333;")
        self.main_layout.addWidget(title_label)
        self.main_layout.addSpacing(20)

class HomePage(BasePage):
    def __init__(self):
        super().__init__("主页")
        self.main_layout.addWidget(QLabel("欢迎回来！这里是您的仪表盘。"))
        self.main_layout.addSpacing(10)
        btn = QPushButton("查看最新动态")
        btn.setFixedSize(150, 35)
        self.main_layout.addWidget(btn)

class MusicPage(BasePage):
    def __init__(self):
        super().__init__("音乐库")
        self.main_layout.addWidget(QLabel("我的播放列表:"))
        self.main_layout.addSpacing(10)
        for i in range(1, 4):
            self.main_layout.addWidget(QLabel(f"🎵 歌曲 {i} - 艺术家"))

class SettingsPage(BasePage):
    def __init__(self):
        super().__init__("设置")
        self.main_layout.addWidget(QPushButton("通用设置"))
        self.main_layout.addWidget(QPushButton("账户安全"))
        self.main_layout.addWidget(QPushButton("关于软件"))

class GenericPage(BasePage):
    """通用页面，用于未具体实现的模块"""
    def __init__(self, title, content):
        super().__init__(title)
        self.main_layout.addWidget(QLabel(content))

class DemoSideMenuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluent Side Menu Demo")
        self.resize(1000, 600)
        
        # 使用 FluentTheme 加载样式表
        self.theme = FluentTheme()
        self.theme.apply(self)
            
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 侧边菜单
        self.side_menu = FluentSideMenu()
        layout.addWidget(self.side_menu)
        
        # 内容区域
        self.stacked_widget = QStackedWidget()
        content_container = QWidget()
        content_container.setStyleSheet("background-color: #FFFFFF;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.addWidget(self.stacked_widget)
        
        layout.addWidget(content_container)
        
        # --- 1. 添加主要功能页面 ---
        # 格式: (图标, 标题, 页面实例)
        pages_config = [
            ("🏠", "主页", HomePage()),
            ("🎵", "音乐库", MusicPage()),
            ("🎥", "视频库", GenericPage("视频库", "这里管理您的所有视频文件")),
            ("📷", "相册", GenericPage("相册", "浏览您的精彩瞬间")),
            ("📁", "文件夹", GenericPage("文件夹", "本地文件浏览")),
        ]
        
        for i, (icon, title, page) in enumerate(pages_config):
            self.side_menu.add_item(icon, title, i)
            self.stacked_widget.addWidget(page)
            
        # --- 2. 添加底部功能页面 ---
        bottom_start_index = len(pages_config)
        
        # 用户页 (使用通用页)
        self.side_menu.add_bottom_item("👤", "用户", bottom_start_index)
        self.stacked_widget.addWidget(GenericPage("用户中心", "管理您的个人信息"))
        
        # 设置页 (使用专用页)
        self.side_menu.add_bottom_item("⚙", "设置", bottom_start_index + 1)
        self.stacked_widget.addWidget(SettingsPage())
            
        # 连接信号
        self.side_menu.button_group.idClicked.connect(self.stacked_widget.setCurrentIndex)
        
        # 默认选中第一项
        if self.side_menu.menu_items:
            self.side_menu.menu_items[0].setChecked(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DemoSideMenuWindow()
    window.show()
    sys.exit(app.exec())
