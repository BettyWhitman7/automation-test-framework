"""
Fluent Design 主题管理器

提供主题加载、切换和管理功能。

使用示例:
    from fluent_qss import FluentTheme
    
    # 方式1: 使用 FluentTheme 类
    theme = FluentTheme()
    theme.apply(app)  # 应用亮色主题到 QApplication
    theme.apply(app, dark=True)  # 切换到暗色主题
    theme.apply(widget)  # 也可以应用到单个 widget
    
    # 方式2: 使用便捷函数
    from fluent_qss import load_theme, get_theme_path
    
    stylesheet = load_theme(dark=True)  # 获取 QSS 样式字符串
    app.setStyleSheet(stylesheet)
    
    path = get_theme_path(dark=False)  # 获取 QSS 文件路径
"""

from pathlib import Path
from typing import Union, Optional
from enum import Enum


class ThemeMode(Enum):
    """主题模式枚举"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"  # 跟随系统（暂未实现）


def get_resource_dir() -> Path:
    """获取资源目录路径"""
    return Path(__file__).parent


def get_theme_path(dark: bool = False) -> Path:
    """
    获取主题文件路径
    
    Args:
        dark: 是否使用暗色主题，默认 False（亮色主题）
    
    Returns:
        主题 QSS 文件的完整路径
    
    Example:
        >>> path = get_theme_path(dark=True)
        >>> print(path)  # .../fluent_qss/fluent_widgets_dark.qss
    """
    filename = "fluent_widgets_dark.qss" if dark else "fluent_widgets.qss"
    return get_resource_dir() / filename


def load_theme(dark: bool = False, encoding: str = "utf-8") -> str:
    """
    加载主题样式表内容
    
    Args:
        dark: 是否使用暗色主题，默认 False（亮色主题）
        encoding: 文件编码，默认 UTF-8
    
    Returns:
        QSS 样式表字符串
    
    Raises:
        FileNotFoundError: 如果样式文件不存在
    
    Example:
        >>> stylesheet = load_theme(dark=True)
        >>> app.setStyleSheet(stylesheet)
    """
    theme_path = get_theme_path(dark)
    
    if not theme_path.exists():
        raise FileNotFoundError(f"主题文件未找到: {theme_path}")
    
    with open(theme_path, "r", encoding=encoding) as f:
        return f.read()


class FluentTheme:
    """
    Fluent Design 主题管理器
    
    提供主题的加载、应用和切换功能。
    
    Attributes:
        current_mode: 当前主题模式 (ThemeMode)
    
    Example:
        >>> theme = FluentTheme()
        >>> 
        >>> # 应用亮色主题
        >>> theme.apply(app)
        >>> 
        >>> # 切换到暗色主题
        >>> theme.apply(app, dark=True)
        >>> 
        >>> # 切换主题（自动反转当前主题）
        >>> theme.toggle(app)
        >>> 
        >>> # 获取当前主题状态
        >>> print(theme.is_dark)  # True or False
    """
    
    def __init__(self, initial_mode: ThemeMode = ThemeMode.LIGHT):
        """
        初始化主题管理器
        
        Args:
            initial_mode: 初始主题模式，默认亮色
        """
        self._mode = initial_mode
        self._stylesheet_cache: dict[ThemeMode, str] = {}
    
    @property
    def current_mode(self) -> ThemeMode:
        """获取当前主题模式"""
        return self._mode
    
    @property
    def is_dark(self) -> bool:
        """是否为暗色主题"""
        return self._mode == ThemeMode.DARK
    
    @property
    def is_light(self) -> bool:
        """是否为亮色主题"""
        return self._mode == ThemeMode.LIGHT
    
    def get_stylesheet(self, dark: Optional[bool] = None, use_cache: bool = True) -> str:
        """
        获取主题样式表
        
        Args:
            dark: 是否获取暗色主题，None 表示使用当前主题
            use_cache: 是否使用缓存，默认 True
        
        Returns:
            QSS 样式表字符串
        """
        if dark is None:
            dark = self.is_dark
        
        mode = ThemeMode.DARK if dark else ThemeMode.LIGHT
        
        # 使用缓存
        if use_cache and mode in self._stylesheet_cache:
            return self._stylesheet_cache[mode]
        
        # 加载样式表
        stylesheet = load_theme(dark=dark)
        
        if use_cache:
            self._stylesheet_cache[mode] = stylesheet
        
        return stylesheet
    
    def apply(self, target, dark: Optional[bool] = None) -> None:
        """
        应用主题到目标对象
        
        Args:
            target: QApplication 或 QWidget 对象
            dark: 是否应用暗色主题，None 表示使用当前主题
        
        Example:
            >>> theme.apply(app)  # 使用当前主题
            >>> theme.apply(app, dark=True)  # 强制使用暗色主题
            >>> theme.apply(widget, dark=False)  # 对单个组件应用亮色主题
        """
        if dark is not None:
            self._mode = ThemeMode.DARK if dark else ThemeMode.LIGHT
        
        stylesheet = self.get_stylesheet()
        target.setStyleSheet(stylesheet)
    
    def toggle(self, target=None) -> ThemeMode:
        """
        切换主题（亮色 <-> 暗色）
        
        Args:
            target: 可选，如果提供则同时应用新主题到目标对象
        
        Returns:
            切换后的主题模式
        
        Example:
            >>> current = theme.toggle(app)
            >>> print(f"切换到: {current.value}")
        """
        # 切换模式
        if self._mode == ThemeMode.LIGHT:
            self._mode = ThemeMode.DARK
        else:
            self._mode = ThemeMode.LIGHT
        
        # 如果提供了目标，应用新主题
        if target is not None:
            self.apply(target)
        
        return self._mode
    
    def set_mode(self, mode: ThemeMode, target=None) -> None:
        """
        设置主题模式
        
        Args:
            mode: 目标主题模式
            target: 可选，如果提供则同时应用新主题
        """
        self._mode = mode
        
        if target is not None:
            self.apply(target)
    
    def clear_cache(self) -> None:
        """清除样式表缓存"""
        self._stylesheet_cache.clear()
    
    @staticmethod
    def get_light_path() -> Path:
        """获取亮色主题文件路径"""
        return get_theme_path(dark=False)
    
    @staticmethod
    def get_dark_path() -> Path:
        """获取暗色主题文件路径"""
        return get_theme_path(dark=True)
