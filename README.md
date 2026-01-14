# 自动化测试框架

一个基于 PySide6 的自动化测试框架，支持多轮测试、测试套件管理和实时日志输出。

## 功能特性

- 🎯 **测试套件管理**：支持多项目、多测试套件的组织管理
- 🔄 **多轮测试**：支持配置多轮测试，失败停止，轮次间延时
- 📊 **实时统计**：实时显示测试进度、成功率、失败统计
- 📝 **详细日志**：彩色日志输出，支持不同级别的日志显示
- 🎨 **现代界面**：基于 Fluent Design 的现代化 UI，支持亮/暗主题切换
- 🔧 **灵活配置**：YAML 配置文件管理测试用例和测试套件

## 项目结构

```
yaxon/
├── main.py                 # 主程序入口
├── config.py              # 配置文件
├── testCaseModel.py       # 测试用例数据模型
├── business/              # 业务逻辑模块
│   ├── can_module/       # CAN 通信模块
│   ├── serial_module/    # 串口通信模块
│   └── po_module/        # Page Object 模块
├── case_script/           # 测试脚本
│   ├── demo_project/     # 示例项目
│   ├── example_project/  # 演示项目
│   └── zhongqi/         # 重汽项目
├── fluent_qss/           # UI 主题样式
├── tools/                # 工具模块
│   ├── log_tool/        # 日志工具
│   ├── communication/   # 通信工具
│   └── android_tools/   # Android 工具
└── user_config/          # 用户配置
    ├── project_config/  # 项目配置
    └── test_suite/      # 测试套件配置

```

## 快速开始

### 环境要求

- Python 3.8+
- PySide6
- PyYAML
- loguru

### 安装依赖

```bash
pip install PySide6 PyYAML loguru
```

### 运行程序

```bash
python main.py
```

## 使用说明

1. **选择项目和测试套件**：在左侧树形视图中选择项目和测试套件
2. **选择测试用例**：勾选要执行的测试用例
3. **配置测试参数**：点击"多轮测试设置"配置测试轮数和相关参数
4. **开始测试**：点击"开始"按钮执行测试
5. **查看结果**：在日志窗口和表格中查看测试结果

## 配置文件说明

### 项目配置 (project_cfg.yaml)

定义可用的项目列表和对应的配置文件。

### 测试套件配置

每个测试套件使用 YAML 格式定义测试用例及其执行参数。

## 开发者

Betty Whitman

## 许可证

MIT License
