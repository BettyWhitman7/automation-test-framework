import sys
import os
import importlib
import datetime
import json
from config import Config
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeView,
    QTableView,
    QTextEdit,
    QPushButton,
    QSplitter,
    QLabel,
    QProgressBar,
    QLineEdit,
    QStatusBar,
    QToolBar,
    QHeaderView,
    QDialog,
    QSpinBox,
    QDialogButtonBox,
    QFormLayout,
    QCheckBox,
    QGroupBox,
    QAbstractItemView,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from PySide6.QtCore import Qt, QObject, QThread, Signal, QTimer
from tools.load_yaml import load_yaml_config
from testCaseModel import TestCaseModel
from fluent_qss import FluentTheme, FluentMessageBox, show_toast
from fluent_qss.fluent_dock_log_panel import FluentDockLogPanel
from tools.log_tool import setup_logger, get_logger


# 多轮测试设置对话框
class MultiRoundTestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("多轮测试设置")
        self.setModal(True)
        self.resize(300, 200)

        layout = QFormLayout()

        # 测试轮数设置
        self.rounds_spinbox = QSpinBox()
        self.rounds_spinbox.setMinimum(1)
        self.rounds_spinbox.setMaximum(9999)
        self.rounds_spinbox.setValue(1)
        layout.addRow("测试轮数:", self.rounds_spinbox)

        # 失败停止选项
        self.stop_on_fail_checkbox = QCheckBox()
        self.stop_on_fail_checkbox.setChecked(False)
        layout.addRow("失败时停止:", self.stop_on_fail_checkbox)

        # 轮次间延时
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setMinimum(0)
        self.delay_spinbox.setMaximum(60)
        self.delay_spinbox.setValue(1)
        self.delay_spinbox.setSuffix(" 秒")
        layout.addRow("轮次间延时:", self.delay_spinbox)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_settings(self):
        return {
            "rounds": self.rounds_spinbox.value(),
            "stop_on_fail": self.stop_on_fail_checkbox.isChecked(),
            "delay": self.delay_spinbox.value(),
        }


class TestWorker(QObject):
    finished = Signal(str, str, str, int)  # case_name, result, message, round_num
    all_finished = Signal()
    log = Signal(str, str)
    round_finished = Signal(int)

    def __init__(self, cases_to_run, test_settings=None):
        super().__init__()
        self.cases_to_run = cases_to_run
        self.is_running = True
        self.test_settings = test_settings or {
            "rounds": 1,
            "stop_on_fail": False,
            "delay": 1,
        }

    def run(self):
        try:
            total_rounds = self.test_settings["rounds"]

            for current_round in range(1, total_rounds + 1):
                if not self.is_running:
                    self.log.emit("测试执行被用户中断。", "WARNING")
                    break

                self.log.emit(f"开始第 {current_round}/{total_rounds} 轮测试", "INFO")

                round_has_failure = False

                for case_name, case_details in self.cases_to_run:
                    if not self.is_running:
                        self.log.emit("测试执行被用户中断。", "WARNING")
                        break

                    try:
                        self.log.emit(
                            f"[轮次 {current_round}] 正在执行: {case_name}...", "INFO"
                        )

                        # 根据您的配置格式解析
                        # case_details 格式: [项目名, 模块文件, 类名, 其他参数...]
                        if len(case_details) < 3:
                            self.log.emit(f"测试用例 {case_name} 配置不完整", "ERROR")
                            self.finished.emit(
                                case_name, "Error", "配置不完整", current_round
                            )
                            round_has_failure = True
                            continue

                        project_name = case_details[0]  # 项目名，如 "zhongqi"
                        module_file = case_details[
                            1
                        ]  # 模块文件，如 "zhongqi_Phone_case.py"
                        class_name = case_details[2]  # 类名，如 "DialingKeyboard_UI"
                        test_data = case_details[3:] if len(case_details) > 3 else {}

                        # 构建模块导入路径
                        module_name = module_file.replace(".py", "")

                        # 构建导入路径
                        module_import_path = f"case_script.{project_name}.{module_name}"

                        self.log.emit(f"正在导入模块: {module_import_path}", "INFO")

                        # 动态导入模块
                        module = importlib.import_module(module_import_path)

                        if not hasattr(module, class_name):
                            error_msg = (
                                f"模块 {module_import_path} 中未找到类 {class_name}"
                            )
                            self.log.emit(error_msg, "ERROR")
                            self.finished.emit(
                                case_name, "Error", error_msg, current_round
                            )
                            round_has_failure = True
                            continue

                        # 获取测试类
                        test_class = getattr(module, class_name)

                        # 创建测试实例，传入测试数据
                        test_instance = test_class(test_data)

                        # 执行测试
                        if hasattr(test_instance, "run"):
                            # 调用 run 方法
                            result, message = test_instance.run()

                            if result:
                                self.finished.emit(
                                    case_name, "Pass", message, current_round
                                )
                            else:
                                self.finished.emit(
                                    case_name, "Fail", message, current_round
                                )
                                round_has_failure = True
                        else:
                            # 如果没有 run 方法，直接调用实例
                            test_instance()
                            self.finished.emit(
                                case_name, "Pass", "执行完成（无返回值）", current_round
                            )

                    except ImportError as e:
                        error_msg = f"导入模块失败: {str(e)}"
                        self.log.emit(error_msg, "ERROR")
                        self.finished.emit(case_name, "Error", error_msg, current_round)
                        round_has_failure = True

                    except AttributeError as e:
                        error_msg = f"类或方法不存在: {str(e)}"
                        self.log.emit(error_msg, "ERROR")
                        self.finished.emit(case_name, "Error", error_msg, current_round)
                        round_has_failure = True

                    except Exception as e:
                        error_msg = f"执行测试用例时出错: {str(e)}"
                        self.log.emit(error_msg, "ERROR")
                        self.finished.emit(case_name, "Error", error_msg, current_round)
                        round_has_failure = True

                self.round_finished.emit(current_round)

                # 如果设置了失败停止且本轮有失败，则停止
                if self.test_settings["stop_on_fail"] and round_has_failure:
                    self.log.emit(
                        f"第 {current_round} 轮测试有失败，根据设置停止后续测试",
                        "WARNING",
                    )
                    break

                # 轮次间延时（除了最后一轮）
                if current_round < total_rounds and self.is_running:
                    delay = self.test_settings["delay"]
                    if delay > 0:
                        self.log.emit(f"等待 {delay} 秒后开始下一轮测试...", "INFO")
                        import time

                        time.sleep(delay)

        except Exception as e:
            error_msg = f"测试执行过程中发生未处理的异常: {str(e)}"
            self.log.emit(error_msg, "ERROR")
            import traceback

            self.log.emit(f"异常详情: {traceback.format_exc()}", "ERROR")

        finally:
            # run方法结束时，发出 all_finished 信号
            self.all_finished.emit()

    def stop(self):
        self.is_running = False


