# coding:utf-8

# uiautomator2 android的相关操作
import uiautomator2 as u2
from uiautomator2 import Direction
from uiautomator2.xpath import XPathSelector
from enum import Enum
from typing import Union
import time


class AndroidKeys(Enum):
    HOME = 'home'
    BACK = 'back'
    LEFT = 'left'
    RIGHT = 'right'
    UP = 'up'
    DOWN = 'down'
    CENTER = 'center'
    MENU = 'menu'
    SEARCH = 'search'
    ENTER = 'enter'
    DELETE = 'delete'
    RECENT = 'recent'
    VOLUME_UP = 'volume_up'
    VOLUME_DOWN = 'volume_down'
    VOLUME_MUTE = 'volume_mute'
    CAMERA = 'camera'
    POWER = 'power'


class Operators:

    def __init__(self, obj):
        self._object = obj


    def click(self, timeout=5):
        """
        如果指定元素找到则点击
        :param timeout: 查找元素的超时时间
        :return:
        """
        assert self._object.click_exists(timeout=timeout), '点击元素失败'

    def get_text(self, timeout=None):
        """
        获取text值
        :return: text值
        """
        if isinstance(self._object, XPathSelector):
            return self._object.get(timeout).attrib.get("text", "")
        else:
            return self._object.get_text(timeout)

    def expect_exist(self, timeout, exist=True, raiseout=False):
        """
        在指定的时长内，对象是否可见
        :param timeout: 超时时长
        :param exist: 期望结果，False表示期望对象不存在，True表示存在
        :param raiseout: 当没有发现对象时是否抛出异常，False不抛出异常,返回false或true, True: 当找不到对象时抛异常
        :return:
        """
        ...

    def click_exists(self, timeout=5) -> bool:
        return self._object.click_exists(timeout)

    @property
    def exists(self) -> bool:
        if self._object.exists:
            return True
        return False

    def screenshot(self):
        return self._object.screenshot()

    def wait_gone(self, timeout=5) -> bool:
        return self._object.wait_gone(timeout)

    @property
    def info(self):
        return self._object.info


class UiObjectOperators(Operators):
    """
    uiObject对象相关操作
    """

    def __init__(self, obj: u2.UiObject):
        super().__init__(obj)

    @property
    def bounds(self):
        return self._object.bounds()

    def expect_exist(self, timeout, exist=True, raiseout=False):
        """
        在指定的时长内，对象是否可见
        :param timeout: 超时时长
        :param exist: 期望结果，False表示期望对象不存在，True表示存在
        :param raiseout: 当没有发现对象时是否抛出异常，False不抛出异常,返回false或true, True: 当找不到对象时抛异常
        :return:
        """
        if raiseout:
            self._object.must_wait(exists=exist, timeout=timeout)
        else:
            return self._object.wait(exists=exist, timeout=timeout)

    def send_text(self, text: str, timeout=5):
        """
        向对象输入指定的内容.在输入内容前会先清除对象的内容
        :param text: 要输入的内容
        :param timeout: 等待对象出现的超时时长
        :return:
        """
        self._object.clear_text(timeout)
        self._object.set_text(text, timeout)

    def clear_text(self, timeout=5):
        """
        清除对象的内容
        :param timeout: 等待对象出现的超时时长
        :return:
        """
        self._object.clear_text(timeout)

    def child(self, locate: dict):
        self._object = self._object.child(**locate)
        return self._object

    def click(self, timeout=None, offset=None):
        self._object.click(timeout, offset)

    def wait_display(self, timeout: Union[float, int] = None) -> bool:
        """
        等待元素显示
        :param timeout: 等待时间
        :return:
        """
        return self._object.wait(True, timeout)

    def get_attr(self, name):
        """
        bounds: [y2, x2, x1, y1]
            x=bounds[1]  y=bounds[3]  width=bounds[2]-bounds[1]  height=bounds[0]-bounds[3]
        """
        res = self._object.info.get(name)
        if isinstance(res, dict):
            return res.values()
        return res

    def click_gone(self, maxretry=10.0, interval=1.0):
        """
        点击元素消失停止；超时停止
        :param maxretry: 最长时间
        :param interval: 检查间隔
        :return:
        """
        return self._object.click_gone(maxretry, interval)

    def swipe(self, direction, steps=10):
        """
        Args:
            direction (str): one of ("left", "right", "up", "down")
            steps (int): move steps, one step is about 5ms
        """
        self._object.swipe(direction, steps)

    def long_click(self, timeout=None, duration: float = 0.5):
        self._object.long_click(duration, timeout)

    @property
    def scroll(self):
        """
        Args:
        dimention (str): one of "vert", "vertically", "vertical", "horiz", "horizental", "horizentally"
        action (str): one of "forward", "backward", "toBeginning", "toEnd", "to"
        """
        return self._object.scroll

    def scroll_to(self, **local):
        if self._object.child(**local).exists:
            return self._object.child(**local)
        if self.scroll.to(**local):
            return self._object.child(**local)
        return None

    def left(self, locate):
        self._object = self._object.left(**locate)
        return self._object

    def right(self, locate: dict):
        self._object = self._object.right(**locate)
        return self._object

    def up(self, locate):
        self._object = self._object.up(**locate)
        return self._object

    def down(self, locate):
        self._object = self._object.down(**locate)
        return self._object

    def drag_to(self, *args, **kwargs):
        return self._object.drag_to(*args, **kwargs)

    def double_click(self, timeout=None):
        self.click(timeout, None)
        self.click(None, None)


