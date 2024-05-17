import os
import cv2

def detect_faces(image_path, face_cascade):
    # 读取图像
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("图像未找到或路径错误")

    # 转换为灰度图像
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 进行人脸检测
    faces = face_cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=4, minSize=(10, 10))

    # 输出检测到的人脸数量
    print(f"检测到 {len(faces)} 个人脸")

    # 在检测到的人脸周围画矩形框并输出位置和大小
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
        print(f"人脸位置和大小：x={x}, y={y}, w={w}, h={h}")

    # 显示图像
    cv2.imshow('Face Detected', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def detect_faces_in_directory(directory_path):
    # 指定Haar级联文件路径
    cascade_path = '/Users/chenweichu/dev/miniconda3/envs/face-img-mac/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    results = []

    # 遍历目录中的文件
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):  # 确保是图像文件
            file_path = os.path.join(directory_path, filename)
            faces = detect_faces(file_path, face_cascade)
            if faces is not None:
                results.append({'filename': filename, 'faces': faces})

    cv2.destroyAllWindows()
    return results
# 调用函数，需要提供一个包含人脸的图像路径
# detect_faces_in_directory('/Volumes/192.168.1.173-1/pic/陈都灵_503[167_MB]/thumbnail/7.jpg')
detect_faces_in_directory('/Users/chenweichu/dev/data/test_副本/thumbnail')
