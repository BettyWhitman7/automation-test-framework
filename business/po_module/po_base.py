from datetime import datetime
import inspect
import re
import subprocess
import time
from typing import Union

import uiautomator2 as u2
from airtest.core.api import *
from airtest.core.cv import Template
from airtest.core.error import TargetNotFoundError
import os.path

from tools.find_template import find_template
from tools.log_tool import log as lg


class PO_Base:
    """
    UI自动化测试基类（Page Object模式）

    封装Android UI自动化常用操作，基于uiautomator2和airtest实现，支持：
    - 元素定位（ID/text/description等）
    - 基础操作（点击（支持基于图像识别）、输入、滑动等）
    - 手势操作（拖拽、长按等）
    - 智能等待与断言
    - 分辨率自适应滑动
    - _开头的方法是私有方法，仅供内部调用

    作者: 单奇奇
    创建日期: 2025年1月15日
    最后修改: 2025年2月13日
    """

    def __init__(self, driver=None):
        self.u2_driver = driver or u2.connect()  # 此驱动直接来源于uiautomator2
        self._cached_resolution = self._get_screen_resolution()  # 缓存分辨率
        self.widget = Widget()
        # [Nick新增device_id属性]
        self.device_id = self._get_adb_device_id()
        self.baseline_path = "/sdcard/DCIM/baseline.png"
        self.test_prefix = "/sdcard/DCIM/aggressor_"

    def _capture_baseline(self, dev):
        dev.GotoFourDirectionImage()
        subprocess.run(f"adb shell screencap -p {self.baseline_path}", shell=True)
        dev.go_home()

    def _capture_test_image(self, dev, cycle):
        dev.GotoFourDirectionImage()
        subprocess.run(
            f"adb shell screencap -p {self.test_prefix}{cycle}.png", shell=True
        )
        dev.go_home()

    def _compare_images(self, img1_path, img2_path):
        import cv2
        from skimage.metrics import structural_similarity as ssim

        # 使用ADB拉取图片到本地
        subprocess.run(f"adb pull {img1_path} baseline.png", shell=True)
        subprocess.run(f"adb pull {img2_path} test.png", shell=True)

        # # 图像预处理,这种方法不释放图像资源
        # baseline = cv2.imread('baseline.png')
        # test_img = cv2.imread('test.png')
        # 直接使用cv2加载图像
        baseline = cv2.imread("baseline.png", cv2.IMREAD_COLOR)
        test_img = cv2.imread("test.png", cv2.IMREAD_COLOR)
        time.sleep(1)
        # 删除临时文件
        os.remove("baseline.png")
        os.remove("test.png")
        # 计算SSIM相似度
        return ssim(baseline, test_img, multichannel=True, channel_axis=2, win_size=9)

    def _get_adb_device_id(self):
        """通过adb devices命令获取首个设备id"""
        try:
            output = subprocess.check_output("adb devices", shell=True).decode()
            devices = [
                line.split("\t")[0]
                for line in output.splitlines()[1:]
                if line.endswith("device")
            ]
            print("[Nick Debug]通过adb devices查询到设备", devices)
            if devices:
                return devices[0]
        except subprocess.CalledProcessError as e:
            lg.error(f"获取设备ID失败: {e}")
            return "unknown_device"

    def adb_shell(self, command):
        """执行adb shell命令"""
        try:
            result = (
                subprocess.check_output(
                    f"adb -s {self.device_id} shell {command}",
                    shell=True,
                    stderr=subprocess.STDOUT,
                )
                .decode()
                .strip()
            )
            lg.debug(f"ADB命令执行成功: {command}")
            return result
        except subprocess.CalledProcessError as e:
            lg.error(f"ADB命令执行失败: {command} | 错误: {e.output.decode()}")
            raise

    def adb_check_awake(self, timeout=26):
        """
        检测设备是否处于唤醒状态
        :param timeout: 超时时间(秒)
        :return: True-已唤醒 False-未唤醒
        """
        print("[Nick Debug]开始检测设备唤醒状态~)")
        max_retries = 5
        retry_interval = 1
        end_time = time.time() + timeout

        for attempt in range(1, max_retries + 1):
            try:
                # 直接通过adb获取窗口策略
                output = subprocess.check_output(
                    f"adb -s {self.device_id} shell dumpsys window policy", shell=True
                ).decode()
                # 解析mAwake状态
                if "INTERACTIVE_STATE_AWAKE" in output:
                    lg.info("设备已唤醒，继续测试流程")
                    return True
                # 未检测到唤醒状态时增加重试计数
                print(f"[Nick Debug]第{attempt}次重试")
                time.sleep(retry_interval)  # 添加间隔避免高频查询
            except:
                print(f"[Nick Debug]设备连接失败，正在重试...")
                lg.warning(f"设备连接失败，正在重试... ({attempt}/{max_retries})")
                time.sleep(retry_interval)

            # 达到最大重试次数后执行错误处理
        lg.error("ADB唤醒命令执行失败,设备未唤醒")
        return False

    def _wait_device_online(self, timeout):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._get_adb_device_id() != "":
                print("[Nick Debug]adb_device检测为空")
                return
            print("[Nick Debug]adb_device检测为空,1秒后再次检测~")
            time.sleep(1)
        print("[Nick Debug]adb_device检测为空,等待连接失败~")
        raise RuntimeError("设备未重新连接")

    def adb_reboot(self):
        """依赖APK自动重连"""
        try:
            timeout_online = 10
            timeout_awake = 26
            # self.u2_driver.reboot()
            subprocess.run("adb reboot", shell=True, check=True)
            lg.info(f"设备{self.device_id}开始重启")
            # 第一阶段：基础等待26秒
            time.sleep(26)
            # 第二阶段：循环检测唤醒状态
            # self._wait_device_online(timeout=timeout_online)
            if not self.adb_check_awake(timeout=timeout_awake):
                lg.error(f"设备{self.device_id}{timeout_awake}秒内未唤醒")
        except Exception as e:
            lg.error(f"重启失败: {str(e)}")
            raise

    def go_home(self, text="home"):
        # 返回主页
        self.u2_driver.press(text)

    def load_image_paths(self):
        """
        遍历子类文件同级目录下的 image 文件夹，
        将图片文件名映射到其绝对路径（从根目录起）的字典中，并返回该字典。
        """
        # 通过 inspect 获取当前实例所属类的文件路径（即子类文件路径）
        base_dir = os.path.dirname(os.path.abspath(inspect.getfile(self.__class__)))
        # 构造 image 文件夹的绝对路径
        image_dir = os.path.join(base_dir, "image")

        if not os.path.isdir(image_dir):
            raise FileNotFoundError(f"找不到目录: {image_dir}")

        # 定义允许的图片文件扩展名
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".txt"}
        image_dict = {}
        # 遍历 image 文件夹中的所有文件
        for filename in os.listdir(image_dir):
            file_path = os.path.join(image_dir, filename)
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in valid_extensions:
                    image_dict[filename] = file_path

        return image_dict

    def at_assert_img_exist(
        self, image_dir, threshold=0.8, isrgb=True, touch_after_touch=False
    ):
        """
        检查指定图像是否存在

        :param touch_after_touch:
        :param threshold: 图像匹配阈值
        :param image_dir: 图像绝对路径，图片路径应由统一路径管理模块处理
        :raises FileNotFoundError: 当图像不存在时抛出
        :raises TargetNotFoundError: 当图像存在但未匹配到屏幕内容时抛出
        """
        # 修复点1：增加文件检查的日志记录
        if not os.path.exists(image_dir):
            error_msg = f"断言失败：图像文件不存在 | Path={image_dir}"
            lg.error(error_msg)  # 显式记录错误日志
            raise FileNotFoundError(error_msg)  # 将日志信息包含在异常中

        try:
            pos = exists(
                Template(
                    image_dir,
                    threshold=threshold,
                    rgb=isrgb,
                    resolution=self._cached_resolution,
                )
            )
            if not pos:
                # 修复点2：补充错误上下文信息
                error_msg = f"图像匹配失败 | Path={image_dir}"
                lg.error(error_msg)
                lg.debug(f"匹配详情: 分辨率={self._cached_resolution}, RGB模式={isrgb}")
                raise TargetNotFoundError(error_msg)

            # 成功日志补充细节
            lg.info(f"图像匹配成功 | Path={image_dir} | 坐标={pos}")
            if touch_after_touch:
                touch(pos)
            return pos

        except TargetNotFoundError as e:
            # 修复点3：避免重复记录已处理的错误
            raise  # 已在前面记录过错误，直接传递异常

        except Exception as e:
            # 修复点4：增加意外错误的上下文信息
            error_msg = (
                f"图像断言意外错误 | Path={image_dir} | 错误类型={type(e).__name__}"
            )
            lg.exception(error_msg)  # 使用exception记录堆栈信息
            raise RuntimeError(error_msg) from e

    def at_assert_img_not_exist(self, image_dir, isrgb=True, timeout=3):
        """
        断言指定图像不存在于当前屏幕

        :param image_dir: 图像绝对路径
        :param isrgb: 是否使用RGB模式匹配（默认True）
        :param timeout: 匹配超时时间（秒），默认3秒
        :raises FileNotFoundError: 当图像文件不存在时抛出（与原始逻辑相反）
        :raises AssertionError: 当图像仍存在于屏幕时抛出
        """
        # 1. 检查图像文件是否存在（逻辑相反：文件不存在直接返回成功）
        if not os.path.exists(image_dir):
            raise FileNotFoundError(
                f"断言失败：图像文件不存在，无法进行不存在性验证: {image_dir}"
            )

        try:
            # 2. 尝试查找图像（允许设置超时时间）
            pos = exists(
                Template(image_dir, rgb=isrgb, resolution=self._cached_resolution)
            )

            # 3. 核心逻辑相反：找到图像则断言失败
            if pos:
                lg.error(f"断言失败：检测到不应存在的图像 | Path={image_dir}")
                raise AssertionError(f"图像仍存在于屏幕: {image_dir}")

            # 4. 未找到图像则记录成功日志
            lg.debug(f"断言成功：图像未出现在屏幕 | Path={image_dir}")
            return True

        except TargetNotFoundError:
            # 5. 捕获预期异常（图像不存在）并记录
            lg.debug(f"断言成功：图像未找到（符合预期） | Path={image_dir}")
            return True

        except Exception as e:
            # 6. 处理其他异常
            lg.exception(f"图像不存在性断言时发生意外错误: {str(e)}")
            raise RuntimeError(f"断言过程异常: {str(e)}")

    def at_img_touch(
        self,
        image_dir,
        record_pos=None,
        isrgb=True,
        times=1,
        duration=0.1,
        right_click=False,
    ):
        """
        根据图像路径点击屏幕上匹配的图像

        :param image_dir: 图像绝对路径，图片路径应由统一路径管理模块处理
        :param rgb: 是否使用RGB三通道进行匹配（默认True）
        :param times: 连续点击次数（默认1次）
        :param duration: 长按时间（单位：秒）
        # :param right_click: 是否使用右键点击（默认左键）
        :return: 最终点击的坐标位置
        :raises TargetNotFoundError: 当图像未找到时抛出
        """

        # (不拼接路径，此操作应该由外部完成，统一路径管理)
        full_path = image_dir
        print(full_path)

        # 参数有效性校验
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"图像文件不存在: {full_path}")

        try:
            # 执行点击操作
            print(self._cached_resolution)
            clicked_pos = touch(
                Template(
                    full_path,
                    # record_pos=record_pos,
                    rgb=isrgb,
                    resolution=self._cached_resolution,
                ),
                times=times,
                duration=duration,
                # right_click=False
            )

            lg.info(f"成功点击图像 {image_dir} 坐标：{clicked_pos}")
            return clicked_pos

        except TargetNotFoundError as e:
            lg.error(f"图像匹配失败: {full_path}")
            lg.debug(f"失败详情：{str(e)}")
            raise
        except Exception as e:
            lg.exception(f"图像点击发生意外错误: {str(e)}")
            raise

    def click_by_image(self, template_image, threshold=0.9):
        """
        通过图像匹配点击
        :param template_image: 模板图像路径
        :param threshold: 匹配阈值，默认为 0.9
        """
        try:
            # 使用模板图像查找
            position = find_template(template_image, threshold)
            if position:
                self.u2_driver.click(position[0], position[1])  # 点击图像中心位置
                lg.info(f"成功点击模板图像: {template_image} 位于 {position}")
            else:
                lg.error(f"未找到匹配的模板图像: {template_image}")
                raise ValueError(f"未找到模板图像: {template_image}")
        except Exception as e:
            lg.error(f"图像点击失败: {str(e)}", exc_info=True)
            raise

    def long_press_by_image(self, template_image, duration=1.0, threshold=0.9):
        """
        通过图像匹配进行长按
        :param template_image: 模板图像路径
        :param duration: 长按持续时间（秒）
        :param threshold: 匹配阈值，默认为 0.9
        """
        try:
            # 使用模板图像查找
            position = find_template(template_image, threshold)
            if position:
                self.u2_driver.long_click(position[0], position[1], duration=duration)
                lg.info(
                    f"成功长按模板图像: {template_image} 位于 {position} 持续时间: {duration}s"
                )
            else:
                lg.error(f"未找到匹配的模板图像: {template_image}")
                raise ValueError(f"未找到模板图像: {template_image}")
        except Exception as e:
            lg.error(f"图像长按失败: {str(e)}", exc_info=True)
            raise

    def input_text(self, selector, text, clear=False, timeout=10):
        """
        在指定元素输入文本
        :param selector: 元素选择器，如 {"text": "音乐", "resourceId": "com.example:id/button"}
        :param text: 要输入的文本
        :param clear: 是否清除原有文本，默认不清除
        :param timeout: 等待元素出现的超时时间，单位为秒，默认等待10s
        """
        isExist = self.wait_for_element_exists(selector, timeout)
        print(isExist)

        if not isExist:
            raise ValueError(f"元素未找到: {selector}")
        else:
            element = self._find_element(selector)
        if clear:
            element.clear_text()
        element.set_text(text)
        lg.info(f"已输入文本 '{text}' 到元素: {selector}")

    def click_button(self, selector=None, timeout=None, x=None, y=None):
        """
        点击按钮（优化后）
        增强版点击方法（同时支持元素和坐标点击）
        现在支持等待元素出现
        :param selector: 元素选择器，如 {"text": "音乐", "resourceId": "com.example:id/button"}
        :param timeout: 等待元素出现的超时时间，单位为秒，默认等待10s
        """
        try:
            if selector:
                try:
                    # 1. 查找元素
                    if self.wait_for_element_exists(selector, timeout):
                        element = self._find_element(selector)

                        # 2. 显式检查元素是否存在
                        if element.exists:
                            # 3. 执行点击
                            element.click()
                            lg.info(f"成功点击元素: {selector}")
                        else:
                            lg.error(f"元素不存在，点击失败: {selector}")
                    else:
                        lg.error(f"元素未找到: {selector}")
                except Exception as e:
                    lg.error(
                        f"点击元素时发生异常: {selector}, 错误信息: {e}", exc_info=True
                    )

            elif x is not None and y is not None:
                self.u2_driver.click(x, y)
                lg.info(f"坐标点击成功: ({x},{y})")
            else:
                raise ValueError("必须提供selector或坐标参数")
        except Exception as e:
            lg.error(f"点击操作失败: {str(e)}", exc_info=True)
            raise

    def long_press(self, selector=None, x=None, y=None, duration=1.0, timeout=10):
        """
        长按元素或指定坐标
        :param selector: 元素选择器（优先使用元素定位）
        :param x: X坐标（元素和坐标二选一）
        :param y: Y坐标（元素和坐标二选一）
        :param duration: 长按持续时间（秒）
        :param timeout: 等待元素超时时间
        """
        try:
            if selector:
                if self.wait_for_element_exists(selector, timeout):
                    element = self._find_element(selector)
                    element.long_click(duration=duration)
                    lg.info(f"长按元素成功: {selector} ({duration}s)")
            elif x is not None and y is not None:
                self.u2_driver.long_click(x, y, duration=duration)
                lg.info(f"长按坐标成功: ({x},{y}) ({duration}s)")
            else:
                raise ValueError("必须提供元素选择器或坐标参数")
        except Exception as e:
            lg.error(f"长按操作失败: {str(e)}", exc_info=True)
            raise

    def get_element_attribute(self, selector, attr, timeout=10, custom_message=None):
        """
        优化后的方法：获取元素属性（支持任意属性和定位方式）

        :param selector: 元素选择器（如 {"resourceId": "id", "text": "text"}）
        :param attr: 要获取的属性名（如 "text", "content-desc", "bounds" 等）
        :param timeout: 等待元素出现的超时时间（秒），默认10秒
        :param custom_message: 自定义错误信息（失败时显示）
        :return: 属性值（存在时）或 None（失败时）
        """
        try:
            # 1. 参数校验
            if not selector or not isinstance(selector, dict):
                raise ValueError("selector 必须是非空字典")
            if not attr or not isinstance(attr, str):
                raise ValueError("attr 必须是非空字符串")

            # 2. 显式等待元素出现
            element = self.wait_for_element_exists(selector, timeout)
            if not element:
                base_error = f"元素未找到: {selector}，超时时间: {timeout}秒"
                error_msg = (
                    f"{custom_message}\n{base_error}" if custom_message else base_error
                )
                lg.error(error_msg)
                return None

            # 3. 获取属性
            value = self._find_element(selector)
            value = value.info.get(attr)
            if value is not None:
                lg.info(f"成功获取属性 [{attr}] 的值: {value}（元素: {selector}）")
                return value
            else:
                base_warning = f"元素属性 [{attr}] 不存在: {selector}"
                warning_msg = (
                    f"{custom_message}\n{base_warning}"
                    if custom_message
                    else base_warning
                )
                lg.warning(warning_msg)
                return None

        except Exception as e:
            base_error = f"获取属性时发生异常: {selector}, 错误信息: {e}"
            error_msg = (
                f"{custom_message}\n{base_error}" if custom_message else base_error
            )
            lg.error(error_msg, exc_info=True)
            return None

    def swipe_element_to(self, selector, direction, timeout=5):
        """
        根据指定元素进行方向滑动

        :param selector: 元素选择器，用于定位可滚动容器
        :param direction: 滑动方向（支持中英文大小写混合：上/下/左/右 或 up/down/left/right）
        :param timeout: 等待元素存在的超时时间
        """
        try:
            # 统一转换为小写处理（兼容中英文字符）
            direction = str(direction).lower()
            # 精简后的方向映射表
            direction_map = {
                # 中文处理
                "下": "up",
                "上": "down",
                "右": "left",
                "左": "right",
                "down": "up",
                "up": "down",
                "right": "left",
                "left": "right",
            }

            # 参数有效性校验
            if not selector:
                raise ValueError("元素选择器不能为空")
            if direction not in direction_map:
                valid = "/".join(
                    [k for k in direction_map.keys() if len(k) > 1]
                )  # 过滤单字符中文
                raise ValueError(f"无效方向参数: {direction}，有效值：{valid}")

            # 等待元素存在
            isExist = self.wait_for_element_exists(selector, timeout)
            if not isExist:
                raise RuntimeError(f"元素不存在: {selector}")

            # 执行滑动操作
            element = self._find_element(selector)
            element.swipe(direction_map[direction])
            lg.info(f"元素滑动完成 | 容器: {selector} | 方向: {direction}")

        except Exception as e:
            lg.error(f"滑动操作失败: {str(e)}", exc_info=True)
            raise

    def wait_for_element_exists(self, selector, timeout=10):
        """
        *核心方法
        等待元素加载完成
        :param selector: 元素选择器，支持多种定位方式（如 text, description, resourceId, xpath 等）
                           支持传入字典或直接传入 xpath 字符串：
                           1.radio_card = {"resourceId":"com.yaxon.launcher:id/radio_layout"}
                           2.xpath_selector = "//android.widget.Button[@text='确定']"
                           3.xpath_selector = {"xpath": "//android.widget.Button[@text='确定']"}
        :param timeout: 超时时间，单位为秒
        :return: 如果元素存在，返回 True；否则返回 None
        """
        try:
            # 如果selector为字符串且符合xpath格式
            if isinstance(selector, str) and selector.strip().startswith("/"):
                element = self.u2_driver.xpath(selector)
            elif isinstance(selector, dict) and "xpath" in selector:
                element = self.u2_driver.xpath(selector["xpath"])
            else:
                element = self.u2_driver(**selector)
            isExist = element.wait(timeout=timeout)
            return isExist if isExist else None
        except Exception as e:
            lg.error(f"等待元素时发生异常: {e}", exc_info=True)
            return None

    def _find_element(self, selector):
        """
        *核心方法
        根据选择器查找元素
        :param selector: 元素选择器，支持多种定位方式（如 text, resourceId, description, xpath 等）
                           支持传入字典或直接传入 xpath 字符串：
                           1.radio_card = {"resourceId":"com.yaxon.launcher:id/radio_layout"}
                           2.xpath_selector = "//android.widget.Button[@text='确定']"
                           3.xpath_selector = {"xpath": "//android.widget.Button[@text='确定']"}
        :return: 元素对象（如果找到），否则返回 None
        """
        try:
            # 如果selector为字符串且看起来像xpath（例如以/开头），则使用xpath定位
            if isinstance(selector, str) and selector.strip().startswith("/"):
                return self.u2_driver.xpath(selector)
            # 如果selector为字典，并且包含"xpath"键，则取出其值使用xpath定位
            elif isinstance(selector, dict) and "xpath" in selector:
                return self.u2_driver.xpath(selector["xpath"])
            else:
                return self.u2_driver(**selector)
        except Exception as e:
            lg.error(f"查找元素时发生异常: {e}", exc_info=True)
            return None

    def is_element_exists(self, selector, timeout=3):
        """
        判断元素是否存在，此方法不会报异常，仅返回布尔值
        :param selector: 元素选择器，支持多种定位方式（如 text, description, resourceId, xpath 等）
                           支持传入字典或直接传入 xpath 字符串：
                           1.radio_card = {"resourceId":"com.yaxon.launcher:id/radio_layout"}
                           2.xpath_selector = "//android.widget.Button[@text='确定']"
                           3.xpath_selector = {"xpath": "//android.widget.Button[@text='确定']"}
        :param timeout: 超时时间，单位为秒
        :return: 如果元素存在，返回 True；否则返回 None
        """
        # 如果selector为字符串且符合xpath格式
        if isinstance(selector, str) and selector.strip().startswith("/"):
            element = self.u2_driver.xpath(selector)
        elif isinstance(selector, dict) and "xpath" in selector:
            element = self.u2_driver.xpath(selector["xpath"])
        else:
            element = self.u2_driver(**selector)
        isExist = element.wait(timeout=timeout)
        return isExist if isExist else False

    def swipe_to(
        self,
        direction: str,
        duration: float = 0.1,
        start_ratio: float = None,
        end_ratio: float = None,
        sleep_after: float = 0,
        max_retry: int = 3,
    ) -> None:
        """
        优化后的滑动方法（支持ADB获取分辨率）

        :param direction: 方向 ("上/up", "下/down", "左/left", "右/right")
        :param duration: 滑动持续时间（秒）
        :param start_ratio: 起始点比例（默认根据方向自动设置）
        :param end_ratio: 结束点比例（默认根据方向自动设置）
        :param sleep_after: 滑动后等待时间（秒）
        :param max_retry: 最大重试次数（ADB失败时重试）
        """
        for attempt in range(max_retry):
            try:
                # 获取屏幕分辨率（带缓存）
                if not self._cached_resolution:
                    self._cached_resolution = self._get_screen_resolution()
                width, height = self._cached_resolution

                # 计算坐标
                direction = self._normalize_direction(direction)
                start_x, start_y, end_x, end_y = self._calculate_swipe_points(
                    direction, width, height, start_ratio, end_ratio
                )

                # 执行滑动
                self.u2_driver.swipe(start_x, start_y, end_x, end_y, duration)
                lg.info(
                    f"滑动成功: {direction} | 坐标: ({start_x},{start_y})→({end_x},{end_y})"
                )

                # 滑动后等待
                if sleep_after > 0:
                    time.sleep(sleep_after)
                return

            except Exception as e:
                self._cached_resolution = None  # 清除缓存
                lg.warning(f"滑动失败 (第{attempt + 1}次重试): {str(e)}")
                if attempt == max_retry - 1:
                    raise RuntimeError(f"滑动操作超过最大重试次数: {max_retry}") from e

    def _get_screen_resolution(self) -> tuple:
        """
        通过ADB获取物理分辨率
        为什么要这么做？：因为uiautomator2自带的window_size()在某些设备上方法无法获取屏幕分辨率
        """
        try:
            output = subprocess.check_output(
                ["adb", "shell", "wm", "size"],
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,  # 防止ADB卡死
            )
            if match := re.search(r"Physical size: (\d+)x(\d+)", output):
                width, height = int(match.group(1)), int(match.group(2))
                return (width, height)
            raise ValueError("无法解析分辨率信息")
        except subprocess.TimeoutExpired:
            raise RuntimeError("ADB命令超时，请检查设备连接")
        except Exception as e:
            raise RuntimeError(f"获取分辨率失败: {str(e)}")

    def _normalize_direction(self, direction: str) -> str:
        """统一方向参数为中文"""
        direction_map = {
            "up": "上",
            "down": "下",
            "left": "左",
            "right": "右",
            "上": "上",
            "下": "下",
            "左": "左",
            "右": "右",
        }
        dir_lower = direction.lower()
        if dir_lower not in direction_map:
            raise ValueError(f"无效方向参数: {direction}")
        return direction_map[dir_lower]

    def _calculate_swipe_points(
        self,
        direction: str,
        width: int,
        height: int,
        start_ratio: Union[float, None],
        end_ratio: Union[float, None],
    ) -> tuple:
        """计算滑动坐标点"""
        # 默认滑动比例配置
        defaults = {
            "上": {"axis": "y", "start": 0.2, "end": 0.8},
            "下": {"axis": "y", "start": 0.8, "end": 0.2},
            "左": {"axis": "x", "start": 0.2, "end": 0.8},
            "右": {"axis": "x", "start": 0.8, "end": 0.2},
        }

        # 获取方向配置
        if (config := defaults.get(direction)) is None:
            raise ValueError(f"不支持的方向: {direction}")

        # 使用自定义比例或默认值
        start_ratio = start_ratio if start_ratio is not None else config["start"]
        end_ratio = end_ratio if end_ratio is not None else config["end"]

        # 计算坐标
        axis = config["axis"]
        if axis == "y":
            start_x = end_x = width // 2
            start_y = int(height * start_ratio)
            end_y = int(height * end_ratio)
        else:
            start_y = end_y = height // 2
            start_x = int(width * start_ratio)
            end_x = int(width * end_ratio)

        return (start_x, start_y, end_x, end_y)

    def drag_element_to(
        self,
        source_selector: dict,
        target_selector: dict,
        duration: float = 0.5,
        timeout: int = 10,
    ) -> None:
        """
        拖拽元素到另一个元素
        :param source_selector: 源元素选择器
        :param target_selector: 目标元素选择器
        :param duration: 拖拽持续时间（秒）
        :param timeout: 元素等待超时时间
        """
        try:
            # 等待并获取元素对象
            source = self.wait_for_element_exists(source_selector, timeout)
            target = self.wait_for_element_exists(target_selector, timeout)
            if not (source and target):
                raise ValueError("源或目标元素未找到")

            if (
                self._find_element(source_selector)
                or self._find_element(target_selector) is None
            ):
                raise ValueError("源或目标元素未找到")

            source = self.get_element_attribute(source_selector, attr="bounds")
            target = self.get_element_attribute(target_selector, attr="bounds")
            # 获取元素中心坐标

            source_center = self._get_element_center(source)
            target_center = self._get_element_center(target)

            # 执行拖拽操作
            self.u2_driver.drag(
                source_center[0],
                source_center[1],
                target_center[0],
                target_center[1],
                duration,
            )
            lg.info(f"元素拖拽成功: {source_selector} → {target_selector}")

        except Exception as e:
            lg.error(f"元素拖拽失败: {str(e)}", exc_info=True)
            raise

    def _get_element_center(self, bounds: dict) -> tuple:
        """计算元素中心坐标"""
        left = bounds["left"]
        top = bounds["top"]
        right = bounds["right"]
        bottom = bounds["bottom"]
        return ((left + right) // 2, (top + bottom) // 2)

    def assert_element_exists(self, selector, timeout=3, msg=""):
        """
        验证元素存在
        :param selector: 元素选择器
        :param timeout: 等待超时时间
        :param msg: 错误消息
        """
        if not self.wait_for_element_exists(selector, timeout):
            error_msg = msg or f"元素不存在: {selector}"
            lg.error(error_msg)
            raise AssertionError(error_msg)
        else:
            lg.info(f"元素存在: {selector}")
            return True

    def assert_element_not_exists(self, selector, timeout=3, msg=""):
        """
        验证元素不存在
        :param selector: 元素选择器
        :param timeout: 最大等待时间（单位秒），在该时间内持续检查元素是否消失
        :param msg: 自定义错误消息
        """
        # 核心逻辑反转：如果元素在超时时间内被检测到存在则断言失败
        if self.wait_for_element_exists(selector, timeout):
            error_msg = msg or f"元素被期望不存在,但仍然存在: {selector}"
            lg.error(error_msg)
            raise AssertionError(error_msg)
        else:
            # 只有当整个超时周期内都没有检测到元素时才记录成功
            lg.info(f"元素不存在（符合预期）: {selector}")

        # 显式返回True明确语义（非必须但更清晰）
        return True

    def assert_text_equals(self, selector, expected_text, timeout=10):
        """验证元素文本等于预期值"""
        actual_text = self.get_element_attribute(selector, "text", timeout)
        if actual_text != expected_text:
            error_msg = f"文本不符 | 预期: {expected_text} | 实际: {actual_text}"
            lg.error(error_msg)
            raise AssertionError(error_msg)

    def assert_ele_attr_equals(
        self, selector, attribute_name, expected_value, err_message=None, timeout=10
    ):
        """验证元素属性值等于预期值（自动类型转换）

        Args:
            selector: 元素选择器
            attribute_name: 要验证的属性名
            expected_value: 预期的属性值（支持bool/int/float/str）
            timeout: 超时时间（默认10秒）
            err_message: 自定义错误信息（断言失败时显示）

        特性：
            1. 自动将元素属性值转换为预期值的类型进行比较
            2. 特殊处理布尔型（支持"true"/"false"字符串转换）
            3. 数值型自动进行字符串到数字的类型转换
        """
        # 获取原始属性值（通常是字符串）
        actual_value = self.get_element_attribute(selector, attribute_name, timeout)

        # 执行类型转换
        converted_value = self._convert_actual_value(actual_value, expected_value)

        # 断言比较
        if converted_value != expected_value:
            type_info = f"预期类型: {type(expected_value).__name__}"
            base_error = (
                f"元素: [{selector}]\n"
                f"属性: [{attribute_name}] 验证失败 | {type_info}\n"
                f"预期值: {expected_value}({type(expected_value).__name__})\n"
                f"实际值: {converted_value}({type(converted_value).__name__})"
            )

            # 构建最终错误信息
            error_msg = f"{err_message}\n{base_error}" if err_message else base_error

            # 记录日志并抛出异常
            lg.error(error_msg)
            raise AssertionError(error_msg)

    def _convert_actual_value(self, actual_value, expected_value):
        """类型转换辅助方法"""
        expected_type = type(expected_value)

        # 处理布尔型转换
        if expected_type is bool:
            if isinstance(actual_value, str):
                lower_val = actual_value.strip().lower()
                if lower_val == "true":
                    return True
                if lower_val == "false":
                    return False
            return actual_value

        # 处理数值型转换
        if expected_type in (int, float):
            try:
                # 先转换为float处理小数情况
                num = float(actual_value)
                return num if expected_type is float else int(num)
            except (ValueError, TypeError):
                return actual_value

        # 处理字符串型（显式转换）
        if expected_type is str:
            return str(actual_value)

        # 其他类型尝试直接转换
        try:
            return expected_type(actual_value)
        except (ValueError, TypeError):
            return actual_value

    def scroll_until_find(
        self,
        direction: str,
        target_selector: dict,
        max_swipes: int = 5,
        swipe_duration: float = 0.1,
        edge_ratio: float = 0.2,
    ):
        """
        滚动查找元素（支持边缘检测）
        :param direction: 滚动方向（上/下/左/右）
        :param target_selector: 目标元素选择器
        :param max_swipes: 最大滑动次数
        :param swipe_duration: 滑动持续时间
        :param edge_ratio: 滑动幅度控制
        """
        found = False
        prev_page = None

        for _ in range(max_swipes):
            # 获取当前页面特征（用于检测是否到达边缘）
            current_page = self._get_page_signature()
            if current_page == prev_page:
                lg.warning("检测到页面未变化，可能到达边界")
                break
            prev_page = current_page

            # 查找目标元素
            if self.wait_for_element_exists(target_selector, timeout=1):
                found = True
                time.sleep(0.2)
                return self._find_element(target_selector)

            # 执行滑动
            self.swipe_to(
                direction, duration=swipe_duration, end_ratio=edge_ratio  # 滑动幅度控制
            )

        return None

    def _get_page_signature(self) -> str:
        """获取当前页面特征（用于滚动检测）"""
        xml = self.u2_driver.dump_hierarchy()
        return hash(xml)  # 简单哈希用于比较页面变化

    def click_button_xpath(self, xpath, element_name="控件", timeout=10):
        """
        点击元素
        :param xpath: 元素绝对地址
        :param element_name : 元素名称
        :param timeout: 等待元素超时时间
        """
        try:
            if self.wait_for_element_exists_xpath(xpath, element_name, timeout):
                self.u2_driver.xpath(xpath).click()
                lg.info(f"成功点击元素: {element_name}")
            else:
                lg.error(f"元素不存在，点击失败: {element_name}")
                raise ValueError("元素未找到，点击失败")

        except Exception as e:
            lg.error(
                f"点击元素时发生异常: {element_name}, 错误信息: {e}", exc_info=True
            )
            raise

    def wait_for_element_exists_xpath(self, xpath, element_name="控件", timeout=10):
        """
        元素是否存在
        :param xpath: 元素绝对地址
        :param element_name : 元素名称
        :param timeout: 等待元素超时时间
        """
        try:
            # 使用 u2 的 wait 方法等待元素出现
            isExist = self.u2_driver.xpath(xpath).wait(timeout=timeout)
            # print(element)
            if isExist:
                lg.info(f"元素存在:{element_name}")
            else:
                lg.error(f"元素不存在:{element_name}")
                raise ValueError("元素未找到")

            return isExist
        except Exception as e:
            lg.error(f"等待元素时发生异常: {e}", exc_info=True)
            raise

    def long_press_xpath(self, xpath, element_name="控件", timeout=10):
        """
        长按元素
        :param xpath: 元素绝对地址
        :param element_name : 元素名称
        :param timeout: 等待元素超时时间
        """
        try:
            if self.wait_for_element_exists_xpath(xpath, element_name, timeout):
                self.u2_driver.xpath(xpath).long_click()
                lg.info(f"成功长按元素: {element_name}")
            else:
                lg.error(f"元素不存在，长按失败: {element_name}")
                raise ValueError("元素不存在，长按失败")
        except Exception as e:
            lg.error(
                f"长按元素时发生异常: {element_name}, 错误信息: {e}", exc_info=True
            )
            raise

    def get_element_attribute_xpath(self, xpath, attr, timeout=10):
        """
        获取元素属性值
        :param xpath: 定位元素地址 如果该地址指示多个元素，则默认选取第一个
        :param attr: 要获取的属性名（如 "text", "content-desc", "bounds" 等）
        :param timeout: 等待元素出现的超时时间（秒），默认10秒
        :return: 属性值（存在时）或 None（失败时）
        """
        try:
            if self.wait_for_element_exists_xpath(xpath):
                value = self.u2_driver.xpath(xpath).info.get(attr)

                if value is None:
                    lg.error(f"获取属性值失败，请确认属性是否正确: {attr}")
                    raise ValueError("获取属性值失败，请确认属性是否正确")
                else:
                    if isinstance(value, str):
                        # 判断字符串是否包含 '•'
                        if "•" in value:
                            lg.info(f"属性值包含敏感字符，不打印")
                            return value
                        else:
                            lg.info(f"成功获取元素属性值: {attr}={value}")
                            return value
                    else:
                        lg.info(f"成功获取元素属性值: {attr}={value}")
                        return value

            else:
                lg.error(f"元素不存在")
                raise ValueError("元素不存在")
        except Exception as e:
            lg.error(f"获取属性值时发生异常: 错误信息: {e}", exc_info=True)
            raise

    # 编写一个通过com.yaxon.avm:id/bt_avm_exit 这个rusourceId点击退出按钮的方法
    def click_exit_button(self):
        """
        点击退出按钮
        """
        try:
            if self.wait_for_element_exists(
                {"resourceId": "com.yaxon.avm:id/bt_avm_exit"}
            ):
                self.u2_driver(resourceId="com.yaxon.avm:id/bt_avm_exit").click()
                lg.info(f"成功点击退出按钮")
            else:
                lg.error(f"退出按钮不存在")
                raise ValueError("退出按钮不存在")
        except Exception as e:
            lg.error(f"点击退出按钮时发生异常: 错误信息: {e}", exc_info=True)


if __name__ == "__main__":
    # d = u2.connect()
    # width, height = 1920, 720
    # # print(width,height)
    # start_x, start_y = width // 2, height * 0.8  # 从屏幕底部中间开始
    # end_x, end_y = (width // 2) - (width // 3), height * 0.8  # 滑动到屏幕顶部中间
    # d.swipe(start_x, start_y, end_x, end_y, duration=0.01)  # duration 是滑动持续时间，单位为秒
    #
    # po = PO_Base()
    # po.u2_driver.swipe(1000, 0, 500, 500, 0.5)  # 下拉通知栏
    # time.sleep(2)
    # po.u2_driver.swipe(900, 710, 900, 300, 0.1)  # 收起通知栏
    # print(po.u2_driver.window_size())
    # time.sleep(3)
    po = PO_Base()
    print(po.is_element_exists({"resourceId": "com.yaxon.radio:id/tv_list_empty"}))
    # connect_device("Android:///")
    # # pos = po.at_assert_img_exist(r"F:\ATS\yaxonats\case_script\fudaiA6_new\PO_fudaiA6\PO_radiopage\image\收音机.png")
    # pos = po.at_assert_img_exist(r"\yaxonats\case_script\fudaiA6_new\PO_fudaiA6\PO_radiopage\image\无标题.png")
    # print(pos)
    # po.at_img_touch(r"F:\ATS\yaxonats\case_script\fudaiA6_new\PO_fudaiA6\PO_radiopage\image\音乐.png")
    # xpath = """//*[@resource-id="com.android.systemui:id/quick_menu"]/android.widget.FrameLayout[2]//android.widget.ImageView"""
    # print(po.get_element_attribute_xpath(xpath, "selected"))
    #
    # po.go_home("menu")
    # po.go_home("home")
    # po.wait_for_element_exists({"text": "音乐"}, timeout=5)
    # po.swipe_to("左")
    # po.swipe_to("右")
    # po.swipe_to("上")
    # selector = {"text": "音乐"}
    # element = po._find_element(selector)
    # element.click()
    # po.swipe_to("下")
    # po.swipe_to("上")
    # po.swipe_to("左")
    # time.sleep(1)
    # po.swipe_to("右")
