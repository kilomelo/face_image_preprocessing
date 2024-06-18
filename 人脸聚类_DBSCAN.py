# 迭代编号：3
import os
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import dlib
import numpy as np
from pathlib import Path
from custom_face_data import CustomFace, deserialize_face
import logging
import json
from tqdm import tqdm
from 聚类结果可视化 import plot_embeddings
# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_face_data(directory_path, num_limit):
    """
    从指定目录加载所有人脸数据和文件名。
    参数:
        directory_path: str, 包含人脸数据文件的目录路径。
    返回:
        face_data: list, 包含所有加载的人脸数据。
        face_files: list, 对应的人脸数据文件名。
    """
    logging.info(f"加载数据从目录: {directory_path}")
    face_data = []
    face_files = []
    disus_cnt = 0
    progress = tqdm(total=num_limit, desc="读取人脸信息")
    for filename in os.listdir(directory_path):
        if filename.endswith(".pkl"):
            file_path = os.path.join(directory_path, filename)
            face = deserialize_face(file_path)
            # 过滤掉不符合条件的数据
            if face.gender != 0 or face.det_score < 0.6 or face.age < 10 or face.age > 50:
                disus_cnt += 1
                continue
            face_data.append(deserialize_face(file_path))
            face_files.append(filename)
            progress.update(1)
            if len(face_data) >= num_limit:
                break
    logging.info(f"已加载{len(face_data)}个人脸数据, 淘汰 {disus_cnt} 个数据")
    return face_data, face_files

def save_cluster_results(labels, core_sample_indices, face_files, output_file_path):
    """
    根据聚类结果和面部文件名生成字典并保存到文件。
    参数:
        labels: list, 每个数据点的簇标签。
        core_sample_indices: 核心样本的索引。
        face_files: list, 对应的人脸文件名。
        output_file_path: str, 输出文件的路径。
    """
    cluster_dict = {}
    cluster_cnt = 0
    for label, file in zip(labels, face_files):
        # 确保label是标准的int类型
        label = int(label)  # 转换numpy.int64到Python的int
        if label not in cluster_dict:
            cluster_dict[label] = []
            if label != -1: cluster_cnt += 1
        cluster_dict[label].append(Path(file).stem)
    logging.info(f"聚类字典创建完成，包含 {cluster_cnt} 个簇")
    print({f"{key}: {len(value)}" for key, value in cluster_dict.items()})
    logging.info(f"核心样本数量: {len(core_sample_indices)}")
    core_sample_indices = [face_files[int(x)].split('.')[0] for x in core_sample_indices]  # 转换 numpy.int64 为 Python int

    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump({'cluster_dict': cluster_dict, 'core_sample_indices': list(core_sample_indices)}, file, indent=4, ensure_ascii=False)
    logging.info(f"聚类结果已保存为JSON格式到文件: {output_file_path}")

# 主程序部分
# directory_path = '/Volumes/192.168.1.173/pic/test/faces'  # 设定人脸数据目录路径
directory_path = '/Volumes/Data512/pic/热巴_6654[53_GB]/'  # 设定人脸数据目录路径

if not os.path.exists(directory_path):
    logging.error(f"目录不存在: {directory_path}")
    exit(1)

# 加载人脸数据
face_data, face_files = load_face_data(os.path.join(directory_path, 'faces'), 500)
embeddings = [face.embedding for face in face_data]
embeddings = np.array(embeddings)
# embeddings = StandardScaler().fit_transform(embeddings)  # 数据标准化

use_dlib = False
# 似乎chinese_whispers_clustering不认insightface生成的特征向量，无法聚类
if use_dlib:
    def convert_to_similarity(distances, scale=1.0):
        return np.exp(-distances * scale)

    # 假设embeddings已经标准化
    distances = np.linalg.norm(embeddings[:, None] - embeddings, axis=-1)
    similarities = convert_to_similarity(distances)

    # 转换为dlib向量
    embeddings_dlib = [dlib.vector(similarity_row) for similarity_row in similarities]

    # embeddings_dlib = [dlib.vector(array) for array in embeddings]
    logging.info(f"len of embedding: {len(embeddings_dlib[0])}")
    labels = dlib.chinese_whispers_clustering(embeddings_dlib, 0.9)
    num_classes = len(set(labels))
    logging.info("Number of clusters: {}".format(num_classes))
else:
    eps = 28
    min_samples = 2048
    logging.info(f"开始使用 DBSCAN 分类, eps: {eps}, min_samples: {min_samples}")
    # 使用DBSCAN算法对人脸数据进行聚类。
    # eps: float, DBSCAN的邻域半径。
    # min_samples: int, 形成稳定区域所需的最小样本点数。
    clt = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean")
    clt.fit(embeddings)
    logging.info(f"聚类完成")

    output_file_path = os.path.join(directory_path, f"face_classify_{eps}_{min_samples}_{len(face_data)}.txt")  # 设定输出文件路径
    save_cluster_results(clt.labels_, clt.core_sample_indices_, face_files, output_file_path)  # 保存聚类结果
    labels = np.array(clt.labels_)

    for i, label in enumerate(labels):
        if i in clt.core_sample_indices_:
            labels[i] = 65535 - label

plot_embeddings(embeddings, labels, 'pca_3d', 1, 0.5)  # 进行数据可视化，可视化方法：pca_2d / t-sne_2d / pca_3d