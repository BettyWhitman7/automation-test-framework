"""
完整的Fluent Design QSS 控件展示应用
展示并测试所有支持的PyQt6/PySide6控件
包含 Toast通知、文件选择、颜色选择等功能
"""


from pathlib import Path
import sys

# 添加父目录到路径，以便导入 fluent_qss
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtCore import QDate, QDateTime, QTime, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFontComboBox,
    QGroupBox,
    QHBoxLayout,
    QLCDNumber,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTimeEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fluent_qss import FluentTheme, show_toast


class FluentWidgetsShowcase(QMainWindow):
    """Fluent Design 组件展示应用"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluent Design QSS - 完整控件展示")
        self.setGeometry(50, 50, 1600, 900)
        
        # 初始化主题管理器
        self.theme = FluentTheme()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建主窗口
        self.create_main_content()
        
        # 创建停靠窗口
        self.create_dock_widget()
        
        # 创建状态栏
        self.statusBar().showMessage("准备就绪 - 所有Fluent Design控件已加载")
        
        # 加载样式
        self.load_stylesheet()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        file_menu.addAction("新建(&N)")
        file_menu.addAction("打开(&O)")
        file_menu.addAction("保存(&S)")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("退出(&E)")
        exit_action.triggered.connect(self.close)
        
        # 视图菜单 - 添加主题切换
        view_menu = menubar.addMenu("视图(&V)")
        view_menu.addAction("工具栏")
        view_menu.addAction("状态栏")
        view_menu.addSeparator()
        self.theme_action = view_menu.addAction("切换深色主题")
        self.theme_action.setCheckable(True)
        self.theme_action.triggered.connect(self.toggle_theme)
        edit_menu = menubar.addMenu("编辑(&E)")
        edit_menu.addAction("撤销(&U)")
        edit_menu.addAction("重做(&R)")
        edit_menu.addSeparator()
        edit_menu.addAction("剪切(&X)")
        edit_menu.addAction("复制(&C)")
        edit_menu.addAction("粘贴(&V)")
        
        # 查看菜单
        view_menu = menubar.addMenu("查看(&V)")
        view_menu.addAction("工具栏")
        view_menu.addAction("状态栏")
        view_menu.addAction("停靠窗口")
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = help_menu.addAction("关于(&A)")
        about_action.triggered.connect(
            lambda: QMessageBox.information(
                self, 
                "关于",
                "Fluent Design QSS 完整控件展示应用\n\n"
                "该应用展示了PySide6中所有支持的控件，\n"
                "并应用了Microsoft Fluent设计语言风格。"
            )
        )
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("工具栏")
        toolbar.setMovable(False)
        
        toolbar.addAction("新建")
        toolbar.addAction("打开")
        toolbar.addAction("保存")
        toolbar.addSeparator()
        toolbar.addAction("剪切")
        toolbar.addAction("复制")
        toolbar.addAction("粘贴")
        toolbar.addSeparator()
        toolbar.addSeparator()
        self.theme_btn = toolbar.addAction("🌙 切换主题")
        self.theme_btn.triggered.connect(self.toggle_theme)
        toolbar.addSeparator()
        toolbar.addAction("帮助")
    
    def create_dock_widget(self):
        """创建停靠窗口"""
        dock = QDockWidget("属性面板", self)
        dock_content = QWidget()
        dock_layout = QVBoxLayout()
        
        dock_layout.addWidget(QLabel("停靠窗口面板"))
        dock_layout.addWidget(QLineEdit("属性值"))
        dock_layout.addWidget(QPushButton("应用"))
        dock_layout.addStretch()
        
        dock_content.setLayout(dock_layout)
        dock.setWidget(dock_content)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
    
    def create_main_content(self):
        """创建主内容区域"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout()
        
        # 创建标签页
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # 添加各个标签页
        tabs.addTab(self.create_basic_controls_tab(), "基础控件")
        tabs.addTab(self.create_input_controls_tab(), "输入控件")
        tabs.addTab(self.create_selection_controls_tab(), "选择控件")
        tabs.addTab(self.create_advanced_controls_tab(), "高级控件")
        tabs.addTab(self.create_view_controls_tab(), "视图控件")
        tabs.addTab(self.create_display_controls_tab(), "显示控件")
        tabs.addTab(self.create_date_time_tab(), "日期时间")
        tabs.addTab(self.create_dialog_tab(), "对话框")
        
        main_widget.setLayout(main_layout)
    
    def create_basic_controls_tab(self):
        """基础控件标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("═" * 60))
        layout.addWidget(QLabel("基础控件演示"))
        layout.addWidget(QLabel("═" * 60))
        
        # QPushButton - 按钮
        layout.addWidget(QLabel("\n▶ QPushButton - 按钮"))
        btn_layout = QHBoxLayout()
        
        primary_btn = QPushButton("主要按钮（蓝色）")
        primary_btn.clicked.connect(lambda: self.statusBar().showMessage("点击了主要按钮"))
        
        secondary_btn = QPushButton("次要按钮（灰色）")
        secondary_btn.setObjectName("secondaryButton")
        
        disabled_btn = QPushButton("禁用按钮")
        disabled_btn.setDisabled(True)
        
        btn_layout.addWidget(primary_btn)
        btn_layout.addWidget(secondary_btn)
        btn_layout.addWidget(disabled_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # QLabel - 标签
        layout.addWidget(QLabel("\n▶ QLabel - 标签"))
        normal_label = QLabel("这是一个普通标签")
        disabled_label = QLabel("这是一个禁用标签")
        disabled_label.setDisabled(True)
        layout.addWidget(normal_label)
        layout.addWidget(disabled_label)
        
        # QGroupBox - 分组框
        layout.addWidget(QLabel("\n▶ QGroupBox - 分组框"))
        group_box = QGroupBox("配置选项")
        group_layout = QVBoxLayout()
        group_layout.addWidget(QCheckBox("选项 1"))
        group_layout.addWidget(QCheckBox("选项 2"))
        group_layout.addWidget(QCheckBox("选项 3"))
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_input_controls_tab(self):
        """输入控件标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("═" * 60))
        layout.addWidget(QLabel("输入控件演示"))
        layout.addWidget(QLabel("═" * 60))
        
        # QLineEdit
        layout.addWidget(QLabel("\n▶ QLineEdit - 单行文本输入"))
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("输入文本...")
        layout.addWidget(line_edit)
        
        disabled_line_edit = QLineEdit("禁用状态的输入框")
        disabled_line_edit.setDisabled(True)
        layout.addWidget(disabled_line_edit)
        
        # QTextEdit
        layout.addWidget(QLabel("\n▶ QTextEdit - 多行文本编辑"))
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("输入多行文本...")
        text_edit.setMaximumHeight(120)
        layout.addWidget(text_edit)
        
        # QComboBox
        layout.addWidget(QLabel("\n▶ QComboBox - 下拉框"))
        combo_box = QComboBox()
        combo_box.addItems(["选项1", "选项2", "选项3", "选项4", "选项5"])
        layout.addWidget(combo_box)
        
        # QFontComboBox
        layout.addWidget(QLabel("\n▶ QFontComboBox - 字体选择"))
        font_combo = QFontComboBox()
        layout.addWidget(font_combo)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_selection_controls_tab(self):
        """选择控件标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("═" * 60))
        layout.addWidget(QLabel("选择控件演示"))
        layout.addWidget(QLabel("═" * 60))
        
        # QCheckBox
        layout.addWidget(QLabel("\n▶ QCheckBox - 复选框"))
        check_layout = QVBoxLayout()
        check_layout.addWidget(QCheckBox("选项 1"))
        check_layout.addWidget(QCheckBox("选项 2"))
        check3 = QCheckBox("选项 3（已选中）")
        check3.setChecked(True)
        check_layout.addWidget(check3)
        check4 = QCheckBox("选项 4（禁用）")
        check4.setEnabled(False)
        check_layout.addWidget(check4)
        layout.addLayout(check_layout)
        
        # QRadioButton
        layout.addWidget(QLabel("\n▶ QRadioButton - 单选按钮"))
        radio_layout = QVBoxLayout()
        radio_layout.addWidget(QRadioButton("选项 A"))
        radioB = QRadioButton("选项 B（已选中）")
        radioB.setChecked(True)
        radio_layout.addWidget(radioB)
        radioC = QRadioButton("选项 C（禁用）")
        radioC.setEnabled(False)
        radio_layout.addWidget(radioC)
        layout.addLayout(radio_layout)
        
        # QSlider
        layout.addWidget(QLabel("\n▶ QSlider - 滑块"))
        h_slider = QSlider(Qt.Orientation.Horizontal)
        h_slider.setRange(0, 100)
        h_slider.setValue(50)
        layout.addWidget(h_slider)
        
        layout.addWidget(QLabel("垂直滑块:"))
        slider_layout = QHBoxLayout()
        v_slider = QSlider(Qt.Orientation.Vertical)
        v_slider.setRange(0, 100)
        v_slider.setValue(50)
        v_slider.setMaximumHeight(100)
        slider_layout.addWidget(v_slider)
        slider_layout.addStretch()
        layout.addLayout(slider_layout)
        
        # QProgressBar
        layout.addWidget(QLabel("\n▶ QProgressBar - 进度条"))
        progress1 = QProgressBar()
        progress1.setValue(30)
        layout.addWidget(progress1)
        
        progress2 = QProgressBar()
        progress2.setValue(75)
        layout.addWidget(progress2)
        
        progress3 = QProgressBar()
        progress3.setValue(100)
        layout.addWidget(progress3)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_controls_tab(self):
        """高级控件标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("═" * 60))
        layout.addWidget(QLabel("高级控件演示"))
        layout.addWidget(QLabel("═" * 60))
        
        # QSpinBox
        layout.addWidget(QLabel("\n▶ QSpinBox - 整数输入框"))
        spin_box = QSpinBox()
        spin_box.setRange(0, 100)
        spin_box.setValue(50)
        layout.addWidget(spin_box)
        
        # QDoubleSpinBox
        layout.addWidget(QLabel("\n▶ QDoubleSpinBox - 浮点数输入框"))
        double_spin = QDoubleSpinBox()
        double_spin.setRange(0.0, 100.0)
        double_spin.setValue(50.5)
        double_spin.setDecimals(2)
        layout.addWidget(double_spin)
        
        # QDial
        layout.addWidget(QLabel("\n▶ QDial - 旋钮"))
        dial = QDial()
        dial.setRange(0, 100)
        dial.setValue(50)
        dial.setMaximumHeight(100)
        layout.addWidget(dial)
        
        # QLCDNumber
        layout.addWidget(QLabel("\n▶ QLCDNumber - LCD数字显示"))
        lcd = QLCDNumber()
        lcd.setDigitCount(5)
        lcd.display(12345)
        layout.addWidget(lcd)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_view_controls_tab(self):
        """视图控件标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("═" * 60))
        layout.addWidget(QLabel("视图控件演示"))
        layout.addWidget(QLabel("═" * 60))
        
        # QListWidget
        layout.addWidget(QLabel("\n▶ QListWidget - 列表视图"))
        list_widget = QListWidget()
        for i in range(1, 6):
            list_widget.addItem(QListWidgetItem(f"列表项目 {i}"))
        list_widget.setMaximumHeight(120)
        layout.addWidget(list_widget)
        
        # QTreeWidget
        layout.addWidget(QLabel("\n▶ QTreeWidget - 树形视图"))
        tree_widget = QTreeWidget()
        tree_widget.setHeaderLabels(["名称", "值"])
        
        root = QTreeWidgetItem(tree_widget)
        root.setText(0, "根目录")
        root.setText(1, "值1")
        
        for i in range(1, 4):
            child = QTreeWidgetItem(root)
            child.setText(0, f"子项 {i}")
            child.setText(1, f"值 {i}")
        
        tree_widget.setMaximumHeight(120)
        layout.addWidget(tree_widget)
        
        # QTableWidget
        layout.addWidget(QLabel("\n▶ QTableWidget - 表格视图"))
        table_widget = QTableWidget()
        table_widget.setColumnCount(3)
        table_widget.setRowCount(4)
        table_widget.setHorizontalHeaderLabels(["列1", "列2", "列3"])
        
        for row in range(4):
            for col in range(3):
                item = QTableWidgetItem(f"单元格 {row+1}x{col+1}")
                table_widget.setItem(row, col, item)
        
        table_widget.setMaximumHeight(150)
        layout.addWidget(table_widget)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_display_controls_tab(self):
        """显示控件标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("═" * 60))
        layout.addWidget(QLabel("显示控件演示"))
        layout.addWidget(QLabel("═" * 60))
        
        # 分割视图
        layout.addWidget(QLabel("\n▶ QSplitter - 分割视图"))
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("左侧内容"))
        left_list = QListWidget()
        left_list.addItems(["项目1", "项目2", "项目3"])
        left_layout.addWidget(left_list)
        left_widget.setLayout(left_layout)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("右侧内容"))
        right_text = QTextEdit()
        right_text.setText("这是右侧的文本内容区域")
        right_layout.addWidget(right_text)
        right_widget.setLayout(right_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # 滚动区域
        layout.addWidget(QLabel("\n▶ QScrollArea - 滚动区域"))
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        for i in range(10):
            scroll_layout.addWidget(QLabel(f"滚动项目 {i+1}"))
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)  # 确保内容可以正确调整大小
        scroll_area.setMaximumHeight(150)
        layout.addWidget(scroll_area)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_date_time_tab(self):
        """日期时间控件标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("═" * 60))
        layout.addWidget(QLabel("日期时间控件演示"))
        layout.addWidget(QLabel("═" * 60))
        
        # QDateEdit
        layout.addWidget(QLabel("\n▶ QDateEdit - 日期选择"))
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        layout.addWidget(date_edit)
        
        # QTimeEdit
        layout.addWidget(QLabel("\n▶ QTimeEdit - 时间选择"))
        time_edit = QTimeEdit()
        time_edit.setTime(QTime.currentTime())
        layout.addWidget(time_edit)
        
        # QDateTimeEdit
        layout.addWidget(QLabel("\n▶ QDateTimeEdit - 日期时间选择"))
        datetime_edit = QDateTimeEdit()
        datetime_edit.setDateTime(QDateTime.currentDateTime())
        layout.addWidget(datetime_edit)
        
        # QCalendarWidget
        layout.addWidget(QLabel("\n▶ QCalendarWidget - 日历"))
        calendar = QCalendarWidget()
        calendar.setSelectedDate(QDate.currentDate())
        calendar.setMaximumHeight(300)
        layout.addWidget(calendar)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_dialog_tab(self):
        """对话框标签页 - 文件选择、颜色选择、Toast通知"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("═" * 60))
        layout.addWidget(QLabel("对话框和通知演示"))
        layout.addWidget(QLabel("═" * 60))
        
        # Toast 通知
        layout.addWidget(QLabel("\n▶ Toast 通知"))
        toast_layout = QHBoxLayout()
        
        toast_info_btn = QPushButton("信息通知")
        toast_info_btn.clicked.connect(
            lambda: (
                show_toast("✓ 操作成功完成！", duration=3000, parent=self),
                self.statusBar().showMessage("显示了信息通知")
            )
        )
        
        toast_warning_btn = QPushButton("警告通知")
        toast_warning_btn.setObjectName("secondaryButton")
        toast_warning_btn.clicked.connect(
            lambda: (
                show_toast("⚠ 请检查输入内容！", duration=3000, parent=self),
                self.statusBar().showMessage("显示了警告通知")
            )
        )
        
        toast_error_btn = QPushButton("错误通知")
        toast_error_btn.setObjectName("secondaryButton")
        toast_error_btn.clicked.connect(
            lambda: (
                show_toast("✗ 操作失败，请重试！", duration=3000, parent=self),
                self.statusBar().showMessage("显示了错误通知")
            )
        )
        
        toast_layout.addWidget(toast_info_btn)
        toast_layout.addWidget(toast_warning_btn)
        toast_layout.addWidget(toast_error_btn)
        toast_layout.addStretch()
        
        layout.addLayout(toast_layout)
        
        # 文件选择
        layout.addWidget(QLabel("\n▶ QFileDialog - 文件选择"))
        file_layout = QHBoxLayout()
        
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("color: #A19F9D; padding: 8px;")
        
        open_file_btn = QPushButton("打开文件")
        open_file_btn.clicked.connect(self.open_file_dialog)
        
        open_folder_btn = QPushButton("选择文件夹")
        open_folder_btn.clicked.connect(self.open_folder_dialog)
        
        save_file_btn = QPushButton("保存文件")
        save_file_btn.clicked.connect(self.save_file_dialog)
        
        file_layout.addWidget(open_file_btn)
        file_layout.addWidget(open_folder_btn)
        file_layout.addWidget(save_file_btn)
        file_layout.addStretch()
        
        layout.addLayout(file_layout)
        layout.addWidget(self.file_path_label)
        
        # 颜色选择
        layout.addWidget(QLabel("\n▶ QColorDialog - 颜色选择"))
        color_layout = QHBoxLayout()
        
        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self.open_color_dialog)
        
        self.color_preview = QLabel("     ")
        self.color_preview.setStyleSheet("""
            QLabel {
                background-color: #0078D4;
                border: 1px solid #D1D1D1;
                border-radius: 4px;
                min-width: 80px;
                min-height: 40px;
            }
        """)
        
        self.color_value_label = QLabel("RGB: (0, 120, 212)")
        self.color_value_label.setStyleSheet("color: #323130;")
        
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(QLabel("颜色预览:"))
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_value_label)
        color_layout.addStretch()
        
        layout.addLayout(color_layout)
        
        # 字体选择
        layout.addWidget(QLabel("\n▶ QFontDialog - 字体选择"))
        font_layout = QHBoxLayout()
        
        choose_font_btn = QPushButton("选择字体")
        choose_font_btn.clicked.connect(self.open_font_dialog)
        
        self.font_preview = QLabel("这是字体预览文本")
        self.font_preview.setStyleSheet("padding: 8px;")
        
        font_layout.addWidget(choose_font_btn)
        font_layout.addWidget(self.font_preview)
        font_layout.addStretch()
        
        layout.addLayout(font_layout)
        
        # 消息对话框
        layout.addWidget(QLabel("\n▶ QMessageBox - 消息对话框"))
        msg_layout = QHBoxLayout()
        
        info_msg_btn = QPushButton("信息对话框")
        info_msg_btn.clicked.connect(
            lambda: QMessageBox.information(self, "信息", "这是一条信息消息")
        )
        
        warning_msg_btn = QPushButton("警告对话框")
        warning_msg_btn.setObjectName("secondaryButton")
        warning_msg_btn.clicked.connect(
            lambda: QMessageBox.warning(self, "警告", "这是一条警告消息")
        )
        
        error_msg_btn = QPushButton("错误对话框")
        error_msg_btn.setObjectName("secondaryButton")
        error_msg_btn.clicked.connect(
            lambda: QMessageBox.critical(self, "错误", "这是一条错误消息")
        )
        
        question_msg_btn = QPushButton("问题对话框")
        question_msg_btn.clicked.connect(
            lambda: self.handle_question_dialog()
        )
        
        msg_layout.addWidget(info_msg_btn)
        msg_layout.addWidget(warning_msg_btn)
        msg_layout.addWidget(error_msg_btn)
        msg_layout.addWidget(question_msg_btn)
        msg_layout.addStretch()
        
        layout.addLayout(msg_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def open_file_dialog(self):
        """打开文件对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            str(Path.home()),
            "所有文件 (*);;文本文件 (*.txt);;Python文件 (*.py)"
        )
        
        if file_path:
            self.file_path_label.setText(f"已选择: {file_path}")
            show_toast(f"✓ 选择文件成功: {Path(file_path).name}", parent=self)
            self.statusBar().showMessage(f"选择的文件: {file_path}")
        else:
            show_toast("✗ 未选择任何文件", parent=self)
    
    def open_folder_dialog(self):
        """打开文件夹对话框"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹",
            str(Path.home())
        )
        
        if folder_path:
            self.file_path_label.setText(f"已选择: {folder_path}")
            show_toast(f"✓ 选择文件夹成功: {Path(folder_path).name}", parent=self)
            self.statusBar().showMessage(f"选择的文件夹: {folder_path}")
        else:
            show_toast("✗ 未选择任何文件夹", parent=self)
    
    def save_file_dialog(self):
        """保存文件对话框"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            str(Path.home() / "未命名.txt"),
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            self.file_path_label.setText(f"保存到: {file_path}")
            show_toast(f"✓ 保存文件位置已确定: {Path(file_path).name}", parent=self)
            self.statusBar().showMessage(f"保存路径: {file_path}")
        else:
            show_toast("✗ 未保存文件", parent=self)
    
    def open_color_dialog(self):
        """打开颜色选择对话框"""
        color = QColorDialog.getColor(
            QColor("#0078D4"),
            self,
            "选择颜色"
        )
        
        if color.isValid():
            # 更新颜色预览
            hex_color = color.name()
            self.color_preview.setStyleSheet(f"""
                QLabel {{
                    background-color: {hex_color};
                    border: 1px solid #D1D1D1;
                    border-radius: 4px;
                    min-width: 80px;
                    min-height: 40px;
                }}
            """)
            
            # 更新颜色值标签
            r, g, b, _ = color.getRgb()  # type: ignore
            self.color_value_label.setText(f"RGB: ({r}, {g}, {b})\nHEX: {hex_color}")
            
            show_toast(f"✓ 颜色已选择: {hex_color}", parent=self)
            self.statusBar().showMessage(f"选择的颜色: RGB({r}, {g}, {b}) {hex_color}")
        else:
            show_toast("✗ 未选择颜色", parent=self)
    
    def open_font_dialog(self):
        """打开字体选择对话框"""
        from PySide6.QtWidgets import QFontDialog
        from PySide6.QtGui import QFont
        
        # QFontDialog.getFont() 返回 (bool, QFont) 元组
        ok, font = QFontDialog.getFont(
            QFont("Segoe UI", 10),
            self,
            "选择字体"
        )
        
        if ok:
            # 更新字体预览
            self.font_preview.setFont(font)
            self.font_preview.setText(f"字体: {font.family()}, 大小: {font.pointSize()}pt")
            
            show_toast(f"✓ 字体已选择: {font.family()}", parent=self)
            self.statusBar().showMessage(f"字体: {font.family()} ({font.pointSize()}pt)")
        else:
            show_toast("✗ 未选择字体", parent=self)
    
    def handle_question_dialog(self):
        """处理问题对话框"""
        reply = QMessageBox.question(
            self,
            "问题",
            "您确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            show_toast("✓ 您选择了 是", parent=self)
            self.statusBar().showMessage("用户点击了 '是'")
        else:
            show_toast("✓ 您选择了 否", parent=self)
            self.statusBar().showMessage("用户点击了 '否'")
    
    def toggle_theme(self):
        """切换亮色/暗色主题"""
        self.theme.toggle(self)
        
        if self.theme.is_dark:
            self.theme_action.setChecked(True)
            self.theme_btn.setText("☀️ 切换亮色")
        else:
            self.theme_action.setChecked(False)
            self.theme_btn.setText("🌙 切换暗色")
        
        theme_name = "暗色" if self.theme.is_dark else "亮色"
        self.statusBar().showMessage(f"✓ Fluent Design {theme_name}主题已加载")

    def load_stylesheet(self):
        """加载QSS样式表"""
        self.theme.apply(self)
        theme_name = "暗色" if self.theme.is_dark else "亮色"
        self.statusBar().showMessage(f"✓ Fluent Design {theme_name}主题已加载")


def main():
    app = QApplication(sys.argv)
    
    # 设置应用风格
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = FluentWidgetsShowcase()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
