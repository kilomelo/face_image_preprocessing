import os
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

def count_extensions(directory):
    """
    统计给定目录（包括子目录）中所有文件的扩展名，并动态显示计数过程。
    """
    extension_count = defaultdict(int)
    total_files = 0

    # 初始化动态计数器，不预先设定总数量
    pbar = tqdm(desc="正在计数文件")

    # 遍历目录中的文件
    for root, _, files in os.walk(directory):
        for file in files:
            ext = Path(file).suffix.lower()  # 获取文件扩展名并转为小写
            extension_count[ext] += 1
            total_files += 1
            pbar.update(1)  # 每处理一个文件更新计数器

    pbar.close()  # 所有文件处理完毕后关闭计数器
    return extension_count, total_files

def save_results(directory, extension_count, total_files):
    """
    将扩展名统计结果保存到指定目录下的文本文件。
    """
    output_file = Path(directory) / "extension_summary.txt"
    with open(output_file, 'w') as file:
        file.write(f"总文件数: {total_files}\n")
        file.write(f"唯一扩展名数量: {len(extension_count)}\n")
        for ext, count in sorted(extension_count.items()):
            file.write(f"{ext}: {count}\n")

def main(directory):
    """
    主函数，负责调度整个流程。
    """
    tqdm.write(f"开始扫描目录: {directory}")

    # 统计算扩展名并实时更新计数
    extension_count, total_files = count_extensions(directory)

    # 保存结果
    save_results(directory, extension_count, total_files)
    tqdm.write(f"结果已保存至 {directory}/extension_summary.txt")

    # 输出最终统计摘要
    tqdm.write(f"处理的总文件数: {total_files}")
    tqdm.write(f"发现的唯一扩展名数量: {len(extension_count)}")
    for ext, count in sorted(extension_count.items()):
        tqdm.write(f"扩展名 '{ext}': {count} 个文件")

directory = "/Volumes/192.168.1.173/pic/热巴_6653[53_GB]"
main(directory)