class XpathSelectorOperators(Operators):
    """
    xpathSelector对象的相关的操作
    """

    def __init__(self, selector: XPathSelector, device: u2.Device):
        super().__init__(selector)
        self.__d = device

    def parent(self):
        return self._object.get().parent()

    @property
    def bounds(self):
        return self._object.bounds

    def expect_exist(self, timeout, exist=True, raiseout=False):
        if exist:
            self._object.wait(timeout=timeout)
            if raiseout:
                assert self._object.exists, '元素未找到'
            else:
                return self._object.exists
        else:
            if raiseout:
                assert self._object.wait_gone(timeout), '页面一直显示元素'
            else:
                return self._object.wait_gone(timeout)

    def center(self, timeout=None, offset=None):
        """
        点击点
        :param timeout: 等待超时时间
        :param offset: 偏移量
        :return: 返回对应元素偏移的坐标
        """
        x, y, width, height = self.get(timeout).bounds
        if offset is None:
            offset = 0.5
        return x + ((width - x) * offset), y + ((height - y) * offset)

    def swipe(self, direction, scale=0.6, steps=None):
        self._object.swipe(direction, scale)

    def get_xpath(self):
        return self._object.get().get_xpath()

    def child(self, locate: str) -> XPathSelector:
        """
        子元素
        :param locate: xpath语法定位
        :return: XpathSelector
        """
        return self._object.child(locate)

    def click(self, timeout=None, offset=None):
        """
        等待元素出现点击
        :param timeout: 等待超时时间
        :param offset: 偏移量
        :return:
        """
        self.__d.click(*self.center(timeout, offset))

    def click_gone(self, maxretry=10.0, interval=1.0):
        """
        点击元素消失停止；超时停止
        :param maxretry: 最长时间
        :param interval: 检查间隔
        :return:
        """
        self.click_exists()
        while maxretry > 0:
            time.sleep(interval)
            if not self.exists:
                return True
            self.click_exists()
            maxretry -= 1
        return False

    def double_click(self, timeout=None, offset=None):
        """
        双击
        :param timeout: 等待超时时间
        :param offset: 偏移量
        :return:
        """
        x, y = self.center(timeout, offset)
        self.__d.click(x, y)
        self.__d.click(x, y)

    def long_click(self, timeout=None, duration=0.5):
        """
        长按
        :param timeout: 等待元素出现时间
        :param duration: 长按时间
        :return:
        """
        x, y = self.center(timeout, None)
        self.__d.long_click(x, y, duration)

    def send_text(self, text: str, timeout=5):
        """
        向元素发送文本
        :param text: 文本
        :param timeout: 等待超时时间
        :return:
        """
        assert self._object.wait(timeout), '输入元素不存在'
        self._object.set_text(text)

    def get(self, timeout=None):
        """
        获取匹配到的第一个元素
        :param timeout:
        :return: XMLElement
        """
        return self._object.get(timeout)

    def get_attr(self, name):
        """
        获取对象的一些属性
        bounds: [y2, x1, x2, y1]
            x=bounds[1]  y=bounds[3]  width=bounds[2]-bounds[1]  height=bounds[0]-bounds[3]
        :param name:
        :return:
        """
        res = self._object.info.get(name)
        if res == 'true':
            return True
        if res == 'false':
            return False
        if isinstance(res, dict):
            left, top, right, bottom = res.values()
            return bottom, left, right, top
        if res == '':
            return None
        return res

    def wait_display(self, timeout=None) -> bool:
        """
        等待元素出现
        :param timeout: 等待时间
        :return: XMLElement or raise Exception
        """
        if self._object.wait(timeout):
            return False
        return True

    def scroll(self, direction: Union[Direction, str] = Direction.FORWARD):
        self._object.scroll(direction)

    def scroll_to(self, local, **kwargs):
        return self._object.scroll_to(local, **kwargs)

    def all(self):
        return self._object.all()

    @property
    def attrib(self):
        return self._object.attrib


