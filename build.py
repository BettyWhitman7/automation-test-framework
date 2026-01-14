#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nuitka 打包脚本
用于将自动化测试框架打包为独立的可执行文件
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime


class NuitkaBuild:
    """Nuitka 打包构建器"""

    def __init__(self):
        # 项目根目录
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 输出目录
        self.output_dir = os.path.join(self.root_dir, "dist")
        
        # 应用程序名称
        self.app_name = "AutoTestFramework"
        
        # 主入口文件
        self.main_script = "main.py"
        
        # 版本信息
        self.version = "1.0.0"
        self.company_name = "Yaxon"
        self.product_name = "AutoTest Framework"
        
    def clean_build(self):
        """清理之前的构建产物"""
        print("=" * 60)
        print("清理之前的构建产物...")
        print("=" * 60)
        
        # 清理 dist 目录
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
            print(f"已删除: {self.output_dir}")
            
        # 清理 build 目录
        build_dir = os.path.join(self.root_dir, "build")
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
            print(f"已删除: {build_dir}")
            
        # 清理 .nuitka 缓存目录
        for item in os.listdir(self.root_dir):
            if item.endswith(".build") or item.endswith(".dist") or item.endswith(".onefile-build"):
                path = os.path.join(self.root_dir, item)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"已删除: {path}")
                    
        print("清理完成!\n")
        
    def get_nuitka_command(self):
        """构建 Nuitka 命令行参数"""
        cmd = [
            sys.executable, "-m", "nuitka",
            
            # 基本选项
            "--standalone",                    # 创建独立发布版本
            "--windows-console-mode=disable",  # 禁用控制台窗口 (GUI应用)
            "--assume-yes-for-downloads",      # 自动同意下载依赖
            
            # 输出选项
            f"--output-dir={self.output_dir}",
            f"--output-filename={self.app_name}.exe",
            
            # Windows 特定选项
            f"--windows-company-name={self.company_name}",
            f"--windows-product-name={self.product_name}",
            f"--windows-file-version={self.version}",
            f"--windows-product-version={self.version}",
            
            # 启用插件
            "--enable-plugin=pyside6",         # PySide6 支持
            
            # 包含完整的包
            "--include-package=case_script",   # 测试用例脚本
            "--include-package=business",      # 业务逻辑模块
            "--include-package=tools",         # 工具模块
            "--include-package=fluent_qss",    # Fluent QSS 主题
            "--include-package=openpyxl",      # Excel 处理库
            
            # 排除包含中文命名的模块（避免 Windows 编码问题）
            "--nofollow-import-to=case_script.zhongqi.testcase",
            
            # 包含数据目录
            f"--include-data-dir={os.path.join(self.root_dir, 'user_config')}=user_config",
            f"--include-data-dir={os.path.join(self.root_dir, 'fluent_qss')}=fluent_qss",
            f"--include-data-dir={os.path.join(self.root_dir, 'tools', 'communication', 'candriver')}=tools/communication/candriver",
            
            # 包含 DLL 文件所在的目录
            f"--include-data-files={os.path.join(self.root_dir, 'tools', 'communication', 'candriver', 'win', 'x64')}/*.dll=tools/communication/candriver/win/x64/",
            f"--include-data-files={os.path.join(self.root_dir, 'tools', 'communication', 'candriver', 'win', 'x64', 'kerneldlls')}/*.dll=tools/communication/candriver/win/x64/kerneldlls/",
            f"--include-data-files={os.path.join(self.root_dir, 'tools', 'communication', 'candriver', 'win', 'x32')}/*.dll=tools/communication/candriver/win/x32/",
            f"--include-data-files={os.path.join(self.root_dir, 'tools', 'communication', 'candriver', 'win', 'x32', 'kerneldlls')}/*.dll=tools/communication/candriver/win/x32/kerneldlls/",
            
            # 包含 QSS 样式文件
            f"--include-data-files={os.path.join(self.root_dir, 'fluent_qss')}/*.qss=fluent_qss/",
            
            # 排除不需要的模块以减小体积
            "--nofollow-import-to=pytest",
            "--nofollow-import-to=unittest",
            "--nofollow-import-to=tkinter",
            "--nofollow-import-to=matplotlib",
            "--nofollow-import-to=numpy.tests",
            "--nofollow-import-to=scipy",
            
            # 优化选项
            "--remove-output",                 # 删除中间产物
            "--show-progress",                 # 显示进度
            "--show-memory",                   # 显示内存使用情况
            
            # 主入口脚本
            os.path.join(self.root_dir, self.main_script),
        ]
        
        return cmd
        
    def run_build(self):
        """执行打包构建"""
        print("=" * 60)
        print(f"开始 Nuitka 打包: {self.app_name}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        cmd = self.get_nuitka_command()
        
        # 打印命令 (便于调试)
        print("\n完整打包命令:")
        print("-" * 60)
        print(" \\\n    ".join(cmd))
        print("-" * 60)
        print()
        
        # 执行打包命令
        result = subprocess.run(
            cmd,
            cwd=self.root_dir,
            shell=False
        )
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ 打包成功!")
            print(f"输出目录: {self.output_dir}")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ 打包失败!")
            print(f"返回码: {result.returncode}")
            print("=" * 60)
            sys.exit(1)
            
    def post_build(self):
        """打包后处理"""
        print("\n执行打包后处理...")
        
        # 查找生成的目录
        dist_folder = None
        for item in os.listdir(self.output_dir):
            if item.endswith(".dist"):
                dist_folder = os.path.join(self.output_dir, item)
                break
                
        if not dist_folder:
            print("警告: 未找到生成的 .dist 目录")
            return
            
        # 确保 logs 目录存在
        logs_dir = os.path.join(dist_folder, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        print(f"创建日志目录: {logs_dir}")
        
        # 确保 reports 目录存在
        reports_dir = os.path.join(dist_folder, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        print(f"创建报告目录: {reports_dir}")
        
        print("后处理完成!")


def main():
    """主函数"""
    builder = NuitkaBuild()
    
    # 解析命令行参数
    clean_first = "--clean" in sys.argv or "-c" in sys.argv
    
    if clean_first:
        builder.clean_build()
        
    builder.run_build()
    builder.post_build()
    
    print("\n" + "=" * 60)
    print("全部完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