class MainWindow(QMainWindow):
    """
    自动化测试框架主窗口
    
    代码结构:
    - 初始化方法: __init__, _init_data, _init_widgets, _init_ui, _init_connections
    - UI 构建方法: _create_toolbar, _create_grouped_layout, _setup_table_properties
    - 项目加载方法: _load_project_tree, _load_test_suite, _parse_test_cases
    - 测试执行方法: start_test, stop_test, restart_test
    - 测试回调方法: _on_test_finished, _on_round_finished, _on_all_tests_finished
    - UI 更新方法: _update_stats_ui, _update_button_states, log_message
    - 用例选择方法: select_all, select_none, select_inverse, filter_test_cases
    """

    # ========== 初始化方法 ==========

    def __init__(self):
        super().__init__()
        self.setWindowTitle("自动化测试框架")
        self.setGeometry(100, 100, 1400, 800)

        # 初始化日志系统
        self.logger = get_logger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("自动化测试框架启动") 
        self.logger.info("=" * 60)

        # 初始化主题
        self.theme = FluentTheme()
        self.theme.apply(QApplication.instance())
        self.logger.debug("主题系统初始化完成")

        # 按顺序初始化各部分
        self._init_data()
        self._init_widgets()
        self._init_ui()
        self._init_connections()

        # 加载项目数据
        self._load_project_tree()
        
        self.logger.success("主窗口初始化完成")

    def _init_data(self):
        """初始化数据和状态变量"""
        self.logger.debug("开始初始化数据和状态变量")
        
        # 测试用例模型
        self.test_case_model = TestCaseModel()

        # 项目配置
        self.project_config = {}
        self.current_project_name = ""
        self.current_test_suite = ""
        self.test_cases_config = {}

        # 线程控制
        self.test_thread = None
        self.test_worker = None
        self.is_restarting = False

        # 统计计数器
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

        # 多轮测试设置
        self.test_settings = {"rounds": 1, "stop_on_fail": False, "delay": 1}
        
        self.logger.debug("数据和状态变量初始化完成")

    def _init_widgets(self):
        """初始化所有 UI 控件"""
        self.logger.debug("开始初始化 UI 控件")
        # 测试控制按钮
        self.start_button = QPushButton("开始", self)
        self.stop_button = QPushButton("停止", self)
        self.restart_button = QPushButton("重启", self)
        self.multi_round_button = QPushButton("多轮测试设置", self)

        # 设置按钮样式标识
        self.start_button.setObjectName("successButton")
        self.stop_button.setObjectName("dangerButton")
        self.restart_button.setObjectName("warningButton")
        self.multi_round_button.setObjectName("primaryButton")

        # 统计信息标签
        self.total_label = QLabel("总数: 0", self)
        self.passed_label = QLabel("成功: 0", self)
        self.failed_label = QLabel("失败: 0", self)

        # 进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("就绪")
        self.progress_bar.setMaximumHeight(10)  # 限制进度条高度

        # 搜索框
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("搜索测试用例...")

        # 项目树视图
        self.tree_view = QTreeView(self)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setModel(QStandardItemModel())

        # 测试用例表格
        self.test_case_table = QTableView(self)
        self.test_case_table.setModel(self.test_case_model)
        self.test_case_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        # 设置最小高度，防止内容为空时表格收缩导致标题移动
        self.test_case_table.setMinimumHeight(300)
        # 强制显示垂直滚动条，防止滚动条出现/消失导致表头位置变化
        self.test_case_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # 日志面板 - 使用 FluentDockLogPanel
        self.log_panel = FluentDockLogPanel(self, title="📋 执行日志")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.log_panel)

        # 批量操作按钮
        self.select_all_button = QPushButton("全选", self)
        self.select_none_button = QPushButton("全不选", self)
        self.select_inverse_button = QPushButton("反选", self)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        self.logger.debug("UI 控件初始化完成")

    def _init_ui(self):
        """初始化 UI 布局"""
        self.logger.debug("开始初始化 UI 布局")
        self._update_button_states(is_running=False)
        self._setup_table_properties()
        self._create_toolbar()
        self._create_grouped_layout()
        
        self.logger.debug("UI 布局初始化完成")

    def _init_connections(self):
        """初始化信号连接"""
        # 测试控制按钮
        self.start_button.clicked.connect(self.start_test)
        self.stop_button.clicked.connect(self.stop_test)
        self.restart_button.clicked.connect(self.restart_test)
        self.multi_round_button.clicked.connect(self._show_multi_round_dialog)

        # 项目树
        self.tree_view.clicked.connect(self._on_tree_item_clicked)

        # 搜索筛选
        self.search_box.textChanged.connect(self.filter_test_cases)

        # 批量选择
        self.select_all_button.clicked.connect(self.select_all)
        self.select_none_button.clicked.connect(self.select_none)
        self.select_inverse_button.clicked.connect(self.select_inverse)

        # 模型更新
        self.test_case_model.case_updated.connect(self._on_case_updated)
        
        self.logger.debug("信号连接初始化完成")

    # ========== UI 构建方法 ==========

    def _create_grouped_layout(self):
        """创建分组布局以更好地组织界面元素"""
        # 控制按钮组
        control_group = QGroupBox("测试控制")
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.restart_button)
        control_layout.addWidget(self.multi_round_button)
        control_layout.addStretch(1)
        control_group.setLayout(control_layout)

        # 统计信息组
        stats_group = QGroupBox("测试统计")
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.passed_label)
        stats_layout.addWidget(self.failed_label)
        stats_layout.addStretch(1)
        stats_group.setLayout(stats_layout)

        # 项目选择组
        project_group = QGroupBox("项目与测试套件")
        project_layout = QVBoxLayout()
        project_layout.addWidget(self.tree_view)
        project_group.setLayout(project_layout)

        # 测试用例组
        testcase_group = QGroupBox("测试用例")
        testcase_layout = QVBoxLayout()
        testcase_layout.setContentsMargins(5, 10, 5, 5)  # 设置固定边距
        testcase_layout.setSpacing(5)  # 设置固定间距

        # 搜索和批量操作
        search_batch_layout = QVBoxLayout()
        search_batch_layout.addWidget(self.search_box)

        batch_layout = QHBoxLayout()
        batch_layout.addWidget(self.select_all_button)
        batch_layout.addWidget(self.select_none_button)
        batch_layout.addWidget(self.select_inverse_button)
        batch_layout.addStretch(1)
        search_batch_layout.addLayout(batch_layout)

        testcase_layout.addLayout(search_batch_layout)
        testcase_layout.addWidget(self.test_case_table)
        testcase_group.setLayout(testcase_layout)

        # 左侧面板
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(project_group)
        left_widget.setLayout(left_layout)

        # 右侧面板
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(testcase_group)
        right_widget.setLayout(right_layout)

        # 主分割器
        middle_splitter = QSplitter(Qt.Orientation.Horizontal)
        middle_splitter.addWidget(left_widget)
        middle_splitter.addWidget(right_widget)
        middle_splitter.setSizes([300, 1100])
        # 禁用子组件的收缩，保持布局稳定
        middle_splitter.setChildrenCollapsible(False)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(control_group)
        main_layout.addWidget(stats_group)
        main_layout.addWidget(middle_splitter)
        main_layout.addWidget(self.progress_bar)

        main_layout.setStretch(2, 1)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        toolbar.addAction("开始测试", self.start_test)
        toolbar.addAction("停止测试", self.stop_test)
        toolbar.addAction("重启测试", self.restart_test)
        toolbar.addAction("多轮设置", self._show_multi_round_dialog)
        toolbar.addSeparator()
        toolbar.addAction("💾 保存测试报告", self._save_test_report)
        toolbar.addAction("📋 显示/隐藏日志", self._toggle_log_panel)
        toolbar.addAction("🌓 切换主题", self._toggle_theme)

    def _toggle_theme(self):
        """切换亮色/暗色主题"""
        self.theme.toggle(QApplication.instance())
        mode = "暗色" if self.theme.is_dark else "亮色"
        self.log_message(f"已切换到{mode}主题", "INFO")
    
    def _toggle_log_panel(self):
        """切换日志面板显示/隐藏"""
        if self.log_panel.isVisible():
            self.log_panel.hide()
        else:
            self.log_panel.show()
    
    def _save_test_report(self):
        """保存测试报告"""
        try:
            # 生成报告数据
            report_data = self._generate_report_data()
            
            # 生成报告文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = self.current_project_name or "未知项目"
            suite_name = self.current_test_suite or "未知套件"
            report_filename = f"测试报告_{project_name}_{suite_name}_{timestamp}.json"
            
            # 确保报告目录存在
            report_dir = os.path.join(Config.ROOT_DIR, "test_reports")
            os.makedirs(report_dir, exist_ok=True)
            
            report_path = os.path.join(report_dir, report_filename)
            
            # 保存为JSON格式
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            self.log_message(f"测试报告已保存: {report_path}", "SUCCESS")
            self.logger.success(f"测试报告已保存: {report_path}")
            
            # 显示提示
            show_toast(f"✅ 测试报告已保存至:\n{report_filename}", duration=3000, parent=self)
            
        except Exception as e:
            error_msg = f"保存测试报告失败: {str(e)}"
            self.log_message(error_msg, "ERROR")
            self.logger.exception("保存测试报告时发生异常")
    
    def _generate_report_data(self):
        """生成测试报告数据"""
        # 收集所有测试用例的结果
        test_cases = []
        for row in range(self.test_case_model.rowCount()):
            case_name_item = self.test_case_model.item(row, 1)
            status_item = self.test_case_model.item(row, 2)
            progress_item = self.test_case_model.item(row, 3)
            exec_count_item = self.test_case_model.item(row, 4)
            fail_count_item = self.test_case_model.item(row, 5)
            result_item = self.test_case_model.item(row, 6)
            message_item = self.test_case_model.item(row, 7)
            
            if case_name_item:
                test_cases.append({
                    "用例名称": case_name_item.text(),
                    "状态": status_item.text() if status_item else "",
                    "进度": progress_item.text() if progress_item else "",
                    "执行次数": exec_count_item.text() if exec_count_item else "0",
                    "失败次数": fail_count_item.text() if fail_count_item else "0",
                    "最后结果": result_item.text() if result_item else "",
                    "详细信息": message_item.text() if message_item else ""
                })
        
        # 计算成功率
        pass_rate = (
            (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        )
        
        # 组装报告数据
        report_data = {
            "报告信息": {
                "生成时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "项目名称": self.current_project_name,
                "测试套件": self.current_test_suite,
                "测试轮次": self.test_settings["rounds"]
            },
            "测试统计": {
                "总测试数": self.total_tests,
                "成功数": self.passed_tests,
                "失败数": self.failed_tests,
                "成功率": f"{pass_rate:.2f}%"
            },
            "测试设置": {
                "测试轮数": self.test_settings["rounds"],
                "失败时停止": self.test_settings["stop_on_fail"],
                "轮次间延时": f"{self.test_settings['delay']}秒"
            },
            "测试用例详情": test_cases
        }
        
        return report_data

    def _show_multi_round_dialog(self):
        """显示多轮测试设置对话框"""
        dialog = MultiRoundTestDialog(self)
        dialog.rounds_spinbox.setValue(self.test_settings["rounds"])
        dialog.stop_on_fail_checkbox.setChecked(self.test_settings["stop_on_fail"])
        dialog.delay_spinbox.setValue(self.test_settings["delay"])

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.test_settings = dialog.get_settings()
            self.log_message(
                f"多轮测试设置已更新: {self.test_settings['rounds']}轮", "INFO"
            )

    def _setup_table_properties(self):
        """设置测试用例表格属性"""

        # 表格基本属性
        self.test_case_table.setAlternatingRowColors(True)
        self.test_case_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.test_case_table.setShowGrid(True)
        self.test_case_table.setSortingEnabled(False)  # 禁用排序，防止表格重排导致跳动
        self.test_case_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # 隐藏垂直表头，防止数据加载时表头跳动
        self.test_case_table.verticalHeader().setVisible(False)

        # 设置水平表头属性
        header = self.test_case_table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)  # 禁用最后一列的自动拉伸
            header.setMinimumSectionSize(40)  # 设置最小列宽
            header.setSectionsMovable(False)  # 禁止拖动列
            header.setHighlightSections(False)  # 禁用高亮
            # 防止表头在数据变化时重新计算大小
            header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        
        # 先设置所有列为固定模式，然后再设置具体列宽和拉伸列
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 选择列
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 用例名称列
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 状态列
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 进度列
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 执行次数列
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # 失败次数列
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # 最后结果列
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  # 详细信息列
                        
        # 设置固定列宽
        self.test_case_table.setColumnWidth(0, 50)  # 选择
        self.test_case_table.setColumnWidth(2, 80)  # 状态
        self.test_case_table.setColumnWidth(3, 100)  # 进度
        self.test_case_table.setColumnWidth(4, 80)  # 执行次数
        self.test_case_table.setColumnWidth(5, 80)  # 失败次数
        self.test_case_table.setColumnWidth(6, 100)  # 最后结果

    # ========== 日志方法 ==========

    def log_message(self, message, level="INFO"):
        """统一的日志记录方法，支持颜色和时间戳"""
        # 显示到 UI 日志面板
        self.log_panel.append_log(message, level)
        
        # 同时写入日志文件
        level_upper = level.upper()
        if level_upper == "SUCCESS":
            self.logger.success(message)
        elif level_upper == "ERROR":
            self.logger.error(message)
        elif level_upper == "WARNING" or level_upper == "WARN":
            self.logger.warning(message)
        elif level_upper == "DEBUG":
            self.logger.debug(message)
        elif level_upper == "FAIL":
            self.logger.error(f"[FAIL] {message}")
        else:  # INFO 或其他
            self.logger.info(message)

    # ========== 用例选择与筛选方法 ==========

    def filter_test_cases(self, text):
        """根据搜索框内容筛选测试用例列表"""
        for i in range(self.test_case_model.rowCount()):
            case_name_item = self.test_case_model.item(i, 1)
            if case_name_item:
                should_hide = text.lower() not in case_name_item.text().lower()
                self.test_case_table.setRowHidden(i, should_hide)

    # ========== 项目加载方法 ==========

    def _load_project_tree(self):
        """加载项目树结构"""
        self.logger.info("开始加载项目树结构")
        model = self.tree_view.model()
        if not isinstance(model, QStandardItemModel):
            self.logger.error("树视图模型类型错误")
            return

        model.clear()

        try:
            # 读取项目配置文件
            project_root = Config.ROOT_DIR
            config_path = os.path.join(
                project_root, "user_config", "project_config", "project_cfg.yaml"
            )

            if not os.path.exists(config_path):
                self.log_message(f"项目配置文件不存在: {config_path}", "ERROR")
                self.logger.error(f"项目配置文件不存在: {config_path}")
                return

            self.logger.debug(f"正在加载项目配置: {config_path}")
            self.project_config = load_yaml_config(config_path)
            projects = self.project_config.get("projects", {})

            for project_cfg in projects:
                # 创建项目节点
                project_item = QStandardItem(f"📁 {project_cfg.get('name', '')}")
                project_item.setData(
                    {"type": "project", "name": project_cfg.get("name", "")},
                )

                # 读取项目的测试套件配置文件
                project_config_file = project_cfg.get("path", "")
                if project_config_file:
                    project_config_path = os.path.join(
                        project_root,
                        "user_config",
                        "project_config",
                        "project_list",
                        project_config_file,
                    )

                    if os.path.exists(project_config_path):
                        try:
                            project_detail_config = load_yaml_config(
                                project_config_path
                            )

                            # 为每个测试套件创建子节点
                            for (
                                suite_name,
                                suite_config,
                            ) in project_detail_config.items():
                                suite_item = QStandardItem(f"📋 {suite_name}")
                                suite_item.setData(
                                    {
                                        "type": "test_suite",
                                        "project": project_cfg.get("name", ""),
                                        "suite_name": suite_name,
                                    },
                                )
                                project_item.appendRow(suite_item)

                        except Exception as e:
                            self.log_message(
                                f"加载项目 {project_cfg.get('name', '')} 的配置失败: {str(e)}",
                                "ERROR",
                            )
                    else:
                        self.log_message(
                            f"项目 {project_cfg.get('name', '')} 的配置文件不存在: {project_config_path}",
                            "WARNING",
                        )

                model.appendRow(project_item)

            # 展开所有项目节点
            self.tree_view.expandAll()

            self.log_message(f"已加载 {len(projects)} 个项目", "INFO")
            self.logger.success(f"项目树加载完成，共 {len(projects)} 个项目")

        except Exception as e:
            self.log_message(f"加载项目树失败: {str(e)}", "ERROR")
            self.logger.exception("加载项目树时发生异常")

    def _on_tree_item_clicked(self, index):
        """处理树节点点击事件"""
        model = self.tree_view.model()
        if not isinstance(model, QStandardItemModel):
            return
        item = model.itemFromIndex(index)
        if not item:
            return

        item_data = item.data()
        if not item_data:
            return

        if item_data.get("type") == "test_suite":
            # 点击的是测试套件，加载对应的测试用例
            project_name = item_data.get("project")
            suite_name = item_data.get("suite_name")
            self._load_test_suite(project_name, suite_name)
        elif item_data.get("type") == "project":
            # 点击的是项目节点，清空测试用例列表
            self.test_case_model.clear_all_cases()
            self.log_message(
                f"请选择项目 '{item_data.get('name')}' 下的具体测试套件", "INFO"
            )

    def _load_test_suite(self, project_name, suite_name):
        """加载指定项目的测试套件"""
        self.logger.info(f"开始加载测试套件: {suite_name} (项目: {project_name})")
        try:
            self.current_project_name = project_name
            self.current_test_suite = suite_name

            # 构建测试套件文件路径
            project_root = Config.ROOT_DIR
            suite_file_path = os.path.join(
                project_root,
                "user_config",
                "test_suite",
                project_name,
                f"{suite_name}.yaml",
            )

            # 如果没有找到 .yaml 文件，尝试 .yml 文件
            if not os.path.exists(suite_file_path):
                suite_file_path = os.path.join(
                    project_root,
                    "user_config",
                    "test_suite",
                    project_name,
                    f"{suite_name}.yml",
                )

            if not os.path.exists(suite_file_path):
                self.log_message(f"测试套件文件不存在: {suite_file_path}", "ERROR")
                self.logger.error(f"测试套件文件不存在: {suite_file_path}")
                return

            # 加载测试套件配置
            self.logger.debug(f"正在加载测试套件配置: {suite_file_path}")
            suite_config = load_yaml_config(suite_file_path)

            # 清空现有测试用例
            self.test_case_model.clear_all_cases()

            # 解析测试用例
            test_cases = self._parse_test_cases(suite_config)

            if test_cases:
                # 添加测试用例到模型
                for case_name in test_cases.keys():
                    self.test_case_model.add_test_case(case_name)

                # 存储测试用例配置，供后续执行使用
                self.test_cases_config = {"test_cases": {project_name: test_cases}}
                
                self.log_message(
                    f"已加载项目 '{project_name}' 的测试套件 '{suite_name}'，共 {len(test_cases)} 个测试用例",
                    "INFO",
                )
                self.logger.success(f"测试套件加载成功: {suite_name}，共 {len(test_cases)} 个用例")
            else:
                self.log_message(
                    f"测试套件 '{suite_name}' 中没有找到测试用例", "WARNING"
                )

        except Exception as e:
            self.log_message(f"加载测试套件失败: {str(e)}", "ERROR")
            self.logger.exception(f"加载测试套件失败: {project_name}/{suite_name}")

    def _parse_test_cases(self, suite_config):
        """解析测试套件配置文件中的测试用例
        
        格式要求（数组格式）:
        测试用例名: ["项目名", "模块文件", "类名", 测试数据...]
        
        说明:
        - 前3个元素必须是: 项目名、模块文件、类名
        - 可以在后面添加额外的测试数据参数（可选）
        
        示例:
        root:
          process0:
            # 基础用例（无额外参数）
            简单测试用例: ["demo_project", "demo_test_cases.py", "SimpleTestCase"]
            # 带测试数据的用例
            数据验证测试: ["demo_project", "demo_test_cases.py", "DataTest", {"key": "value"}, 100]
        """
        self.logger.debug("开始解析测试用例配置")
        test_cases = {}

        try:
            # 结构: root -> process0 -> 测试用例名 -> 数组配置
            root = suite_config.get("root", {})
            process0 = root.get("process0", {})

            for case_name, case_config in process0.items():
                if isinstance(case_config, list) and len(case_config) >= 3:
                    # 数组格式: ["项目文件夹", "文件路径", "类名", ...]
                    test_cases[case_name] = case_config
                    self.logger.debug(f"已解析测试用例 '{case_name}': {case_config}")
                else:
                    self.log_message(
                        f"测试用例 '{case_name}' 的配置格式不正确，需要数组格式如: [\"项目\", \"文件\", \"类\"] (当前: {case_config})", 
                        "WARNING"
                    )
                    self.logger.warning(f"测试用例 '{case_name}' 配置格式错误: {case_config}")

        except Exception as e:
            self.log_message(f"解析测试用例配置时出错: {str(e)}", "ERROR")
            self.logger.exception("解析测试用例配置时发生异常")

        self.logger.info(f"成功解析 {len(test_cases)} 个测试用例")
        return test_cases

    # ========== 测试执行方法 ==========

    def start_test(self):
        """开始测试"""
        self.logger.info("=" * 50)
        self.logger.info("开始执行测试")
        self.logger.info("=" * 50)
        
        # 重置统计数据
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.logger.debug("统计数据已重置")

        # 获取选中的测试用例
        selected_case_names = self.test_case_model.get_selected_cases()
        if not selected_case_names:
            self.log_message("请先勾选要测试的用例", "WARNING")
            self.logger.warning("未选择任何测试用例")
            if self.is_restarting:
                self.is_restarting = False
            return

        # 重置所有测试用例数据
        self.test_case_model.reset_all_case_data()

        # 检查是否已选择测试套件
        if not self.current_project_name or not self.current_test_suite:
            self.log_message("请先选择项目和测试套件", "WARNING")
            self.logger.warning("未选择项目或测试套件")
            return
        
        self.logger.info(f"当前项目: {self.current_project_name}, 测试套件: {self.current_test_suite}")
        self.logger.info(f"选中测试用例数: {len(selected_case_names)}, 测试轮次: {self.test_settings['rounds']}")

        # 准备要执行的用例
        cases_to_run = []
        project_cases_config = self.test_cases_config.get("test_cases", {}).get(
            self.current_project_name, {}
        )

        for case_name in selected_case_names:
            case_details = project_cases_config.get(case_name)
            if case_details:
                cases_to_run.append((case_name, case_details))
            else:
                self.log_message(
                    f"在配置文件中找不到用例 '{case_name}' 的详细信息", "ERROR"
                )

        self.total_tests = len(cases_to_run) * self.test_settings["rounds"]
        self._update_stats_ui()

        # 设置进度条
        self.progress_bar.setMaximum(self.total_tests)
        self.progress_bar.setValue(0)

        self.log_message(
            f"开始执行测试套件 '{self.current_test_suite}'，共 {len(cases_to_run)} 个用例，{self.test_settings['rounds']} 轮",
            "INFO",
        )

        # 启动测试线程
        self.test_thread = QThread()
        self.test_worker = TestWorker(cases_to_run, self.test_settings)
        self.test_worker.moveToThread(self.test_thread)

        # 1. 线程启动后，执行worker的run方法
        self.test_thread.started.connect(self.test_worker.run)

        # 2. 连接worker的信号到主窗口的槽
        self.test_worker.finished.connect(self._on_test_finished)
        self.test_worker.log.connect(self.log_message)
        self.test_worker.round_finished.connect(self._on_round_finished)

        # 3. 当worker完成所有工作时 (发出all_finished信号)
        #    a) 更新UI
        #    b) 请求线程退出其事件循环
        self.test_worker.all_finished.connect(self._on_all_tests_finished)
        self.test_worker.all_finished.connect(self.test_thread.quit)

        # 4. 当线程的事件循环真正结束后 (发出finished信号)
        #    a) 安全地删除worker对象
        #    b) 安全地删除thread对象
        #    c) 将成员变量置空，为下一次测试做准备
        self.test_thread.finished.connect(self.test_worker.deleteLater)
        self.test_thread.finished.connect(self.test_thread.deleteLater)
        self.test_thread.finished.connect(self._on_thread_cleaned_up)

        self.logger.info(
            f"测试线程设置完成，共 {len(cases_to_run)} 个用例，{self.test_settings['rounds']} 轮，"
            f"总计 {self.total_tests} 个测试"
        )

        self._update_button_states(is_running=True)
        self.test_thread.start()
        self.logger.success("测试线程已启动")

    # ========== 测试回调方法 ==========

    def _on_test_finished(self, case_name, result, message, round_num):
        """测试完成回调"""
        log_level = (
            "SUCCESS" if result == "Pass" else ("FAIL" if result == "Fail" else "ERROR")
        )
        self.log_message(
            f"[轮次 {round_num}] 测试完成: {case_name} - 结果: {result} - 信息: {message}",
            log_level,
        )
        
        # 使用 loguru 记录更详细的信息
        if result == "Pass":
            self.logger.success(f"[轮次 {round_num}] {case_name}: {message}")
        elif result == "Fail":
            self.logger.error(f"[轮次 {round_num}] {case_name}: {message}")
        else:
            self.logger.warning(f"[轮次 {round_num}] {case_name}: {message}")

        # 更新模型中的测试用例结果
        self.test_case_model.update_case_result(
            case_name, result, message, round_num, self.test_settings["rounds"]
        )

        # 更新统计
        if result == "Pass":
            self.passed_tests += 1
        else:
            self.failed_tests += 1

        # 更新进度条
        current_progress = self.passed_tests + self.failed_tests
        self.progress_bar.setValue(current_progress)
        self.progress_bar.setFormat(f"{current_progress} / {self.total_tests}")

        # 更新状态栏
        self.status_bar.showMessage(
            f"正在执行测试... ({current_progress}/{self.total_tests})"
        )
        
        # 刷新UI统计显示
        self._update_stats_ui()

    def _on_case_updated(self, case_name):
        """测试用例更新回调"""
        # 当测试用例更新时，刷新UI统计
        self._update_stats_ui()

    def _on_round_finished(self, round_num):
        """轮次完成处理"""
        self.log_message(
            f"第 {round_num}/{self.test_settings['rounds']} 轮测试完成", "INFO"
        )
        self.logger.info(f"轮次 {round_num} 执行完成")

    def _on_all_tests_finished(self):
        """
        当所有测试轮次都执行完毕后调用。
        此方法只负责更新UI状态，不处理线程生命周期。
        """
        self.logger.info("=" * 50)
        self.logger.info("所有测试执行完毕")
        self.logger.info(f"总计: {self.total_tests}, 成功: {self.passed_tests}, 失败: {self.failed_tests}")
        self.logger.info("=" * 50)
        
        self.log_message("所有选定测试已执行完毕。", "INFO")
        self._update_button_states(is_running=False)
        # 进度条保持显示，但重置格式
        self.progress_bar.setFormat(f"测试完成 - {self.passed_tests}/{self.total_tests}")

        # 更新状态栏
        pass_rate = (
            (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        )
        self.status_bar.showMessage(f"测试完成 - 成功率: {pass_rate:.1f}%")
        self.logger.success(f"测试完成，成功率: {pass_rate:.1f}%")
        
        # 自动保存测试报告
        if self.total_tests > 0:
            self._save_test_report()

        if self.is_restarting:
            self.is_restarting = False
            self.log_message("将在1秒后自动重启测试...", "INFO")
            QTimer.singleShot(1000, self.start_test)

    def _on_thread_cleaned_up(self):
        """
        当线程完全结束后调用，用于清理成员变量。
        """
        self.log_message("测试线程已安全清理。", "INFO")
        self.test_thread = None
        self.test_worker = None

    def stop_test(self):
        """停止测试"""
        self.logger.warning("用户请求停止测试")
        if self.test_worker:
            self.log_message("正在发送停止信号...", "WARNING")
            self.test_worker.stop()
            self.stop_button.setEnabled(False)
            if not self.is_restarting:
                self.restart_button.setEnabled(True)
        else:
            self.log_message("没有正在运行的测试。", "INFO")

    def restart_test(self):
        """重启测试功能"""
        self.logger.info("用户请求重启测试")
        self.log_message("准备重启测试...", "INFO")
        if self.test_thread and self.test_thread.isRunning():
            self.is_restarting = True
            self.restart_button.setEnabled(False)
            self.stop_test()
        else:
            self.start_test()

    # ========== UI 更新方法 ==========

    def _update_stats_ui(self):
        """更新统计信息显示"""
        #  使用实际的测试总数（如果为0则使用选中用例数计算）
        if self.total_tests == 0:
            # 测试未开始，显示预估数量
            selected_cases = len(self.test_case_model.get_selected_cases())
            display_total = selected_cases * self.test_settings["rounds"]
        else:
            # 测试已开始，使用实际总数
            display_total = self.total_tests

        # 计算成功率
        pass_rate = (
            (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        )

        # 使用更丰富的显示格式
        self.total_label.setText(f"📊 总数: {display_total}")
        self.passed_label.setText(f"✅ 成功: {self.passed_tests}")
        self.failed_label.setText(f"❌ 失败: {self.failed_tests}")

        # 如果有测试结果，显示成功率
        if self.total_tests > 0:
            rate_color = (
                "green" if pass_rate >= 90 else "orange" if pass_rate >= 70 else "red"
            )
            self.total_label.setText(
                f"📊 总数: {display_total} (成功率: <span style='color: {rate_color}'>{pass_rate:.1f}%</span>)"
            )

    def _update_button_states(self, is_running):
        """更新按钮状态"""
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        self.restart_button.setEnabled(not is_running)

    # ========== 用例选择方法 ==========

    def select_all(self):
        """全选测试用例"""
        for i in range(self.test_case_model.rowCount()):
            if not self.test_case_table.isRowHidden(i):
                checkbox_item = self.test_case_model.item(i, 0)
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.CheckState.Checked)

    def select_none(self):
        """全不选测试用例"""
        for i in range(self.test_case_model.rowCount()):
            checkbox_item = self.test_case_model.item(i, 0)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)

    def select_inverse(self):
        """反选测试用例"""
        for i in range(self.test_case_model.rowCount()):
            if not self.test_case_table.isRowHidden(i):
                checkbox_item = self.test_case_model.item(i, 0)
                if checkbox_item:
                    current_state = checkbox_item.checkState()
                    checkbox_item.setCheckState(
                        Qt.CheckState.Unchecked
                        if current_state == Qt.CheckState.Checked
                        else Qt.CheckState.Checked
                    )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    # 确保窗口在显示前完成布局计算
    window.resize(1400, 800)
    window.show()
    sys.exit(app.exec())
