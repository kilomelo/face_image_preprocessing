import os
import shutil
from pathlib import Path

def get_dir_stats(path):
    """
    递归函数，用于计算给定目录及其所有子目录中的文件数量和总大小。
    
    参数:
    - path: 当前正在处理的目录的Path对象。
    
    返回:
    - 一个元组，包含两个元素：
    - 文件总数（包括子目录中的文件）
    - 总大小（所有文件的大小之和，以字节为单位）
    """
    file_count = 0  # 初始化文件计数器
    total_size = 0  # 初始化总大小计数器
    for item in path.iterdir():  # 遍历当前目录下的所有项
        if item.is_file():  # 如果是文件
            file_count += 1  # 增加文件计数
            total_size += item.stat().st_size  # 累加文件大小
        elif item.is_dir():  # 如果是目录
            # 对子目录递归调用此函数，并累加返回的文件计数和大小
            sub_count, sub_size = get_dir_stats(item)
            file_count += sub_count
            total_size += sub_size
    return file_count, total_size

def rename_subdirectories(directory):
    """
    遍历指定目录，对每个子目录进行重命名。
    新的名称格式为：原名_文件数_总大小（单位自适应，无空格）。
    
    参数:
    - directory: 要处理的根目录的路径。
    """
    directory = Path(directory)  # 确保目录路径为Path对象
    
    # 遍历根目录下的所有子项
    for subdir in directory.iterdir():
        if subdir.is_dir():  # 确保处理的是目录
            # 调用get_dir_stats获取当前子目录的文件统计信息
            file_count, total_size = get_dir_stats(subdir)
            
            # 将总大小转换为带单位的字符串，并替换空格为下划线以适合作为文件名
            total_size_str = convert_size(total_size).replace(" ", "_")
            
            # 构建新的目录名
            new_name = f"{subdir.name}_{file_count}[{total_size_str}]"
            new_path = directory / new_name  # 创建新路径
            
            # 使用shutil.move重命名目录（实质上是移动到新位置）
            shutil.move(str(subdir), str(new_path))
            print(f"Renamed '{subdir}' to '{new_name}'")  # 输出重命名信息

def convert_size(size_bytes):
    """
    将字节大小转换为人类可读的格式（B, KB, MB, GB, TB, PB），确保结果无小数点，且在转换后的值至少为10时进入下一个单位。
    
    参数:
    - size_bytes: 要转换的原始大小（字节）。
    
    返回:
    - 字符串，表示转换后的大小及单位，无小数部分。
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0  # 开始时使用字节(B)单位
    
    while unit_index < len(units) - 1:
        next_size = size_bytes / 1024  # 计算转换到下一个单位的值
        if next_size >= 5:  # 确保转换后的值至少为5
            size_bytes = round(next_size)
            unit_index += 1
        else:
            break  # 如果不足10，则停留在当前单位，结束循环
    
    return f"{size_bytes} {units[unit_index]}"  # 返回四舍五入后的整数大小和单位

# def test_convert_size():
#     test_cases = [
#         (0, "0 B"),         # 特殊情况：0字节
#         (1, "1 B"),         # 最小非零值
#         (999, "999 B"),     # 低于1KB阈值
#         (1000, "1000 B"),    # 刚好1KB
#         (1023, "1023 B"),    # 低于10KB阈值
#         (10240, "10 KB"),  # 刚好10KB
#         (11234, "11 KB"),  # 接近但不足100KB
#         (1048575, "1024 KB"), # 接近但不足1MB
#         (1048576, "1024 KB"),  # 刚好1MB
#         (1500000, "1465 KB"),  # 超过1MB但不足10MB
#         (15728640, "15 MB"), # 刚好15MB
#     ]
    
#     for bytes_val, expected_output in test_cases:
#         assert convert_size(bytes_val) == expected_output, f"For {bytes_val}B, expected '{expected_output}', got '{convert_size(bytes_val)}'"
#         print(f"Test passed for {bytes_val}B -> {convert_size(bytes_val)}")
        
#     print("All tests passed.")

def rename_subdirs_with_underscore(root_dir):
    """
    遍历指定目录，重命名所有子目录，删除其名称中第一个下划线及后面的所有字符。
    
    :param root_dir: 要遍历并重命名子目录的根目录路径
    """
    root_path = Path(root_dir)
    
    # 遍历根目录下的所有子项
    for item in root_path.iterdir():
        if item.is_dir():  # 只处理目录
            # 找到第一个下划线的位置
            underscore_index = item.name.find('_')
            if underscore_index != -1:  # 如果找到下划线
                # 删除下划线及其后面的所有字符，并重命名
                new_name = item.name[:underscore_index]
                new_path = root_path / new_name
                
                # 确保新名称不存在，以避免覆盖现有目录
                if not new_path.exists():
                    item.rename(new_path)
                    print(f"Renamed '{item}' to '{new_path}'")
                else:
                    print(f"Skipped renaming '{item}' because '{new_path}' already exists.")
            else:  # 如果没有下划线，跳过
                print(f"'{item}' has no underscore, skipping.")
        else:  # 如果是文件，直接跳过
            continue

# 调用测试函数
# test_convert_size()

# 使用示例
directory_to_rename = 'F:\pic\鞠婧祎_9994[5_GB]'
rename_subdirectories(directory_to_rename)  # 调用函数，传入要处理的目录路径
# rename_subdirs_with_underscore(directory_to_rename)
# print(convert_size(16972898619))