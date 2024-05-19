import os
import shutil
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from pathlib import Path
from tqdm import tqdm

# 迭代编号：2
# 这个函数用于将十进制数转换为基于特定字符集的字符串，防止编码混淆 迭代编号：2
def decimal_to_custom_base(n):
    characters = 'acdefhjkmnpqrtuvwxyz23478'  # 非混淆字符集
    base = len(characters)
    if n == 0:
        return characters[0]
    result = ""
    while n > 0:
        n, remainder = divmod(n, base)
        result = characters[remainder] + result
    return result

# 这个函数用于处理指定目录下的所有图片，进行面部检测和裁剪 迭代编号：2
def process_directory(directory):
    app = FaceAnalysis(providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(512, 512))  # 初始化面部分析模型

    target_dir = Path(directory)
    face_dir = target_dir / "faces"
    mapping_file_path = target_dir / "face_info.txt"

    if not target_dir.is_dir():
        print(f"Directory does not exist: {directory}")
        return

    if face_dir.exists():
        shutil.rmtree(face_dir)  # 删除存在的目录
    face_dir.mkdir(parents=True, exist_ok=True)  # 创建新目录

    with open(mapping_file_path, 'w', encoding='utf-8') as f:  # 打开记录文件
        face_count = 0
        for img_path in tqdm(list(target_dir.glob('*.jpg'))):  # 遍历目录下的jpg图片
            img = cv2.imread(str(img_path))
            faces = app.get(img)  # 进行面部检测
            tqdm.write(f"Found {len(faces)} faces in {img_path}")
            for face in faces:
                bbox = face['bbox']
                x1, y1, x2, y2 = map(int, bbox[:4])
                cropped_img = img[y1:y2, x1:x2]  # 裁剪人脸
                face_filename = f"{decimal_to_custom_base(face_count)}.jpg"  # 生成文件名
                cv2.imwrite(str(face_dir / face_filename), cropped_img)  # 保存裁剪的人脸图片
                f.write(f"{img_path}*{face_filename}\n{face}\n")  # 记录信息
                face_count += 1

# 使用示例
process_directory("/Volumes/192.168.1.173/pic/test")  # 替换为实际的图片目录路径
