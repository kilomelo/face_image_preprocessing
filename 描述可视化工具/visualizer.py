import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QScrollArea, QLabel, QGridLayout, QListWidget, QListWidgetItem, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QFileSystemWatcher, QTimer, QUrl, pyqtSignal
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QFont, QDesktopServices
from pathlib import Path
from termcolor import colored
from collections import deque

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ImageDescriptor:
    # 初始化图像描述器
    def __init__(self, unique_images, similar_groups, similar_groups_flg):
        self.unique_images = set(unique_images)
        self.similar_groups = similar_groups
        self.similar_groups_flg = similar_groups_flg
        self.img_num = [len(unique_images)] + [len(sub_array) for sub_array in similar_groups]

    # 从文件反序列化图像描述器
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
                print(colored(f"Group flg: [{current_group_flg}]", 'yellow'))
                continue
            elif line.strip():
                image_path = line.strip()
                if parsing_mode == 'unique':
                    unique_images.append(image_path)
                elif parsing_mode == 'groups':
                    current_group.append(image_path)

        if current_group:
            similar_groups.append(current_group)
        
        return cls(unique_images, similar_groups, similar_groups_flg)
    
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

class ClickableLabel(QLabel):
    # 定义一个点击信号
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(ClickableLabel, self).__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignCenter)  # 根据需要设置对齐方式

    def mousePressEvent(self, event):
        # 当鼠标被按下时，发出clicked信号
        self.clicked.emit()

