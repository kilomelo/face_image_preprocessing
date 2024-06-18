# 迭代编号：2
import sys
from PIL import Image
import numpy as np
import cv2
import os
import copy
from pathlib import Path
from imagehash import phash
from itertools import combinations
from typing import List, Set, Tuple
from termcolor import colored
import datetime
from tqdm import tqdm

class ImageDescriptor:
    def __init__(self, unique_images: Set[Path], similar_groups: List[List[Path]]):
        self.unique_images = unique_images
        self.similar_groups = similar_groups
        self.group_removed_by_next_detector = []
        self.new_unique_images_by_next_detector = []

    def serialize(self, filepath: str):
        """将描述信息保存为文本文件"""
        tqdm.write(colored(f"Saving description to [{filepath}]", "white"))
        with open(filepath, 'w') as file:
            file.write("Unique Images:\n")
            for image in self.unique_images:
                file.write(f"{image.name}\n")
            file.write("\nSimilar Groups:\n")
            for group, is_removed in zip(self.similar_groups, self.group_removed_by_next_detector):
                group_header = "Group:removed\n" if is_removed else "Group:\n"  # 修改：追踪是否删除 迭代编号：2
                file.write(group_header)
                for image in group:
                    file.write(f"{image.name}\n")
                file.write("\n")
            file.write("New unique Images by next detector:\n")
            for image in self.new_unique_images_by_next_detector:
                file.write(f"{image.name}\n")

class HashDetector:
    def __init__(self, precision: int):
        self.precision = precision

    def detect(self, images: List[Path], display_progressbar = False) -> ImageDescriptor:
        # tqdm.write(colored(f"Detecting duplicates using perceptual hash, precision: {self.precision}\nimages cnt: {len(images)}", "white"))
        hash_dict = {}
        if display_progressbar:
            for image_path in tqdm(images, desc="Hashing images"):
                try:
                    with Image.open(image_path) as img:
                        img_hash = phash(img.convert("L").resize((self.precision, self.precision)))
                        if img_hash in hash_dict:
                            hash_dict[img_hash].append(image_path)
                        else:
                            hash_dict[img_hash] = [image_path]
                except Exception as e:
                    tqdm.write(colored(f"Error processing {image_path}: {e}", "red"))
        else:
            for image_path in images:
                try:
                    with Image.open(image_path) as img:
                        img_hash = phash(img.convert("L").resize((self.precision, self.precision)))
                        if img_hash in hash_dict:
                            hash_dict[img_hash].append(image_path)
                        else:
                            hash_dict[img_hash] = [image_path]
                except Exception as e:
                    tqdm.write(colored(f"Error processing {image_path}: {e}", "red"))
                    
        # tqdm.write(colored(f"Found {len(hash_dict)} unique hashes", "white"))
        unique_images = set()
        similar_groups = []
        for paths in hash_dict.values():
            if len(paths) == 1:
                unique_images.add(paths[0])
            else:
                similar_groups.append(paths)
                
        # tqdm.write(colored(f"Found {len(unique_images)} unique images, {len(similar_groups)} similar groups", "white"))
        return ImageDescriptor(unique_images, similar_groups)

class ORBDetector:
    def __init__(self, nfeatures: int, threshold: float):
        self.nfeatures = nfeatures
        self.threshold = threshold

    def detect(self, images: List[Path], display_progressbar = False) -> ImageDescriptor:
        # tqdm.write(colored(f"Detecting duplicates using ORB, nfeatures: {self.nfeatures}, threshold: {self.threshold}, images cnt: {len(images)}", "white"))
        keypoints_dict = {img: self._extract_features(img) for img in images}
        similar_groups = []
        unique_images = set(images)
        combines = combinations(images, 2)
        for img1, img2 in combines:
            kp1, des1 = keypoints_dict[img1]
            kp2, des2 = keypoints_dict[img2]
            if des1 is not None and des2 is not None:
                if self._match_features(des1, des2) > self.nfeatures * self.threshold:
                    similar_groups.append([img1, img2])
                    unique_images.discard(img1)
                    unique_images.discard(img2)

        return ImageDescriptor(unique_images, similar_groups)

    def _extract_features(self, image_path: Path):
        orb = cv2.ORB_create(self.nfeatures)
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        return orb.detectAndCompute(img, None)

    def _match_features(self, des1, des2):
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        return len(matches)

