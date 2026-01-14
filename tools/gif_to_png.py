import imageio
import numpy as np
import cv2
from PIL import Image
from scipy.stats import entropy


def calculate_frame_entropy(frame):
    """计算单帧图像熵值（信息量指标）"""
    # 转换为灰度图
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    # 计算直方图
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    # 归一化直方图
    hist /= hist.sum()
    # 计算熵值
    return entropy(hist.flatten())


def calculate_frame_difference(prev_frame, curr_frame):
    """计算两帧之间的差异度"""
    # 转换为灰度图
    gray_prev = cv2.cvtColor(prev_frame, cv2.COLOR_RGB2GRAY)
    gray_curr = cv2.cvtColor(curr_frame, cv2.COLOR_RGB2GRAY)
    # 计算绝对差异
    diff = cv2.absdiff(gray_prev, gray_curr)
    # 返回非零像素比例
    return np.mean(diff > 25)  # 阈值可调


def select_max_info_frame(gif_path, method='entropy', diff_threshold=0.1):
    """
      从GIF中选择信息量最大的帧
      参数：
          gif_path: 输入GIF路径
          method: 选择方法 ('entropy'/'difference')
          diff_threshold: 差异法最小变化阈值
      返回：
          最佳帧索引和图像数据
      """
    try:
        # 读取所有帧
        frames = imageio.mimread(gif_path, memtest=False)
        if len(frames) < 2:
            return 0, frames[0]  # 不足两帧直接返回

        best_score = -np.inf
        best_frame_idx = 0
        prev_frame = None

        for idx, frame in enumerate(frames):
            # 预处理：转换为RGB格式
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

            if method == 'entropy':
                # 熵值法
                current_score = calculate_frame_entropy(rgb_frame)
            elif method == 'difference':
                # 差异法（需要比较前帧）
                if prev_frame is not None:
                    current_score = calculate_frame_difference(prev_frame, rgb_frame)
                    # 仅当变化超过阈值时更新
                    if current_score < diff_threshold:
                        current_score = 0
                else:
                    current_score = 0  # 首帧差异法不参与评分
                prev_frame = rgb_frame
            else:
                raise ValueError("无效方法，请选择'entropy'或'difference'")

            # 更新最佳帧
            if current_score > best_score:
                best_score = current_score
                best_frame_idx = idx

        return best_frame_idx, frames[best_frame_idx], frames

    except Exception as e:
        print(f"处理失败: {str(e)}")
        return 0, frames[0] if frames else None, frames


def gif_to_png(gif_path="getCaptcha.gif", output_png=None, frame_index=0):
    """
    将GIF指定帧转换为PNG格式
    参数：
        gif_path: 输入GIF路径
        output_png: 输出PNG路径
        frame_index: 要提取的帧序号（默认0，即第一帧）
    """

    if ".png" not in str(output_png).lower():
        output_png += '.png'
    try:
        best_idx, best_frame, frames = select_max_info_frame(gif_path=gif_path)
        # 转换为PIL Image对象（处理调色板格式）
        pil_image = Image.fromarray(best_frame)
        # 保存为PNG（自动处理透明通道）
        pil_image.save(output_png, format='PNG')
        return {
            'success': True,
            'message': f'成功提取第{frame_index}帧',
            'frame_count': len(frames)
        }

    except Exception as e:
        result = {'success': False, 'error': f'处理失败: {str(e)}'}
        return result


# 使用示例
if __name__ == '__main__':
    ...
