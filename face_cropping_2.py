# 迭代编号：2
import os
import errno
import stat
import cv2
import numpy as np
import shutil
import insightface
from insightface.app import FaceAnalysis
from tqdm import tqdm
from pathlib import Path
from PIL import Image

def handle_remove_readonly(func, path, exc):
    """移除只读文件的异常处理函数。"""
    excvalue = exc[1]
    if func in (os.rmdir, os.unlink) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU)
        func(path)
    else:
        raise

def decimal_to_custom_base(n):
    """将十进制数字转换为使用自定义非混淆字符集的基25字符串。"""
    characters = 'acdefhjkmnpqrtuvwxyz23478'
    base = len(characters)
    if n == 0:
        return characters[0]
    result = ""
    while n > 0:
        n, remainder = divmod(n, base)
        result = characters[remainder] + result
    return result

def prepare_directory(directory):
    """准备输出目录，确保目录存在且干净。"""
    target_dir = Path(directory)
    faces_dir = target_dir / "faces"
    mapping_file_path = target_dir / "face_mapping.txt"

    if not target_dir.is_dir():
        tqdm.write(f"目录不存在: {directory}")
        return None, None

    if faces_dir.exists():
        tqdm.write(f"删除已存在的人脸图片目录: {faces_dir}")
        try:
            shutil.rmtree(faces_dir, onerror=handle_remove_readonly)
        except Exception as e:
            tqdm.write(f"删除人脸图片目录失败, 尝试清空目录")
            # 递归目录删除所有文件
            for file_name in faces_dir.iterdir():
                file_path = faces_dir / file_name
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path, onerror=handle_remove_readonly)
    faces_dir.mkdir(parents=True, exist_ok=True)

    if mapping_file_path.exists():
        tqdm.write(f"删除已存在的映射文件: {mapping_file_path}")
        mapping_file_path.unlink()

    return faces_dir, mapping_file_path

def get_image_mapping(file_path):
    """从映射文件中读取缩略图与原始图片的关系。"""
    mapping_dict = {}
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                original, thumbnail = line.strip().split('*')
                tqdm.write(f"映射: {original} -> {thumbnail}")
                mapping_dict[thumbnail] = original
    except Exception as e:
        tqdm.write(f"读取映射文件失败: {e}")
    return mapping_dict

def calculate_original_coordinates(x, y, x2, y2, original_img, thumbnail_img, thumbnail_size):
    """根据缩略图中的坐标和原始图像尺寸计算原始图像中的坐标。"""
    # tqdm.write(f"缩略图尺寸: {thumbnail_img.shape}, 原始图像尺寸: {original_img.shape}")
    scale_width = original_img.shape[1] / thumbnail_img.shape[1]
    scale_height = original_img.shape[0] / thumbnail_img.shape[0]
    # tqdm.write(f"缩放比例: {scale_width}, {scale_height}")
    scale = max(scale_width, scale_height)
    scaled_width = original_img.shape[1] / scale
    scaled_height = original_img.shape[0] / scale
    # tqdm.write(f"缩放后尺寸: {scaled_width}, {scaled_height}")
    offset_x = (thumbnail_size - scaled_width) / 2
    offset_y = (thumbnail_size - scaled_height) / 2
    # tqdm.write(f"偏移量: {offset_x}, {offset_y}")
    # 转换坐标到原始图像
    original_x = int((x - offset_x) * scale)
    original_y = int((y - offset_y) * scale)
    original_x2 = int((x2 - offset_x) * scale)
    original_y2 = int((y2 - offset_y) * scale)
    return original_x, original_y, original_x2, original_y2

