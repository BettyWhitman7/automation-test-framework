import os
import functools
import inspect
from config import Config
from tools.log_tool import log


def validate_image_path(func):
    """
    图片路径校验装饰器
    功能：
    1. 将相对路径转换为基于IMAGE_ROOT_DIR的绝对路径
    2. 去除路径中重复的根目录部分
    3. 校验图片文件是否存在
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        if 'image_dir' not in bound_args.arguments:
            return func(*args, **kwargs)

        original_path = bound_args.arguments['image_dir']

        try:
            # 路径解析处理
            processed_path = _process_image_path(original_path)
            bound_args.arguments['image_dir'] = processed_path

            # 文件存在性校验
            if not os.path.exists(processed_path):
                raise FileNotFoundError(f"Image file not found: {processed_path}")

        except Exception as e:
            log.error(f"路径校验失败: {original_path}")
            log.error(f"处理后的路径: {processed_path}")
            log.exception("路径校验异常详情")
            raise

        return func(*bound_args.args, **bound_args.kwargs)

    return wrapper


def _process_image_path(input_path: str) -> str:
    """路径处理核心逻辑"""
    # 获取标准化的根目录（建议Config.LOG_DIR配置为绝对路径）
    root_dir = os.path.normpath(Config.LOG_DIR)

    # 处理相对路径，若不是绝对路径则基于root_dir拼接
    if not os.path.isabs(input_path):
        abs_path = os.path.join(root_dir, input_path)
    else:
        abs_path = input_path

    normalized_path = os.path.normpath(abs_path)

    # 分割驱动器和余下部分，避免后续分割时丢失驱动器末尾的反斜杠
    drive_root, rest_root = os.path.splitdrive(root_dir)
    drive_path, rest_path = os.path.splitdrive(normalized_path)

    # 将路径余下部分按os.sep拆分为列表
    root_parts = rest_root.strip(os.sep).split(os.sep) if rest_root else []
    path_parts = rest_path.strip(os.sep).split(os.sep) if rest_path else []

    # 查找重复部分
    overlap_index = _find_repetition(root_parts, path_parts)

    if overlap_index > 0:
        # 去除重复的部分后，使用根目录部分再拼接后面的剩余部分
        processed_parts = root_parts + path_parts[overlap_index:]
    else:
        processed_parts = path_parts

    # 重新拼接路径（此时不包含驱动器）
    processed_path = os.path.join(*processed_parts) if processed_parts else ""
    # 将驱动器补回（drive_path优先，否则使用drive_root）
    drive = drive_path if drive_path else drive_root
    # 注意：如果drive为形如"F:"，需要补上反斜杠
    if drive and not drive.endswith(os.sep):
        processed_path = drive + os.sep + processed_path
    else:
        processed_path = drive + processed_path

    return os.path.normpath(processed_path)


def _find_repetition(base_parts: list, target_parts: list) -> int:
    """
    查找目标路径中与根目录重复的部分
    如果目标路径开头即等于根目录，则返回 len(base_parts)
    否则尝试在后续查找完整的重复部分，未找到则返回 0
    """
    base_len = len(base_parts)
    target_len = len(target_parts)
    # 如果目标路径开头与根目录相同，则重合部分长度为 base_len
    if target_parts[:base_len] == base_parts:
        return base_len

    # 尝试在后续查找根目录完整出现的情况
    for i in range(1, target_len - base_len + 1):
        if target_parts[i:i + base_len] == base_parts:
            return i + base_len
    return 0