class ImageDeduplicator:
    def __init__(self, directory: str):
        if not os.path.exists(directory) or not os.path.isdir(directory):
            tqdm.write(colored(f"Directory {directory} not valid", "red"))
            self.directory = None
            return
        thumbnail = Path(f"{directory}/thumbnail")
        if not os.path.exists(thumbnail) or not os.path.isdir(thumbnail):
            tqdm.write(colored(f"Directory {thumbnail} not valid, create thumbnails first", "red"))
            self.directory = None
            return
        self.directory = directory
        self.detectors = [
            # HashDetector(8),
            HashDetector(16),
            # ORBDetector(500, 0.5),
            # ORBDetector(500, 0.7)
        ]

    def deduplicate(self):
        if self.directory is None:
            tqdm.write(colored("Directory not valid", "red"))
            return
        tqdm.write(colored(f"Start deduplicating images in {self.directory}, collect thumbnail images.", "green"))
        thumbnails = [file for file in Path(f"{self.directory}/thumbnail").glob('*') if not file.name.startswith('.') and file.suffix.lower() in [".jpg", ".png"]]
        tqdm.write(colored(f"Collected {len(thumbnails)} thumbnail images.", "green"))
        descriptor = ImageDescriptor(set(), [thumbnails])
        previous_descriptor = None
        prv_timestamp = None
        prv_hash_list = []

        for idx, detector in enumerate(self.detectors):
            # tqdm.write(colored(f"Process with {type(detector).__name__}[{id(detector)}], unique images: {len(descriptor.unique_images)} similar_groups count: {len(descriptor.similar_groups)}", "yellow"))
            new_descriptor = ImageDescriptor(descriptor.unique_images, [])
            new_unique_images = set()
            if idx > 0:
                for group_of_img in tqdm(descriptor.similar_groups):
                    result = detector.detect(group_of_img)
                    new_unique_images.update(result.unique_images - new_descriptor.unique_images)
                    new_descriptor.unique_images.update(result.unique_images)
                    new_descriptor.similar_groups.extend(result.similar_groups)
            else:
                for group_of_img in descriptor.similar_groups:
                    result = detector.detect(group_of_img, True)
                    new_unique_images.update(result.unique_images - new_descriptor.unique_images)
                    new_descriptor.unique_images.update(result.unique_images)
                    new_descriptor.similar_groups.extend(result.similar_groups)
            tqdm.write(colored(f"Processed with {type(detector).__name__}[{id(detector)}], unique images: {len(new_descriptor.unique_images)} similar_groups count: {len(new_descriptor.similar_groups)}", "yellow"))
            hash_list = [hash(f"{group[0]}{group[1]}{len(group)}") for group in new_descriptor.similar_groups]
            if previous_descriptor:
                tqdm.write(f"prev descriptor unique images: {len(previous_descriptor.unique_images)}")
                previous_descriptor.new_unique_images_by_next_detector = list(new_unique_images)
                for group_idx, prev_hash in enumerate(prv_hash_list):
                    if prev_hash not in hash_list:
                        tqdm.write(colored(f"Group {group_idx} is removed by {type(detector).__name__}", "blue"))
                        previous_descriptor.group_removed_by_next_detector.append(True)
                    else:
                        previous_descriptor.group_removed_by_next_detector.append(False)

                # 使用上一个detector的名字来命名文件
                filepath = f"{self.directory}/descriptor_{idx-1}_{type(self.detectors[idx - 1]).__name__}_{prv_timestamp}.txt"
                previous_descriptor.serialize(filepath)

            # 更新previous变量
            previous_descriptor = copy.deepcopy(new_descriptor)
            prv_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            prv_hash_list = hash_list
            descriptor = new_descriptor

        # 序列化最后一个descriptor
        if previous_descriptor:
            for idx in range(len(previous_descriptor.similar_groups)):
                previous_descriptor.group_removed_by_next_detector.append(False)
            # filepath = f"{self.directory}/descriptor_{len(self.detectors)-1}_{type(self.detectors[-1]).__name__}_{prv_timestamp}.txt"
            # 集成到工具链，生成固定文件名
            filepath = f"{self.directory}/descriptor_final.txt"
            previous_descriptor.serialize(filepath)
        
        return descriptor

def main(directory):
    deduplicator = ImageDeduplicator(directory)

    final_descriptor = deduplicator.deduplicate()
    if final_descriptor is None:
        tqdm.write(colored("Deduplication failed", "red"))
    else:
        tqdm.write(colored(f"Final unique images count: {len(final_descriptor.unique_images)}", "white"))

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