def process_images(thumbnail_paths, output_dir, mapping_dict, thumbnail_size=512):
    """处理图像列表中的每个图像，识别人脸并保存裁剪的人脸图像。"""
    if len(thumbnail_paths) == 0:
        tqdm.write("没有缩略图图片")
        return []
    if len(mapping_dict) == 0:
        tqdm.write("没有映射关系")
        return []
    expand_range = 0.2
    app = FaceAnalysis(providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(512, 512))
    face_mappings = []
    for index, thumb_path in enumerate(tqdm(thumbnail_paths, desc="处理图片")):
        thumbnail_img = cv2.imread(str(thumb_path))
        original_img_path = mapping_dict.get(thumb_path.stem)
        original_img = cv2.imread(original_img_path) if original_img_path else None
        if original_img is None:
            tqdm.write(f"找不到 {thumb_path.name} 的原始图片: {original_img_path}")
            continue
        faces = app.get(thumbnail_img)
        # faces = app.get(original_img)
        for face_id, face in enumerate(faces):
            bbox = face.bbox.astype(int)
            x, y, x2, y2 = bbox
            # tqdm.write(f"人脸坐标: {x}, {y}, {x2}, {y2}")
            w, h = x2 - x, y2 - y
            # tqdm.write(f"人脸尺寸: {w}, {h}")
            x, y = max(0, x - int(expand_range * 0.5 * w)), max(0, y - int(expand_range * 0.5 * h))
            x2, y2 = min(thumbnail_img.shape[1], x2 + int(expand_range * 0.5 * w)), min(thumbnail_img.shape[0], y2 + int(expand_range * 0.5 * h))
            # tqdm.write(f"调整后的人脸坐标: {x}, {y}, {x2}, {y2}")
            cropped_face_thumbnail = thumbnail_img[y:y2, x:x2]
            x, y, x2, y2 = calculate_original_coordinates(x, y, x2, y2, original_img, thumbnail_img, thumbnail_size)
            # tqdm.write(f"坐标转换后的人脸坐标: {x}, {y}, {x2}, {y2}")
            # 确保坐标在原图范围内
            x, y, x2, y2 = max(0, x), max(0, y), min(x2, original_img.shape[1]), min(y2, original_img.shape[0])

            cropped_face = original_img[y:y2, x:x2]
            face_filename = decimal_to_custom_base(index * 100 + face_id) + ".jpg"
            face_file_thumbnail = decimal_to_custom_base(index * 100 + face_id) + "_thumbnail" + ".jpg"
            cv2.imwrite(str(output_dir / face_file_thumbnail), cropped_face_thumbnail)
            cv2.imwrite(str(output_dir / face_filename), cropped_face)
            with open(str(output_dir / (face_filename[:-4] + ".txt")), 'w') as f:
                f.write(str(face))
            face_mappings.append(f"{original_img_path}*{face_filename}")
    return face_mappings

def save_mappings(mapping_file_path, mappings):
    """保存映射到文件。"""
    with open(mapping_file_path, 'w') as f:
        for mapping in mappings:
            f.write(mapping + "\n")

def parse_unique_images(file_path):
    """解析文件以获取位于'Unique Images:'部分下的图片列表。"""
    with open(file_path, 'r') as file:
        recording = False
        images = []
        for line in file:
            line = line.strip()
            if line == "Unique Images:":
                recording = True
                continue
            elif line.endswith(":") and recording:
                # 假设任何以冒号':'结尾的行都标志着新的标题开始，因此停止记录
                break
            if recording and line:
                images.append(line)
    return images

def main(image_list_file):
    """主函数，负责整个处理流程。"""
    directory = Path(image_list_file).parent
    output_dir, mapping_file_path = prepare_directory(directory)
    if output_dir is None:
        return

    # 读取缩略图列表和映射文件
    thumbnail_paths = [directory / 'thumbnail' / image_name for image_name in parse_unique_images(image_list_file)]
    mapping_dict = get_image_mapping(directory / 'mapping.txt')
    mappings = process_images(thumbnail_paths, output_dir, mapping_dict)
    save_mappings(mapping_file_path, mappings)

# 示例用法
# main("/Volumes/192.168.1.173/pic/陈都灵_503[167_MB]/descriptor_2_ORBDetector_20240513161411.txt")
main("/Volumes/192.168.1.173/pic/test/descriptor_0_HashDetector_20240519202916.txt")
