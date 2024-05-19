# 迭代编号：3
import os
import rawpy
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS
from pathlib import Path
from tqdm import tqdm

def convert_image(file_path, output_folder, output_size=4096, overwrite=False):
    """
    转换图像文件到指定格式。
    参数:
        file_path: str - 输入图像文件的路径。
        output_folder: str - 转换后的图像存储路径。
        overwrite: bool - 是否覆盖已存在的文件。
    返回:
        bool - 转换是否成功。
    """
    file_name = os.path.basename(file_path)
    _, ext = os.path.splitext(file_name)
    ext = ext.lower()

    output_file = os.path.join(output_folder, file_name[:-len(ext)] + '.jpg')
    try:
        if ext in ['.arw', '.cr2', '.orf', '.tif', '.tiff']:
            img = process_image(file_path, ext, output_size)
            if img is None:
                return False  # 图像处理失败
            if os.path.exists(output_file) and not overwrite:
                tqdm.write(f"File {output_file} already exists and won't be overwritten.")
                return False
            img.save(output_file, 'JPEG', quality=95)
            return True
        else:
            tqdm.write(f"Unsupported file format: {file_path}")
            return False
    except Exception as e:
        tqdm.write(f"Error processing {file_path}: {e}")
        raise
        return False

def rotate_image_according_to_exif(image):
    """根据图片的EXIF信息调整图片方向。"""
    try:
        exif = image._getexif()
        if exif is not None:
            # 获取所有EXIF标签
            for orientation in TAGS.keys():
                if TAGS[orientation] == 'Orientation':
                    break
            # 根据方向旋转图片
            if orientation in exif:
                if exif[orientation] == 3:
                    image = image.rotate(180, expand=True)
                    tqdm.write("旋转图片 180 度")
                elif exif[orientation] == 6:
                    image = image.rotate(270, expand=True)
                    tqdm.write("旋转图片 270 度")
                elif exif[orientation] == 8:
                    image = image.rotate(90, expand=True)
                    tqdm.write("旋转图片 90 度")
    except (AttributeError, KeyError, IndexError):
        # cases: image doesn't have getexif
        pass
    image.load()  # 确保数据加载到内存
    return image

def resize_image(img, max_size):
    # 如果图像的宽或高大于max_size，等比缩放到最大max_size
    if img.width > max_size or img.height > max_size:
        tqdm.write(f"Orig size: {img.width} * {img.height}, Resizing image...")
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    else:
        tqdm.write(f"Orig size: {img.width} * {img.height}, Skipping resize.")
    return img

def process_image(file_path, ext, max_size):
    """
    根据文件扩展名处理图像文件，返回处理后的PIL Image对象。
    参数:
        file_path: str - 图像文件路径。
        ext: str - 文件扩展名。
    返回:
        Image or None - 成功返回PIL Image对象，失败返回None。
    """
    try:
        if ext in ['.arw', '.cr2', '.orf']:
            with rawpy.imread(file_path) as raw:
                rgb = raw.postprocess(use_camera_wb=True)
                img = Image.fromarray(rgb)
                img = resize_image(img, max_size)
                return img
        elif ext in ['.tif', '.tiff']:
            with Image.open(file_path) as img:
                img = rotate_image_according_to_exif(img)
                tqdm.write(f"id of image: {id(img)}")
                img = resize_image(img, max_size)
                tqdm.write(f"id of image after resize function: {id(img)}")
                return img.convert('RGB') if img.mode == 'CMYK' else img
    except Exception as e:
        tqdm.write(f"Error in processing image {file_path}: {e}")
        return None

def main(directory):
    """
    主函数，遍历目录并转换图像。
    参数:
        directory: str - 目录路径。
    """
    if not (directory and os.path.exists(directory) and os.path.isdir(directory)):
        tqdm.write(f"目录不存在或无效: {directory}")
        return

    converted_file_dir = Path(os.path.join(directory, "converted_images"))
    if not converted_file_dir.exists():
        converted_file_dir.mkdir(parents=True, exist_ok=True)

    support_format = ['.arw', '.cr2', '.orf', '.tif', '.tiff']

    image_files = defaultdict(list)

    tqdm.write(f"开始扫描目录: {directory}")
    for root, dirs, files in os.walk(directory):
        if 'thumbnail' in dirs:
            dirs.remove('thumbnail')
        if 'converted_images' in dirs:
            dirs.remove('converted_images')
        for file in files:
            if file.startswith('.'):
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext in support_format:
                image_files[ext].append(os.path.join(root, file))
    tqdm.write(f"找到 {len(image_files)} 种图像格式, 数量:\n{', '.join([f'{ext}: {len(files)}' for ext, files in image_files.items()])}")

    # 新需求：分别处理每种图像格式，显示进度条 迭代编号：3
    success_count, fail_count = 0, 0  # 成功和失败的计数器 迭代编号：2
    for ext, files in image_files.items():
        tqdm.write(f"Processing {len(files)} files of type {ext}")
        progress = tqdm(total=len(files), desc=f"Converting {ext} images")
        for file in files:
            if convert_image(file, converted_file_dir, 4096, True):
                success_count+=1
            else:
                fail_count+=1
            progress.update(1)
        progress.close()
    tqdm.write(f"转换完成。成功: {success_count}, 失败: {fail_count}")  # 输出结果 迭代编号：2

# target_directory = "/Volumes/192.168.1.173/pic/热巴_6654[53_GB]"
# target_directory = "/Volumes/192.168.1.173/pic/test"
# main(target_directory)

# # 转换一组图片
# imgs = [
#     '/Volumes/192.168.1.173/pic/热巴_6654[53_GB]/879A1211.tif',
#     '/Volumes/192.168.1.173/pic/热巴_6654[53_GB]/879A1278.tif'
# ]
# ext = '.tif'
# converted_file_dir = '/Volumes/192.168.1.173/pic/热巴_6654[53_GB]/converted_images'
# progress = tqdm(total=len(imgs), desc=f"Converting {ext} images")
# for img in imgs:
#     # 如果output_size参数填写的数值大于图片的宽和高（如size为4096，图片是3000*2000），则报错
#     convert_image(img, converted_file_dir, 4096, True)
#     progress.update(1)
# progress.close()
# tqdm.write(f"转换完成。")