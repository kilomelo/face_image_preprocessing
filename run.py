import os
from tools.统计文件扩展名 import main as 统计文件扩展名
from tools.生成均匀缩放缩略图 import resize as 生成均匀缩放缩略图
from tools.图像格式转换 import main as 图像格式转换
from 图片去重 import main as 图片去重
from face_cropping_2 import main as 人脸剪切
from 人脸聚类_dlib_chinese_whispers import main as 人脸聚类
from tools.copy_video_files import copy_files_with_extensions
target_dir = '/Volumes/Data512/pic/杨幂_3597[21_GB]'
# target_dir = '/Volumes/Data512/pic/张靓颖 7.4G_1419[7_GB]'

def process(target_dir):
    if not target_dir:
        print("请输入目录路径")
        exit(1)
    if not os.path.isdir(target_dir):
        print("请输入有效的目录路径")
        exit(1)

    exts = 统计文件扩展名(target_dir)
    copy_files_with_extensions(target_dir, 'videos', ['.mp4', '.mov', '.ova', '.wmv', '.3gp', '.flv', '.avi', '.rmvb', '.mkv'])
    support_format = ['.arw', '.cr2', '.orf', '.tif', '.tiff']
    if any(i in exts for i in support_format):
        图像格式转换(target_dir)
    生成均匀缩放缩略图(target_dir)
    图片去重(target_dir)
    face_cnt = 人脸剪切(target_dir + '/descriptor_final.txt')
    # face_cnt=100000
    人脸聚类(target_dir, face_cnt, 0.4)

for item in os.listdir('/Volumes/Data512/pic/'):
    if item.startswith('.'): continue
    if item.startswith('_'): continue
    path = '/Volumes/Data512/pic/' + item
    if os.path.isdir(path):
        print(f'处理文件夹 \'{path}\'')
        process(path)