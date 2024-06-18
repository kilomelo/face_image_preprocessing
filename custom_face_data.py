import os
import pickle
import numpy as np

class CustomFace:
    def __init__(self, data):
        self.bbox = data['bbox']  # 人脸框，格式为[x, y, width, height]，标识图像中人脸的位置和大小。
        self.kps = data['kps']  # 关键点坐标，通常包括眼睛、鼻子、嘴巴等特征点的位置。
        self.det_score = data['det_score']  # 人脸检测得分，表示检测到的人脸的置信度。
        self.landmark_3d_68 = data['landmark_3d_68']  # 68个3D人脸关键点，提供了人脸的三维结构信息。
        self.pose = data['pose']  # 人脸姿态，包括俯仰角、偏航角和翻滚角，描述人脸相对于相机的方向。
        self.landmark_2d_106 = data['landmark_2d_106']  # 106个2D人脸关键点，用于更精细的面部特征分析。
        self.gender = data['gender']  # 性别预测结果，通常为男性或女性。
        self.age = data['age']  # 年龄预测结果，估计的人脸年龄。
        self.embedding = data['embedding']  # 人脸的特征向量，用于人脸识别和验证等高级任务。


def serialize_face(face, file_path):
    if os.path.exists(file_path):
        return
    # 将面部数据转换为字典并序列化
    data_to_save = {
        'bbox': face.bbox,
        'kps': face.kps,
        'det_score': face.det_score,
        'landmark_3d_68': face.landmark_3d_68,
        'pose': face.pose,
        'landmark_2d_106': face.landmark_2d_106,
        'gender': face.gender,
        'age': face.age,
        'embedding': face.embedding
    }
    with open(file_path, 'wb') as f:
        pickle.dump(data_to_save, f)

def deserialize_face(file_path):
    # 从文件加载数据并重建面部数据对象
    with open(file_path, 'rb') as f:
        data_loaded = pickle.load(f)
    return CustomFace(data_loaded)