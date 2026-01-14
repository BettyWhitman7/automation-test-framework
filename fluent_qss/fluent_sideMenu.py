from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy


class FluentSideMenuItem(QPushButton):
    """侧边菜单项"""
    def __init__(self, icon_text, text, parent=None):
        super().__init__(parent)
        self.icon_text = icon_text
        self.text_label = text
        self.setCheckable(True)
        self.setAutoExclusive(True)
        # 移除前导空格，确保图标位置固定
        self.setText(f"{icon_text}    {text}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setObjectName("SideMenuItem")
        
    def set_collapsed(self, collapsed):
        if collapsed:
            self.setText(f"{self.icon_text}")
            self.setToolTip(self.text_label)
        else:
            # 保持一致的格式，无前导空格
            self.setText(f"{self.icon_text}    {self.text_label}")
            self.setToolTip("")

class FluentSideMenu(QWidget):
    """侧边菜单"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.is_collapsed = False
        self.setObjectName("SideMenu")
        # 启用样式背景绘制
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(8, 10, 8, 10)
        self.v_layout.setSpacing(4)
        
        # 顶部折叠按钮
        self.toggle_btn = FluentSideMenuItem("☰", "菜单", self)
        self.toggle_btn.setCheckable(False)
        self.toggle_btn.setAutoExclusive(False)
        self.toggle_btn.clicked.connect(self.toggle_menu)
        self.v_layout.addWidget(self.toggle_btn)
        
        self.v_layout.addSpacing(10)
        
        self.menu_items = []
        self.button_group = QButtonGroup(self)
        
        # 使用 QSpacerItem 作为伸缩占位符，以便在其前后插入
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.v_layout.addItem(self.verticalSpacer)
        
    def add_item(self, icon, text, page_index):
        item = FluentSideMenuItem(icon, text, self)
        
        # 查找 spacer 的位置并插入到它之前
        index = -1
        for i in range(self.v_layout.count()):
            if self.v_layout.itemAt(i) == self.verticalSpacer:
                index = i
                break
        
        if index != -1:
            self.v_layout.insertWidget(index, item)
        else:
            self.v_layout.addWidget(item)
            
        self.menu_items.append(item)
        if page_index >= 0:
            self.button_group.addButton(item, page_index)
        return item

    def add_bottom_item(self, icon, text, page_index=-1):
        """添加底部菜单项"""
        item = FluentSideMenuItem(icon, text, self)
        self.v_layout.addWidget(item)
        self.menu_items.append(item)
        if page_index >= 0:
            self.button_group.addButton(item, page_index)
        return item
        
    def toggle_menu(self):
        self.is_collapsed = not self.is_collapsed
        width = 70 if self.is_collapsed else 180

        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(width)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.start()
        
        self.animation_max = QPropertyAnimation(self, b"maximumWidth")
        self.animation_max.setDuration(250)
        self.animation_max.setStartValue(self.width())
        self.animation_max.setEndValue(width)
        self.animation_max.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation_max.start()
        
        self.toggle_btn.set_collapsed(self.is_collapsed)
        for item in self.menu_items:
            item.set_collapsed(self.is_collapsed)