class AndroidDevice:

    def __init__(self, device_name: str):
        self._name = device_name
        self.__dv = u2.connect(device_name)

    def __str__(self):
        return self._name

    def turn_on(self):
        """
        打开屏幕。如果屏幕没高亮，则屏幕高亮
        :return:
        """
        self.__dv.screen_on()

    def turn_off(self):
        """
        关闭屏幕.如果屏幕高亮，则屏幕关闭高亮
        :return:
        """
        self.__dv.screen_off()

    def find_element(self, **locate) -> UiObjectOperators:
        """
        查找元素
        :param locate:
        :return:
        """
        return UiObjectOperators(self.__dv(**locate))

    def find_element_byxpath(self, xpath: str) -> XpathSelectorOperators:
        """
        通过xath查询元素
        :param xpath: 元素的xpath
        :return:
        """
        return XpathSelectorOperators(self.__dv.xpath(xpath), self.__dv)

    def disconnect(self):
        """
        关闭连接设备
        :return:
        """
        del self.__dv

    def app_current(self, key=None):
        """
        default Returns:
            {'package': 'com.yaxon.launcher', 'activity': '.main.MainActivity', 'pid': 945}
        官方说明 低概率失败获取不到pid
        """
        if key:
            return self.__dv.app_current().get(key, None)
        return self.__dv.app_current()

    def app_start(self, packageName, activity=None, wait=False, stop=False, use_monkey=False):
        self.__dv.app_start(packageName, activity, wait, stop, use_monkey)

    def app_stop(self, packageName):
        self.__dv.app_stop(packageName)

    def app_uninstall(self, packageName):
        self.__dv.app_uninstall(packageName)

    def app_clear(self, pkn):
        self.__dv.app_clear(pkn)

    def app_wait(self, packageName, timeout=20.0, front=False) -> bool:
        """等待app启动"""
        self.__dv.app_wait(package_name=packageName, timeout=timeout, front=front)
        if front:
            if self.app_current("package") == packageName:
                return True
        else:
            if packageName in self.__dv.app_list_running():
                return True
        return False

    def click(self, x: int or float, y: int or float):
        """坐标点击"""
        self.__dv.click(x, y)

    def double_click(self, x, y, duration=0.1):
        """双击"""
        self.__dv.double_click(x, y, duration)

    def drag(self, sx, sy, ex, ey, duration=0.5):
        """拖拽"""
        self.__dv.drag(sx, sy, ex, ey, duration)

    @property
    def dump_hierarchy(self):
        """返回当前界面xml"""
        return self.__dv.dump_hierarchy()

    def implicitly_wait(self, seconds=None):
        """隐式等待"""
        if seconds:
            return self.__dv.implicitly_wait(seconds)
        return self.__dv.implicitly_wait()

    @property
    def info(self):
        return self.__dv.info

    def keyevent(self, key):
        """测试back有效"""
        self.__dv.keyevent(key)

    def long_click(self, x, y, duration):
        """长按坐标"""
        self.__dv.long_click(x, y, duration)

    def press(self, v) -> bool:
        """press key via name or key code. Supported key name includes:
            home, back, left, right, up, down, center, menu, search, enter,
            delete(or del), recent(recent apps), volume_up, volume_down,
            volume_mute, camera, power.
        参考AndroidKeys
        """
        return self.__dv.press(v)

    def push(self, src, dst: str):
        """推送"""
        self.__dv.push(src, dst)

    def pull(self, src, dst):
        """获取"""
        self.__dv.pull(src, dst)

    def screenshot(self, filename=None, fmt='pillow'):
        """如果没有文件名，返回一个PIL.Image.Image对象, mode=RGB"""
        return self.__dv.screenshot(filename, fmt)

    def settings(self, key=None, value=None):
        """
        {'fallback_to_blank_screenshot': False,
         'operation_delay': (0, 0),  # 前后延时
         'operation_delay_methods': ['click', 'swipe'], # 受影响的模块
         'wait_timeout': 20.0,  # 默认等待时间
         'xpath_debug': False}
        """
        if key and value:
            self.__dv.settings[key] = value
        return self.__dv.settings

    def shell(self, cmdargs, stream=False, timeout=60):
        return self.__dv.shell(cmdargs, stream, timeout).output

    def sleep(self, t: float):
        """休眠"""
        self.__dv.sleep(t)

    def swipe(self, fx, fy, tx, ty, duration=None, steps=None):
        """steps(ms)如果设置，duration(s)无效
        逻辑:
            if not duration:
                steps = SCROLL_STEPS
            if not steps:
                steps = int(duration * 200)
            steps = max(2, steps)  # step=1 has no swipe effect
        """
        self.__dv.swipe(fx, fy, tx, ty, duration=duration, steps=steps)

    def swipe_ext(self, direction, scale=0.8, box=None, **kwargs):
        """
        duration 秒
        Args:
            direction (str): one of "left", "right", "up", "down" or Direction.LEFT
            scale (float): percent of swipe, range (0, 1.0]
            box (tuple): None or [lx, ly, rx, ry]
            kwargs: used as kwargs in d.swipe
        Raises:
            ValueError
        """
        d = {"上": Direction.UP, "下": Direction.DOWN, "左": Direction.LEFT, "右": Direction.RIGHT}
        self.__dv.swipe_ext(d.get(direction), scale, box=box, **kwargs)

    def swipe_points(self, points: iter, duration=0.5):
        """
        Args:
            points: eg eg [[200, 300], [210, 320]]
            duration: duration to inject between two points
        """
        self.__dv.swipe_points(points, duration)

    def show_toast(self, text, duration: float = 1.0):
        return self.__dv.toast.show(text, duration=duration)
        """
        .show(text: str, duration: float)  # 展示   江淮（11） 测试无效
        .get_message(wait_timeout=10, cache_timeout=10, default=None)  # 获取
        .reset()  # 重置
        """

    def get_message(self, wait_timeout=10, cache_timeout=10, default=None):
        return self.__dv.toast.get_message(wait_timeout, cache_timeout, default)

    def touch(self):
        """
        比较原生的底层接口，
        eg  .up(x, y).down(x, y).move(x, y).sleep(time)
        """
        return self.__dv.touch

    def wait_activity(self, activity, timeout=10) -> bool:
        """wait activity display"""
        return self.__dv.wait_activity(activity, timeout)

    @property
    def watcher(self):
        """返回xpath观察者对象"""
        return self.__dv.watcher

    @property
    def wtc_ctx(self):
        return self.__dv.watch_context()

    def window_size(self) -> tuple:
        return self.__dv.window_size()


__all__ = [
    'AndroidDevice'
]

if __name__ == '__main__':
    d = UiObjectOperators(u2.connect())
    d.swipe("right")