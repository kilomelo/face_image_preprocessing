# 迭代编号：1

import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from insightface.data import get_image as ins_get_image
from pathlib import Path
import shutil
import logging

# 配置日志设置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_remove_readonly(func, path, exc):
    """处理只读文件的删除
    参数:
        func: 调用的函数
        path: 文件路径
        exc: 异常信息
    """
    # 尝试取消只读并再次删除
    import os, stat
    os.chmod(path, stat.S_IWRITE)
    func(path)

def process_images(directory):
    """处理目录中的所有图片文件，识别出人脸并保存标记后的图片
    参数:
        directory (str): 目录路径
    """
    # 初始化insightface
    app = FaceAnalysis(providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])  # 迭代编号：1
    app.prepare(ctx_id=0, det_size=(640, 640))  # 迭代编号：1

    # 目标目录和faces目录的路径
    target_dir = Path(directory)
    faces_dir = target_dir / "draw_faces"
    
    # 检查目录是否存在
    if not target_dir.is_dir():
        logging.error(f"目录不存在: {directory}")
        return

    # 删除已存在的faces目录
    if faces_dir.exists():
        logging.info(f"删除已存在的faces目录: {faces_dir}")
        shutil.rmtree(faces_dir, onerror=handle_remove_readonly)
    faces_dir.mkdir(parents=True, exist_ok=True)

    # 遍历目录下的所有图片文件
    for image_file in target_dir.glob("*.jpg"):
        logging.info(f"处理文件: {image_file}")
        
        # 读取图片
        img = cv2.imread(str(image_file))
        if img is None:
            logging.error(f"无法读取图片: {image_file}")
            continue

        # 检测人脸
        faces = app.get(img)  # 迭代编号：1

        # 绘制人脸框和置信度
        for face in faces:
            bbox = face.bbox.astype(int)
            det_score = face.det_score
            cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 255, 0), 2)  # cyan色框
            cv2.putText(img, f'det_score: {det_score:.2f}', (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)  # 置信度文本

        # 保存处理后的图片
        output_path = faces_dir / image_file.name
        cv2.imwrite(str(output_path), img)
        logging.info(f"保存处理后的图片: {output_path}")

if __name__ == "__main__":
    # 指定要处理的目录
    directory = "/Volumes/192.168.1.173/pic/test"  # 修改为实际路径
    process_images(directory)
