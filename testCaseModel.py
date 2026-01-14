from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor


class TestCaseModel(QStandardItemModel):
    """专门管理测试用例数据的模型"""

    # 定义信号
    case_updated = Signal(str)  # 当测试用例更新时发出信号

    def __init__(self):
        super().__init__()
        self.test_case_data = {}  # 存储测试用例的详细数据
        self.setup_headers()

    def setup_headers(self):
        """设置表头"""
        headers = [
            "选择",
            "用例名称",
            "状态",
            "进度",
            "执行次数",
            "失败次数",
            "最后结果",
            "详细信息",
        ]
        self.setHorizontalHeaderLabels(headers)

    def add_test_case(self, case_name):
        """添加测试用例到模型"""
        # 初始化数据
        self.test_case_data[case_name] = {
            "test_count": 0,
            "fail_count": 0,
            "result": "",
            "message": "",
            "progress": 0,
            "status": "待测试",
        }

        # 创建表格行
        row_items = []

        # 选择列 (复选框)
        checkbox_item = QStandardItem()
        checkbox_item.setCheckable(True)
        checkbox_item.setEditable(False)
        row_items.append(checkbox_item)

        # 用例名称列
        name_item = QStandardItem(case_name)
        name_item.setEditable(False)
        row_items.append(name_item)

        # 其他列
        for _ in range(6):  # 状态、进度、执行次数、失败次数、最后结果、详细信息
            item = QStandardItem("-")
            item.setEditable(False)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            row_items.append(item)

        self.appendRow(row_items)

    def update_case_result(self, case_name, result, message, round_num, total_rounds):
        """更新测试用例结果"""
        if case_name not in self.test_case_data:
            return

        # 更新数据
        data = self.test_case_data[case_name]
        data["test_count"] += 1
        if result != "Pass":
            data["fail_count"] += 1
        data["result"] = result
        data["message"] = message
        data["progress"] = int((round_num / total_rounds) * 100)

        # 更新状态
        if data["progress"] < 100:
            data["status"] = "执行中"
        else:
            data["status"] = "已完成"

        # 更新表格显示
        self._update_table_row(case_name)

        # 发出信号
        self.case_updated.emit(case_name)

    def _update_table_row(self, case_name):
        """更新表格中指定用例的行数据"""
        row_index = self._find_case_row(case_name)
        if row_index == -1:
            return

        data = self.test_case_data[case_name]

        # 更新状态列 - 添加颜色
        status_item = self.item(row_index, 2)
        status_item.setText(data["status"])
        if data["status"] == "待测试":
            status_item.setForeground(QColor("gray"))
        elif data["status"] == "执行中":
            status_item.setForeground(QColor("blue"))
        else:
            status_item.setForeground(QColor("green"))

        # 更新进度列 - 添加背景色
        progress_item = self.item(row_index, 3)
        progress_item.setText(f"{data['progress']}%")
        if data["progress"] == 100:
            progress_item.setBackground(QColor(76, 175, 80, 50))  # 绿色背景
        elif data["progress"] > 0:
            progress_item.setBackground(QColor(255, 193, 7, 50))  # 黄色背景

        # 更新执行次数
        self.item(row_index, 4).setText(str(data["test_count"]))

        # 更新失败次数 - 失败时高亮
        fail_item = self.item(row_index, 5)
        fail_item.setText(str(data["fail_count"]))
        if data["fail_count"] > 0:
            fail_item.setForeground(QColor("red"))
            fail_item.setBackground(QColor(244, 67, 54, 30))  # 红色背景

        # 更新最后结果 - 添加图标和颜色
        result_item = self.item(row_index, 6)
        if data["result"] == "Pass":
            result_item.setText("✓ Pass")
            result_item.setForeground(QColor("green"))
        elif data["result"] == "Fail":
            result_item.setText("✗ Fail")
            result_item.setForeground(QColor("red"))
        elif data["result"] == "Error":
            result_item.setText("⚠ Error")
            result_item.setForeground(QColor("orange"))
        else:
            result_item.setText("-")

        # 更新详细信息 - 添加工具提示
        info_item = self.item(row_index, 7)
        message = data["message"]
        if len(message) > 50:
            message = message[:47] + "..."
        info_item.setText(message)
        info_item.setToolTip(data["message"])  # 完整信息作为工具提示

    def _find_case_row(self, case_name):
        """查找用例对应的行索引"""
        for i in range(self.rowCount()):
            name_item = self.item(i, 1)
            if name_item and name_item.text() == case_name:
                return i
        return -1

    def get_selected_cases(self):
        """获取所有选中的测试用例"""
        selected_cases = []
        for i in range(self.rowCount()):
            checkbox_item = self.item(i, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                name_item = self.item(i, 1)
                if name_item:
                    selected_cases.append(name_item.text())
        return selected_cases

    def clear_all_cases(self):
        """清空所有测试用例"""
        self.clear()
        self.test_case_data.clear()
        self.setup_headers()

    def reset_all_case_data(self):
        """重置所有测试用例的数据"""
        # 暂时阻塞信号以避免多次刷新导致界面闪烁
        self.blockSignals(True)
        
        for case_name in self.test_case_data.keys():
            self.test_case_data[case_name] = {
                "test_count": 0,
                "fail_count": 0,
                "result": "",
                "message": "",
                "progress": 0,
                "status": "待测试",
            }
            self._update_table_row(case_name)
        
        # 恢复信号发射
        self.blockSignals(False)
        
        # 发出一次布局变化信号，触发视图刷新
        self.layoutChanged.emit()
