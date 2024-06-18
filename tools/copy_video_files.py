import sys
import os
from pathlib import Path
import shutil

def copy_files_with_extensions(source_dir, target_subdir, extensions):
    # 创建目标目录的完整路径
    target_dir = os.path.join(source_dir, target_subdir)
    
    # 如果目标目录不存在，则创建它
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    cnt = 0
    # 遍历源目录
    for root, dirs, files in os.walk(source_dir):
        # 忽略目标子目录
        dirs[:] = [d for d in dirs if os.path.join(root, d) != target_dir]
        
        for file in files:
            # 检查文件扩展名是否在允许的扩展名列表中
            if any(file.lower().endswith(ext) for ext in extensions):
                source_file_path = os.path.join(root, file)
                target_file_path = os.path.join(target_dir, file)
                
                # 确保源文件和目标文件不是同一个文件
                if source_file_path != target_file_path:
                    # 复制文件
                    shutil.copy2(source_file_path, target_file_path)
                    cnt += 1
                    print(f"Copied '{source_file_path}' to '{target_file_path}'")
    print(f"Copied {cnt} files")


target_subdirectory = 'videos'
allowed_extensions = ['.mp4', '.mov']  # 允许复制的文件扩展名
copy_files_with_extensions('/Volumes/Data512/pic/_柳岩_2928[14_GB]', target_subdirectory, allowed_extensions)

# if __name__ == "__main__":
#     # sys.argv 是一个列表，包含了命令行参数
#     # main 函数调用时传入 sys.argv，这样 main 就可以接收所有命令行参数
#     directory = sys.argv[1] if len(sys.argv) > 1 else ''
#     if not directory:
#         print("请输入目录路径")
#         exit(1)
#     if not os.path.isdir(directory):
#         print("请输入有效的目录路径")
#         exit(1)
#     target_subdirectory = 'videos'
#     allowed_extensions = ['.mp4', '.mov']  # 允许复制的文件扩展名
#     copy_files_with_extensions(directory, target_subdirectory, allowed_extensions)
