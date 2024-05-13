import logging

class ImageDescriptor:
    # 初始化图像描述器
    def __init__(self, unique_images, similar_groups, similar_groups_flg, new_unique_images):
        if len(similar_groups) != len(similar_groups_flg):
            raise ValueError(f"Similar groups and flags must have the same length, len of similar_groups: {len(similar_groups)}, len of similar_groups_flg: {len(similar_groups_flg)}")
        self.unique_images = set(unique_images)
        self.similar_groups = similar_groups
        self.similar_groups_flg = similar_groups_flg
        self.new_unique_images = new_unique_images
        self.img_num = [len(unique_images)] + [len(sub_array) for sub_array in similar_groups]

    @classmethod
    def deserialize(cls, filepath):
        with open(filepath, 'r') as file:
            content = file.read()
        lines = content.split('\n')
        if not lines[0].startswith("Unique Images:"):
            raise ValueError("Not a valid descriptor file")

        unique_images = []
        similar_groups = []
        similar_groups_flg = []
        new_unique_images = []
        current_group = []
        current_group_flg = ""
        parsing_mode = 'unique'

        for line in lines[1:]:
            if line.startswith("Similar Groups:"):
                parsing_mode = 'groups'
                continue
            elif line.startswith("Group:"):
                if current_group:
                    similar_groups.append(current_group)
                    similar_groups_flg.append(current_group_flg)
                current_group = []
                current_group_flg = line.split(':')[1].strip()
                # print(colored(f"Group flag: [{current_group_flg}]", 'yellow'))
                continue
            elif line.startswith("New unique Images by next detector:"):
                parsing_mode = 'new_unique'
                continue
            elif line.strip():
                image_path = line.strip()
                if parsing_mode == 'unique':
                    unique_images.append(image_path)
                elif parsing_mode == 'groups':
                    current_group.append(image_path)
                elif parsing_mode == 'new_unique':
                    new_unique_images.append(image_path)

        if current_group:
            similar_groups.append(current_group)
            similar_groups_flg.append(current_group_flg)

        return cls(unique_images, similar_groups, similar_groups_flg, new_unique_images)
    
    def file_by_idx(self, idx):
        # 根据索引获取文件
        if idx < len(self.unique_images):
            return list(self.unique_images)[idx]
        else:
            count = len(self.unique_images)
            for group in self.similar_groups:
                if idx < count + len(group):
                    return group[idx - count]
                else:
                    count += len(group)
            logging.error("Invalid index")
            return None