#!/usr/bin/env python
import os
import time
from datetime import datetime, timedelta

import yaml


def find_parent_directory_with_child(start_path, target_child):
    """
    逐级轮询目录，查找包含指定子目录的父目录

    参数:
        start_path (str): 开始搜索的根目录
        target_child (str): 要查找的子目录名称

    返回:
        str: 包含目标子目录的父目录路径，如果未找到则返回None
    """
    # 规范化路径，处理可能的路径分隔符问题
    current_path = os.path.normpath(start_path)

    while True:
        # 检查当前路径下是否存在目标子目录
        target_path = os.path.join(current_path, target_child)
        if os.path.isdir(target_path):
            return current_path

        # 获取上一级目录
        parent_path = os.path.dirname(current_path)

        # 如果已经到达根目录，停止搜索
        if parent_path == current_path:
            break

        current_path = parent_path

    return None


def get_timestamp(dateStr=None, _format="%Y-%m-%d %H:%M:%S", delta_hours=0):
    """
    获取时间戳（毫秒级）。

    Args:
        dateStr (str, optional): 时间字符串。默认为None。
        _format (str, optional): 时间字符串的格式。默认为"%Y-%m-%d %H:%M:%S"。
        delta_hours (int, optional): 需要增加的小时数。默认为0。

    Returns:
        int: 时间戳（毫秒级）。

    """
    if dateStr:
        # 将时间字符串转换为datetime对象
        time_object = datetime.strptime(dateStr, _format)
        # 将datetime对象转换为时间戳（秒级）
        timestamp = int(time_object.timestamp())
    else:
        if isinstance(delta_hours, str):
            delta_hours = eval(delta_hours)
        now = datetime.now()
        # 计算当前时间与delta_hours小时后的时间差
        delta = now + timedelta(hours=delta_hours)
        # 将datetime对象转换为时间戳（秒级）
        timestamp = int(delta.timestamp())
    return int(round(timestamp * 1000))


def get_time_str(delta_hours=0, _format="%Y-%m-%d %H:%M:%S"):
    """
    获取指定时间间隔后的时间字符串。

    Args:
        delta_hours (int): 时间间隔，以小时为单位，默认为0小时。
        _format (str): 时间字符串的格式，默认为"%Y-%m-%d %H:%M:%S"。

    Returns:
        str: 指定的时间间隔后的时间字符串。

    """
    if isinstance(delta_hours, str):
        delta_hours = eval(delta_hours)
    now = datetime.now()
    # 计算当前时间与delta_hours小时后的时间差
    delta = now + timedelta(hours=delta_hours)
    # 将datetime对象转换为时间戳（秒级）
    timestamp = int(delta.timestamp())
    local_time = time.localtime(timestamp)
    time_str = time.strftime(_format, local_time)
    return time_str


def is_date_str(date_str, _format="%Y-%m-%d %H:%M:%S"):
    try:
        datetime.strptime(date_str, _format)
        return True
    except (ValueError, TypeError):
        return False


def get_config(path):
    """
    从指定路径读取配置文件并返回配置内容。

    Args:
        path (str): 配置文件的路径。

    Returns:
        dict: 配置内容，类型为字典。

    Raises:
        FileNotFoundError: 如果指定的路径不存在。
        yaml.YAMLError: 如果YAML文件存在语法错误。

    """
    with open(path, encoding='utf-8') as f:
        cfgs = yaml.safe_load(f)
    return cfgs


def download_image(response, save_path, chunk_size=1024):
    """
    下载图片并保存到指定路径。

    Args:
        response (requests.Response): HTTP请求的响应对象。
        save_path (str): 图片的保存路径。
        chunk_size (int, optional): 每次读取的数据块大小，默认为1024字节。

    Returns:
        bool: 如果下载成功并保存了图片，则返回True；否则返回False。

    """
    # 检查请求是否成功
    if response.status_code == 200:
        # 设置图片类型
        content_type = response.headers.get('Content-Type')
        if content_type and 'image' in content_type:
            # 确定图片扩展名
            ext = content_type.split('/')[-1]
            if not save_path.endswith(ext):
                save_path += f'.{ext}'

            # 保存图片
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size):
                    f.write(chunk)
            print(f"图片已保存到: {save_path}")
            return True
        else:
            print("URL不是有效的图片链接")
    else:
        print(f"请求失败，状态码: {response.status_code}")

    return False


def calculate_time_difference(datetime_str1, datetime_str2, format_str="%Y-%m-%d %H:%M:%S"):
    """
    计算两个日期时间字符串的差值

    参数:
        datetime_str1: 第一个日期时间字符串
        datetime_str2: 第二个日期时间字符串
        format_str: 日期时间格式字符串(默认为"%Y-%m-%d %H:%M:%S")

    返回:
        时间差(timedelta对象)
    """
    # 将字符串转换为datetime对象
    dt1 = datetime.strptime(datetime_str1, format_str)
    dt2 = datetime.strptime(datetime_str2, format_str)

    # 计算差值
    return dt2 - dt1  # 返回dt2减去dt1的结果


def get_delta_time(time1, time2, fmt="[%H:%M:%S.%f]", offset=0.0):
    t1 = datetime.strptime(time1, fmt)
    t2 = datetime.strptime(time2, fmt)
    delta = (t2 - t1).total_seconds()
    return delta - offset if delta - offset > 0 else 0


if __name__ == "__main__":
    get_time_str(30)
