import os
import time

import cv2
import numpy as np
import uiautomator2 as u2
from PIL import Image

from config import Config
from framework.var import globals_var


def imread(file_path):
    image = cv2.imread(file_path)
    if image is None:
        # 使用 numpy.fromfile 读取文件
        image_np = np.fromfile(file_path, dtype=np.uint8)
        # 使用 cv2.imdecode 解码图像
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    return image


def find_template(template_path, threshold=0.9, is_check_color=True):
    """
    在屏幕图像中查找模板图像的位置。
    :param template_path: 模板图像（灰度图）
    :param threshold: 匹配阈值，默认 0.8
    :param is_check_color: 是否对颜色进行校验，默认 True
    :return: 匹配位置的左上角坐标 (x, y)，如果未找到返回 None
    """
    # 连接设备并截屏
    d = globals_var.d or u2.connect()
    screenshot = d.screenshot()
    screenshot_dir = Config.ROOT_DIR + "/reports/img"
    file_path = f"{screenshot_dir}/screen.png"
    screenshot.save(file_path)
    template = imread(template_path)
    # 加载图像
    screen = imread(file_path)
    cv2.imread(file_path)
    if is_check_color:
        template = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
        screen = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        # 计算中心点
        h, w, *other = template.shape
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return center_x, center_y
    return None


if __name__ == '__main__':
    t = time.time()
    print(u2.connect().click(*find_template(r"F:\workspace\yaxonats\case_script\fudaiA6\testcase\功能测试\空调\测试数据\外循环模式.png")))
    print(time.time() - t)
