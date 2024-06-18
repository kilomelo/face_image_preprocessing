# http://dlib.net/files/shape_predictor_5_face_landmarks.dat.bz2
# http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2

import sys
import os
import dlib
from tqdm import tqdm
import imageio  # 导入imageio库

def main(img_folder_path, limit, distance=0.4):
    predictor_path = 'shape_predictor_5_face_landmarks.dat'
    face_rec_model_path = 'dlib_face_recognition_resnet_model_v1.dat'
    faces_folder_path = img_folder_path + '/faces'
    output_folder_path = img_folder_path + '/clutered'

    # Load all the necessary models
    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(predictor_path)
    facerec = dlib.face_recognition_model_v1(face_rec_model_path)

    descriptors = []
    images = []
    # limit = 100000
    min_cluster_size = 2  # Minimum number of images in a cluster to be saved
    progress = tqdm(desc="load faces", total=limit)
    cnt = 0

    # Process each face and compute 128D face descriptors
    for filename in os.listdir(faces_folder_path):
        if not filename.endswith(".jpg") or filename.startswith('.'):
            continue
        cnt += 1
        if cnt > limit:
            break
        progress.update(1)
        f = os.path.join(faces_folder_path, filename)
        img = dlib.load_rgb_image(f)
        dets = detector(img, 1)

        for k, d in enumerate(dets):
            shape = sp(img, d)
            face_descriptor = facerec.compute_face_descriptor(img, shape)
            descriptors.append(face_descriptor)
            images.append((img, shape, f))

    progress.close()
    # Cluster the faces
    labels = dlib.chinese_whispers_clustering(descriptors, distance)
    num_classes = len(set(labels))
    print("Number of clusters: {}".format(num_classes))

    # Prepare to save faces by cluster
    output_folder_path += f'/dlib_{limit}_{distance}'
    cluster_info = {}

    # Gather cluster information
    for label in set(labels):
        cluster_size = sum(1 for l in labels if l == label)
        if cluster_size >= min_cluster_size:
            cluster_info[label] = cluster_size

    # Sort clusters by size in descending order
    sorted_clusters = sorted(cluster_info.items(), key=lambda x: x[1], reverse=True)

    # Save faces from each cluster, skipping small clusters
    print("Saving faces by cluster to output folder...")
    for id, (label, size) in enumerate(sorted_clusters):
        cluster_dir = os.path.join(output_folder_path, f"cluster_{id}({size})")
        os.makedirs(cluster_dir, exist_ok=True)

        indices = [i for i, lbl in enumerate(labels) if lbl == label]
        print(f"Cluster ID {label}: {size} faces")

        for count, index in enumerate(indices):
            img, shape, original_path = images[index]
            file_path = os.path.join(cluster_dir, os.path.basename(original_path))
            imageio.imwrite(file_path, img)  # 使用imageio保存原始图像

if __name__ == "__main__":
    # sys.argv 是一个列表，包含了命令行参数
    # main 函数调用时传入 sys.argv，这样 main 就可以接收所有命令行参数
    directory = sys.argv[1] if len(sys.argv) > 1 else ''
    if not directory:
        print("请输入目录路径")
        exit(1)
    if not os.path.isdir(directory):
        print("请输入有效的目录路径")
        exit(1)
    main(directory)