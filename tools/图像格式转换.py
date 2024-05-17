import os
import rawpy
import imageio
from PIL import Image
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm
import shutil
import errno
import stat

def convert_image(file_path, output_folder, overwrite=False):
    # 获取文件扩展名
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # 输出文件路径
    output_file = os.path.join(output_folder, os.path.basename(file_path).replace(ext, '.png'))
    # tqdm.write(f"Converting {file_path} to {output_file}")
    try:
        # 处理RAW格式
        if ext in ['.arw', '.cr2', '.orf']:  # 添加其他RAW格式的扩展名
            with rawpy.imread(file_path) as raw:
                rgb = raw.postprocess()  # 使用rawpy处理RAW数据
                # 检查文件是否存在，并根据overwrite参数决定是否保存
                if os.path.exists(output_file):
                    if not overwrite:
                        tqdm.write(f"File {output_file} already exists and won't be overwritten.")
                        return  # Exit the function if not allowed to overwrite
                # Save the image (either overwriting or to a new file)
                imageio.imsave(output_file, rgb)
                # print(f"Saved {output_file}")
        
        # 处理TIFF格式
        elif ext in ['.tif', '.tiff']:
            with Image.open(file_path) as img:
                if img.mode == 'CMYK':
                    # 将CMYK转换为RGB
                    img = img.convert('RGB')
                if os.path.exists(output_file):
                    if not overwrite:
                        # print(f"File {output_file} already exists. Set overwrite=True to overwrite it.")
                        return  # Exit the function if not allowed to overwrite
                    # else:
                        # print(f"Overwriting existing file {output_file}.")
                
                # Save the image (either overwriting or to a new file)
                img.save(output_file, 'PNG')  # 直接保存为PNG
                # print(f"Saved {output_file}")
        else:
            tqdm.write(f"Unsupported file format: {file_path}")
    except Exception as e:
        tqdm.write(f"Error processing {file_path}: {e}")

def handle_remove_readonly(func, path, exc):
    exc_value = exc[1]
    if exc_value.errno == errno.ENOENT:
        pass  # 文件不存在，忽略
    elif exc_value.errno == errno.EACCES:
        os.chmod(path, stat.S_IWUSR)  # 修改文件权限
        func(path)  # 再次尝试删除操作
    else:
        raise  # 其他错误，抛出异常

def main(directory):
    if not (directory and os.path.exists(directory) and os.path.isdir(directory)):
        tqdm.write(f"目录不存在或无效: {directory}")
        return
    
    converted_file_dir = Path(os.path.join(directory, "converted_uncommon_images"))
    if not converted_file_dir.exists():
        converted_file_dir.mkdir(parents=True, exist_ok=True)
    # if converted_file_dir.exists():
    #     tqdm.write(f"删除已存在的转换目标目录: {converted_file_dir}")
    #     shutil.rmtree(converted_file_dir, onerror=handle_remove_readonly)
    # converted_file_dir.mkdir(parents=True, exist_ok=True)

    tqdm.write(f"开始扫描目录: {directory}")
    common_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    uncommon_image_dic = {}
    # 遍历目录中的文件
    for root, dirs, files in os.walk(directory):
        if 'thumbnail' in dirs:
            dirs.remove('thumbnail')  # 忽略thumbnail目录
        for file in files:
            if file.startswith('.'): continue
            ext = Path(file).suffix.lower()  # 获取文件扩展名并转为小写
            path = os.path.join(root, file)
            if ext not in common_extensions:
                if ext not in uncommon_image_dic:
                    uncommon_image_dic[ext] = [path]
                else:
                    uncommon_image_dic[ext].append(path)
    for ext, files in uncommon_image_dic.items():
        # support_format = ['.arw', '.cr2', '.orf', '.tif', '.tiff']
        support_format = ['.arw','.cr2', '.orf', '.tiff']

        if ext not in support_format:
            continue
        tqdm.write(f"开始处理文件扩展名: {ext}, 数量: {len(files)}")
        for file in tqdm(files):
            # convert_image(os.path.join(directory, file), directory)
            # tqdm.write(f"开始处理文件: {file}")
            convert_image(file, converted_file_dir, True)

target_directory = "/Volumes/192.168.1.173/pic/热巴_6654[53_GB]"
main(target_directory)
