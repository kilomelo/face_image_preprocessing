import os
import shutil
from pathlib import Path
from PIL import Image, ExifTags
from tqdm import tqdm
import errno
import stat

def handle_remove_readonly(func, path, exc):
    """处理无法删除的文件或目录，尝试修改权限后重试。"""
    exc_value = exc[1]
    if exc_value.errno == errno.ENOENT:
        pass  # 文件不存在，忽略
    elif exc_value.errno == errno.EACCES:
        os.chmod(path, stat.S_IWUSR)  # 修改文件权限
        func(path)  # 再次尝试删除操作
    else:
        raise  # 其他错误，抛出异常

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

def human_readable_size(size):
    """将字节转换为更易读的格式。"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"
    else:
        return f"{size / (1024 ** 3):.2f} GB"

def rotate_image_according_to_exif(image):
    """根据图片的EXIF信息调整图片方向。"""
    try:
        exif = image._getexif()
        if exif is not None:
            # 获取所有EXIF标签
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
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
    return image

def resize(directory, thumbnail_size=256, grayscale=True):
    """调整目录中所有图像的大小，保持宽高比不变，并转换为灰度（可选），使用基25编码重命名。"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    successful_files = set()
    failed_counter = 0

    target_dir = Path(directory)
    thumbnail_dir = target_dir / "thumbnail"
    mapping_file_path = target_dir / "mapping.txt"

    if not target_dir.is_dir():
        tqdm.write(f"目录不存在: {directory}")
        return

    if thumbnail_dir.exists():
        tqdm.write(f"删除已存在的缩略图目录: {thumbnail_dir}")
        shutil.rmtree(thumbnail_dir, onerror=handle_remove_readonly)
    thumbnail_dir.mkdir(parents=True, exist_ok=True)

    total_size = 0
    image_paths = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for name in files:
            if not name.startswith('.') and any(name.lower().endswith(ext) for ext in image_extensions):
                path = Path(root) / name
                image_paths.append(path)

    progress = tqdm(image_paths, desc="正在扫描文件夹")
    images = []
    if len(image_paths) == 0:
        tqdm.write("未找到任何图片文件。")
        return
    for path in progress:
        file_size = path.stat().st_size
        total_size += file_size
        images.append(path)
        progress.set_description(f"已收集 {len(images)} 张图片, 总大小: {human_readable_size(total_size)}")

    tqdm.write(f"共找到 {len(images)} 张图片, 总大小: {human_readable_size(total_size)}")

    pbar = tqdm(images, desc="处理图片中")
    mapping_lines = []
    for index, source_path in enumerate(pbar):
        new_name = decimal_to_custom_base(index + 1)  # 基于0的索引
        target_path = thumbnail_dir / f"{new_name}.jpg"
        try:
            img = Image.open(source_path)
            img = rotate_image_according_to_exif(img)
            if grayscale:
                img = img.convert('L')
            # 保持宽高比缩放
            img.thumbnail((thumbnail_size, thumbnail_size), Image.LANCZOS)
            # 创建一个白色背景的新图片
            final_image = Image.new('RGB' if not grayscale else 'L', (thumbnail_size, thumbnail_size), 'white')
            # 计算居中的起始坐标
            x = (final_image.width - img.width) // 2
            y = (final_image.height - img.height) // 2
            # 将img贴在final_image的计算位置上
            final_image.paste(img, (x, y))
            final_image.save(target_path, format='JPEG', quality=85)
            successful_files.add(new_name + '.jpg')
            mapping_lines.append(f"{source_path}*{new_name}\n")

        except Exception as e:
            pbar.write(f"处理文件错误 {source_path}: {e}")
            failed_counter += 1

    with open(mapping_file_path, 'w') as file:
        file.writelines(mapping_lines)

    thumbnail_size = sum(p.stat().st_size for p in thumbnail_dir.iterdir())
    tqdm.write(f"处理完成。成功操作: {len(successful_files)}, 失败操作: {failed_counter}")
    percentage = (thumbnail_size / total_size) * 100
    tqdm.write(f"缩略图总大小: {human_readable_size(thumbnail_size)}, 与原图比例: {percentage:.2f}%")

# target_directory = "/Volumes/192.168.1.173-1/pic/陈都灵_503[167_MB]"
# target_directory = "/Volumes/192.168.1.173-1/pic/鞠婧祎_4999[5_GB]"
target_directory = "/Users/chenweichu/dev/data/test_副本"

tqdm.write("开始处理...")
resize(target_directory, 512)