class DescripterViewer(QMainWindow):
    def __init__(self, default_directory=None):
        super().__init__()
        self.title = '查看去重结果'
        self.left = 128
        self.top = 128
        self.width = 900
        self.height = 600
        self.view_refresh_throttling = 200
        self.current_directory = ''
        self.current_selected_file = None
        self.descriptor = None
        self.loaded_descripter_path = {}
        # 待载入队列
        self.load_queue = deque()
        self.reset_runtime_status()

        # 图片显示宽度
        self.img_width = 128
        # 图片显示高度
        self.img_height = 128
        # 图片排列水平间距
        self.img_horizontal_spacing = 2
        # grid竖直间距
        self.widgets_vertical_spacing = 5
        # 图片名字高度
        self.label_height = 24
        # 组标题高度
        self.title_height = 50
        # 每行图片数
        self.num_columns = 1
        
        # 刷新图像视图的定时器
        self.view_refresh_timer = QTimer(self)
        self.view_refresh_timer.timeout.connect(self.img_viewport_change_delay_action)  # 连接超时信号到处理函数
        # 非阻塞加载图片的定时器
        self.load_timer = QTimer(self)
        self.load_timer.timeout.connect(self.handle_load_timer)  # 连接超时信号到处理函数
        self.load_timer.setSingleShot(True)  # 设置为单次触发
        self.load_timer.start(100)

        # self.status_bar_timer = QTimer(self)
        # self.status_bar_timer.timeout.connect(lambda: self.status_label.setText(
            # f"当前已载入图片数: {self.loaded_img_cnt} 每行图片数: {self.num_columns} 滚动条位置: {self.scroll_area.verticalScrollBar().value()}"))
        # self.status_bar_timer.start(10)

        # 监听文件夹的变化
        self.watcher = QFileSystemWatcher()
        self.init_ui()

        if default_directory and os.path.exists(default_directory) and os.path.isdir(default_directory):
            self.load_dir(default_directory)

    def init_ui(self):
        # 初始化用户界面
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        widget = QWidget()
        self.setCentralWidget(widget)
        v_layout = QVBoxLayout()

        h_layout = QHBoxLayout()
        self.entry_directory = QLineEdit()
        self.entry_directory.setPlaceholderText("请输入或选择一个目录...")
        self.btn_open = QPushButton('打开目录')
        self.btn_open.clicked.connect(self.open_directory)
        h_layout.addWidget(self.entry_directory)
        h_layout.addWidget(self.btn_open)

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.display_file_content)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_container = QWidget()
        self.scroll_area.setWidget(self.image_container)

        self.image_layout = QVBoxLayout()
        self.image_layout.setSpacing(self.widgets_vertical_spacing)
        self.image_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.image_container.setLayout(self.image_layout)

        self.scroll_area.verticalScrollBar().valueChanged.connect(self.scrollbar_value_changed)
        self.scroll_area.horizontalScrollBar().valueChanged.connect(self.scrollbar_value_changed)

        splitter = QtWidgets.QSplitter(Qt.Horizontal)
        splitter.addWidget(self.file_list)
        splitter.addWidget(self.scroll_area)
        splitter.setSizes([150, self.width - 150])
        splitter.splitterMoved.connect(self.on_image_container_size_changed)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(splitter)

        # 更新状态栏布局
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.status_label = QLabel("未打开文件夹")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.btn_status_1 = QPushButton('上一组')
        self.btn_status_2 = QPushButton('下一组')
        self.btn_status_1.clicked.connect(self.show_prev_group)
        self.btn_status_2.clicked.connect(self.show_next_group)
        status_layout.addWidget(self.status_label, stretch=1)
        status_layout.addWidget(self.btn_status_1)
        status_layout.addWidget(self.btn_status_2)

        # 将新的状态栏布局添加到主布局中
        status_container = QWidget()
        status_container.setLayout(status_layout)
        status_container.setFixedHeight(28)  # 可以根据需要调整高度
        v_layout.addWidget(status_container)

        widget.setLayout(v_layout)

    def open_directory(self):
        # 打开目录并更新文件列表
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        self.load_dir(directory)

    def load_dir(self, directory):
        if directory and os.path.exists(directory) and os.path.isdir(directory):
            self.status_label.setText("未打开文件夹")
            self.entry_directory.setText(directory)
            if self.current_directory:
                self.watcher.removePath(self.current_directory)
            self.current_directory = directory
            self.watcher.addPath(directory)
            self.watcher.directoryChanged.connect(self.directory_changed)
            self.populate_files_list(directory)
        else:
            logging.error(f"Invalid directory: {directory}")

    def populate_files_list(self, directory):
        logging.debug(f"Populating files list: {directory}")

        def human_readable_name(file_name):
            """将字节转换为更易读的格式。"""
            try:
                # 分割字符串，获取中间的部分（somestr）和时间部分
                parts = file_name.split("_")
                detector = parts[1]
                time_part = parts[2]
                # 从时间部分提取小时和分钟
                hour_minute = time_part[10:14]  # 索引10到13对应小时和分钟
                # 组合为目标格式
                return f"{hour_minute} {detector}"
            except Exception as e:
                logging.error(f"转换可读名字失败: {e}")
                return file_name
        # 填充文件列表
        self.file_list.clear()
        self.loaded_descripter_path = {}
        files = [f for f in os.listdir(directory) if f.endswith('.txt')]
        descriptor_files = [f for f in files if self.is_descriptor_file(os.path.join(directory, f))]
        current_select_found = False
        for file in descriptor_files:
            display_name = human_readable_name(file)
            self.loaded_descripter_path[display_name] = file
            item = QListWidgetItem(display_name)
            self.file_list.addItem(item)
            if display_name == self.current_selected_file:
                self.file_list.setCurrentItem(item)
                current_select_found = True
        if not current_select_found:
            self.current_selected_file = None
            self.descriptor = None
            self.display_file_content(None)

    def is_descriptor_file(self, filepath):
        # 检查是否为描述文件
        try:
            with open(filepath, 'r') as file:
                first_line = file.readline()
                return "Unique Images:" in first_line
        except Exception as e:
            logging.error(f"Error checking descriptor file: {e}")
            return False

    def display_file_content(self, item):
        logging.debug(f"Displaying file content: {item}")
        if item is None:
            self.clear_layout(self.image_layout)  # 清理布局
            placeholder = QLabel("当前未选择文件")
            self.image_layout.addWidget(placeholder)  # 显示提示信息
            self.reset_runtime_status()
            self.view_refresh_timer.stop()
            return
        # 显示文件内容和相关图像
        filepath = os.path.join(self.current_directory, self.loaded_descripter_path.get(item.text()))
        try:
            self.descriptor = ImageDescriptor.deserialize(filepath)
            self.current_selected_file = item.text()
            self.status_label.setText(f"唯一图片: {len(self.descriptor.unique_images)} | 相似组: {len(self.descriptor.similar_groups)}")
            self.construct_img_layout_structure()
        except Exception as e:
            self.status_label.setText(f"解析描述文件出错: {e}")
            logging.error(f"无法解析描述文件 {filepath}, 错误新消息：{e}")

    def img_viewport_width(self):
        # return (self.scroll_area.viewport().width() -
            # self.image_layout.contentsMargins().left() -
            # self.image_layout.contentsMargins().right())
        return self.scroll_area.viewport().width() - self.image_layout.contentsMargins().left()
    def img_display_vertical_pos(self, img_idx):
        """
        计算图像在显示区域中的垂直位置
        :param img_idx: 图像索引
        :return: 垂直位置
        """
        if self.descriptor is None:
            logging.error("No descriptor to calculate image display vertical position")
            return float('inf')
        # num_columns = max(1, self.img_viewport_width() // (self.img_width + self.img_horizontal_spacing))
        # logging.debug(colored(f"Number of columns: {num_columns}", "yellow"))
        v_pos = 0
        count = 0
        row_height = self.img_height + self.widgets_vertical_spacing * 2 + self.label_height
        for group_img_num in self.descriptor.img_num:
            v_pos += self.title_height + self.image_layout.spacing()
            if count + group_img_num > img_idx:
                return v_pos + ((img_idx - count) // self.num_columns) * row_height
            count += group_img_num
            v_pos += ((group_img_num - 1) // self.num_columns + 1) * row_height - self.widgets_vertical_spacing + self.image_layout.spacing()
            
        # 传入的img_idx超过当前描述文件记录的图片数量
        return float('inf')
    
    def reset_runtime_status(self):
        self.loaded_img_cnt = 0
        self.load_queue.clear()
        self.image_labels = {}
        self.group_scroll_vpos = []

    def construct_img_layout_structure(self):
        # 构建图像显示区域结构
        logging.debug("Updating image display")
        if self.descriptor is None:
            logging.error("No descriptor to update image display")
            return

        self.clear_layout(self.image_layout)
        self.reset_runtime_status()
        self.num_columns = max(1, self.img_viewport_width() // (self.img_width + self.img_horizontal_spacing))

        def display_image_group(title, images, start_image_idx):
            title_label = QLabel(title)
            title_label.setFixedHeight(self.title_height)
            title_label.setFont(QFont("Arial", 20, QFont.Bold))
            self.image_layout.addWidget(title_label)
            vertical_size = self.title_height + self.widgets_vertical_spacing

            grid_layout = QGridLayout()
            grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setHorizontalSpacing(self.img_horizontal_spacing)
            grid_layout.setVerticalSpacing(self.widgets_vertical_spacing)
            row = 0
            col = 0
            vertical_size += self.img_height + self.label_height + self.widgets_vertical_spacing * 2
            for idx, filename in enumerate(images):
                img_label = ClickableLabel()
                img_label.setFixedSize(self.img_width, self.img_height)
                img_label.setStyleSheet("background-color: gray")  # 灰色占位图
                txt_label = QLabel(f"[{start_image_idx + idx}] {filename.split('.')[0]}")
                txt_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
                txt_label.setFixedHeight(self.label_height)
                txt_label.setFixedWidth(self.img_width)
                grid_layout.addWidget(img_label, row, col)
                grid_layout.addWidget(txt_label, row + 1, col)
                self.image_labels[start_image_idx + idx] = img_label

                col += 1
                if col >= self.num_columns and idx != len(images) - 1:
                    row += 2  # 为文件名标签留出空间
                    vertical_size += self.img_height + self.label_height + self.widgets_vertical_spacing * 2
                    col = 0

            for column in range(col, self.num_columns):
                grid_layout.setColumnStretch(column, 0)
                
            widget = QWidget()
            widget.setLayout(grid_layout)
            self.image_layout.addWidget(widget)
            return start_image_idx + len(images), vertical_size

        self.group_scroll_vpos.append(0)
        vertical_pos = 0
        image_idx, vertical_pos = display_image_group("唯一图片", list(self.descriptor.unique_images), 0)
        self.group_scroll_vpos.append(vertical_pos)
        for group_idx, images in enumerate(self.descriptor.similar_groups):
            image_idx, vertical_size = display_image_group(f"重复图片组 {group_idx + 1} [{len(images)}]", images, image_idx)
            vertical_pos += vertical_size
            self.group_scroll_vpos.append(vertical_pos)

        logging.debug("图片标签准备完成")

        # self.view_refresh_timer.start(self.view_refresh_throttling)  # 启动定时器重新调整布局
        self.img_viewport_change_delay_action()

    def lazy_load_and_unload_imgs(self):
        """
        加载可见图片，卸载不可见图片
        """
        logging.debug("加载可见图片")

        if self.descriptor is None:
            logging.error("No descriptor to load visible images")
            return

        for img_idx, label in self.image_labels.items():
            pos = self.img_display_vertical_pos(img_idx)
            visible = pos + self.img_height > self.scroll_area.verticalScrollBar().value() \
                and pos < self.scroll_area.verticalScrollBar().value() + self.scroll_area.viewport().height()

            pixmap = label.pixmap()
            loaded = pixmap is not None and not pixmap.isNull()
            if visible and not loaded:
                # logging.debug(colored(f"{self.descriptor.file_by_idx(img_idx)} 进入加载队列", "blue"))
                if img_idx not in self.load_queue:
                    self.load_queue.append(img_idx)
            if not visible:
                if loaded:
                    # logging.debug(colored(f"{self.descriptor.file_by_idx(img_idx)} 已卸载", "yellow"))
                    label.setPixmap(QPixmap())
                    label.disconnect()
                    self.loaded_img_cnt -= 1
                else:
                    try:
                        self.load_queue.remove(img_idx)
                        # logging.debug(colored(f"{self.descriptor.file_by_idx(img_idx)} 已取消加载", "yellow"))
                    except ValueError:
                        pass
    
    def show_next_group(self):
        # 按钮1点击时执行的操作
        logging.debug("下一组")
        current_vertical_scroll_pos = self.scroll_area.verticalScrollBar().value()
        for vpos in self.group_scroll_vpos:
            if vpos > current_vertical_scroll_pos:
                self.scroll_area.verticalScrollBar().setValue(vpos)
                break

    def show_prev_group(self):
        # 按钮2点击时执行的操作
        logging.debug("上一组")
        current_vertical_scroll_pos = self.scroll_area.verticalScrollBar().value()
        for vpos in reversed(self.group_scroll_vpos):
            if vpos < current_vertical_scroll_pos:
                self.scroll_area.verticalScrollBar().setValue(vpos)
                break

    def open_original_image(self, thumbnail_name):
        mapping_file_path = os.path.join(self.current_directory, "mapping.txt")
        try:
            with open(mapping_file_path, 'r') as file:
                for line in file:
                    # 去除每行末尾的空白符，这包括'\n'
                    clean_line = line.strip()
                    if clean_line.endswith(thumbnail_name):
                        # 返回'*'分割后的第一个部分，假设存在，且防止空行造成的影响
                        original_file_path = clean_line.split('*')[0]
                        QDesktopServices.openUrl(QUrl.fromLocalFile(original_file_path))
        except Exception as e:
            logging.error(f"Failed to read mapping file: {e}")
            return

    def directory_changed(self, path):
        # 目录变更处理
        if path == self.current_directory:
            self.populate_files_list(path)

    def scrollbar_value_changed(self):
        self.view_refresh_timer.start(self.view_refresh_throttling)  # 启动定时器重新调整布局

    def resizeEvent(self, event):
        # todo 窗口宽度改变时，重新设置图片grid的布局。
        # logging.debug(colored(f"窗口宽度改变: {event.size().width()}", "red"))
        super().resizeEvent(event)
        self.on_image_container_size_changed(0, 0)
        
    def on_image_container_size_changed(self, pos, index):
        # logging.debug(colored(f"on_image_container_size_changed", "red"))
        # 判断每行显示图片数是否发生变化，如果发生了变化，就重新构建结构
        num_columns = max(1, self.img_viewport_width() // (self.img_width + self.img_horizontal_spacing))
        self.view_refresh_timer.start(self.view_refresh_throttling)  # 启动定时器重新调整布局

    def img_viewport_change_delay_action(self):
        # logging.debug(colored(f"img_viewport_change_delay_action", "green"))
        num_columns = max(1, self.img_viewport_width() // (self.img_width + self.img_horizontal_spacing))
        if num_columns != self.num_columns:
            self.construct_img_layout_structure()
        else:
            self.lazy_load_and_unload_imgs()  # 重新加载可见图片
        self.view_refresh_timer.stop()

        # self.num_columns = max(1, self.img_viewport_width() // (self.img_width + self.img_horizontal_spacing))
        # logging.debug(colored(f"Number of columns: {self.num_columns}", "yellow"))

    def handle_load_timer(self):
        if len(self.load_queue) == 0:
            # 一直没有任务时，以较低的频率检测
            QTimer.singleShot(100, self.load_timer.start)
            return
        
        img_idx = self.load_queue.popleft()
        img_label = self.image_labels.get(img_idx)
        if img_label is None:
            logging.error(f"No label found for image index {img_idx}")
        else:
            img_path = os.path.join(self.current_directory, 'thumbnail', self.descriptor.file_by_idx(img_idx))
            # logging.debug(colored(f"{self.descriptor.file_by_idx(img_idx)} 已加载", "green"))
            pixmap = QPixmap(img_path).scaled(self.img_width, self.img_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pos = self.img_display_vertical_pos(img_idx)
            visible = pos + self.img_height > self.scroll_area.verticalScrollBar().value() \
                    and pos < self.scroll_area.verticalScrollBar().value() + self.scroll_area.viewport().height()
            if not visible:
                logging.debug(colored(f"图片 {self.descriptor.file_by_idx(img_idx)} 未在可视区域内", "red"))
            else:
                img_label.setPixmap(pixmap)
                img_label.clicked.connect(lambda: self.open_original_image(self.descriptor.file_by_idx(img_idx).split('.')[0]))
                self.loaded_img_cnt += 1
        # 有任务时，以较高的频率检测
        QTimer.singleShot(1, self.load_timer.start)

    def clear_layout(self, layout):
        # 清空布局中的所有控件
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # ex = FileViewerApp("/Users/chenweichu/dev/data/test")
    ex = DescripterViewer("/Volumes/192.168.1.173/pic/陈都灵_503[167_MB]")
    # ex = DescripterViewer("/Volumes/192.168.1.173/pic/鞠婧祎_4999[5_GB]")

    ex.show()
    sys.exit(app.exec_())
