import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QScrollArea, QLabel, QGridLayout, QListWidget, QListWidgetItem, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QFileSystemWatcher, QTimer
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from pathlib import Path
from termcolor import colored

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ImageDescriptor:
    # 初始化图像描述器
    def __init__(self, unique_images, similar_groups):
        self.unique_images = set(unique_images)
        self.similar_groups = similar_groups
        self.img_num = [len(unique_images)] + [len(sub_array) for sub_array in similar_groups]

    # 从文件反序列化图像描述器
    @classmethod
    def deserialize(cls, filepath):
        with open(filepath, 'r') as file:
            content = file.read()
        lines = content.split('\n')
        if not lines[0].startswith("Unique Images:"):
            raise ValueError("Not a valid descriptor file")
        
        base_path = Path(filepath).parent
        unique_images = []
        similar_groups = []
        current_group = []
        parsing_mode = 'unique'
        
        for line in lines[1:]:
            if line.startswith("Similar Groups:"):
                parsing_mode = 'groups'
                continue
            elif line.startswith("Group:"):
                if current_group:
                    similar_groups.append(current_group)
                current_group = []
                continue
            elif line.strip():
                image_path = base_path / line.strip()
                if parsing_mode == 'unique':
                    unique_images.append(image_path)
                elif parsing_mode == 'groups':
                    current_group.append(image_path)

        if current_group:
            similar_groups.append(current_group)
        
        return cls(unique_images, similar_groups)
    
    def file_by_idx(self, idx):
        # 根据索引获取文件
        if idx < len(self.unique_images):
            return list(self.unique_images)[idx]
        else:
            cnt = len(self.unique_images)
            for group in self.similar_groups:
                if idx < cnt + len(group):
                    return group[idx - cnt]
                else:
                    cnt += len(group)
            logging.error("Invalid index")
            return None

class FileViewerApp(QMainWindow):
    def __init__(self, default_directory=None):
        super().__init__()
        self.title = '文件和图像浏览器'
        self.left = 100
        self.top = 100
        self.width = 1280
        self.height = 480
        self.view_refresh_throttling = 100
        self.current_directory = ''
        self.current_selected_file = None
        self.descriptor = None
        self.image_labels = {}  # 存储图片标签

        # 图片显示宽度
        self.img_width = 256
        # 图片显示高度
        self.img_height = 256
        # 图片排列水平间距
        self.img_horizontal_spacing = 2
        # grid竖直间距
        self.grid_vertical_spacing = 5
        # 图片名字高度
        self.label_height = 24
        # 组标题高度
        self.title_height = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.handle_img_viewport_change)  # 连接超时信号到处理函数
        # 监听文件夹的变化
        self.watcher = QFileSystemWatcher()
        self.initUI()

        if default_directory and os.path.exists(default_directory) and os.path.isdir(default_directory):
            self.load_dir(default_directory)

    def initUI(self):
        # 初始化用户界面
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        widget = QWidget()
        self.setCentralWidget(widget)
        vLayout = QVBoxLayout()

        hLayout = QHBoxLayout()
        self.entry_directory = QLineEdit()
        self.entry_directory.setPlaceholderText("请输入或选择一个目录...")
        self.btn_open = QPushButton('打开目录')
        self.btn_open.clicked.connect(self.open_directory)
        hLayout.addWidget(self.entry_directory)
        hLayout.addWidget(self.btn_open)

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.display_file_content)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_container = QWidget()
        self.scroll_area.setWidget(self.image_container)
        self.image_layout = QGridLayout()
        self.image_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.image_layout.setContentsMargins(0, 0, 0, 0)
        self.image_layout.setHorizontalSpacing(self.img_horizontal_spacing)
        self.image_layout.setVerticalSpacing(self.grid_vertical_spacing)
        self.image_container.setLayout(self.image_layout)

        self.scroll_area.verticalScrollBar().valueChanged.connect(self.scrollbar_value_changed)  # 滚动时加载可见图片
        self.scroll_area.horizontalScrollBar().valueChanged.connect(self.scrollbar_value_changed)  # 滚动时加载可见图片

        splitter = QtWidgets.QSplitter(Qt.Horizontal)
        splitter.addWidget(self.file_list)
        splitter.addWidget(self.scroll_area)
        splitter.setSizes([280, 1000])

        vLayout.addLayout(hLayout)
        vLayout.addWidget(splitter)
        widget.setLayout(vLayout)

    def open_directory(self):
        # 打开目录并更新文件列表
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        self.load_dir(directory)

    def load_dir(self, directory):
        if directory and os.path.exists(directory) and os.path.isdir(directory):
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
        # 填充文件列表
        self.file_list.clear()
        files = [f for f in os.listdir(directory) if f.endswith('.txt')]
        descriptor_files = [f for f in files if self.is_descriptor_file(os.path.join(directory, f))]
        current_select_found = False
        for file in descriptor_files:
            item = QListWidgetItem(file.split('.')[0])
            self.file_list.addItem(item)
            if file == self.current_selected_file:
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
        if item is None:
            self.clear_layout(self.image_layout)  # 清理布局
            placeholder = QLabel("当前未选择文件")
            self.image_layout.addWidget(placeholder)  # 显示提示信息
            return
        # 显示文件内容和相关图像
        filepath = os.path.join(self.current_directory, item.text(),) + '.txt'
        try:
            self.descriptor = ImageDescriptor.deserialize(filepath)
            self.current_selected_file = item.text()

            self.update_image_display()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法解析描述文件 {filepath}, 错误新消息：{e}")

    def img_display_vertical_pos(self, img_idx):
        """
        计算图像在显示区域中的垂直位置
        :param img_idx: 图像索引
        :return: 垂直位置
        """
        if self.descriptor is None:
            logging.error("No descriptor to calculate image display vertical position")
            return float('inf')
        num_columns = max(1, self.scroll_area.viewport().width() // (self.img_width + self.img_horizontal_spacing))
        logging.debug(colored(f"Number of columns: {num_columns}", "blue"))
        v_pos = 0
        cnt = 0
        row_height = self.img_height + self.grid_vertical_spacing * 2 + self.label_height
        for group_img_num in self.descriptor.img_num:
            v_pos += self.title_height + self.grid_vertical_spacing
            if cnt + group_img_num > img_idx:
                return v_pos + ((img_idx - cnt) // num_columns) * row_height
            cnt += group_img_num
            v_pos += ((group_img_num + 1) // num_columns) * row_height
            
        # 传入的img_idx超过当前描述文件记录的图片数量
        return float('inf')
    
    def update_image_display(self):
        # 更新图像显示区域

        if self.descriptor is None:
            logging.error("No descriptor to update image display")
            return

        logging.debug(f"Updating image display, unique images: {len(self.descriptor.unique_images)}, similar groups: {len(self.descriptor.similar_groups)}")
        self.clear_layout(self.image_layout)
        row, col = 0, 0
        num_columns = max(1, self.scroll_area.viewport().width() // (self.img_width + self.img_horizontal_spacing))
        logging.debug(colored(f"Number of columns: {num_columns}", "yellow"))
        logging.debug(f"Number of columns: {num_columns}")

        for idx, filename in enumerate(self.descriptor.unique_images):
            img_label = QLabel()
            img_label.setFixedSize(self.img_width, self.img_height)
            img_label.setStyleSheet("background-color: gray")  # 灰色占位图
            txt_label = QLabel(filename.stem)
            txt_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            txt_label.setFixedHeight(self.label_height)
            self.image_layout.addWidget(img_label, row, col)
            self.image_layout.addWidget(txt_label, row + 1, col)
            self.image_labels[idx] = img_label

            col += 1
            if col >= num_columns:
                row += 2  # 为文件名标签留出空间
                col = 0

        logging.debug("图片标签准备完成")
        self.timer.start(self.view_refresh_throttling)  # 启动定时器重新调整布局

    def loadVisibleImages(self):
        """
        加载可见图片，卸载不可见图片
        """
        logging.debug("加载可见图片")

        if self.descriptor is None:
            logging.error("No descriptor to load visible images")
            return
        for img_idx, label in self.image_labels.items():
            visible = self.img_display_vertical_pos(img_idx) + self.img_height > self.scroll_area.verticalScrollBar().value() and self.img_display_vertical_pos(img_idx) < self.scroll_area.verticalScrollBar().value() + self.scroll_area.viewport().height()
            pixmap = label.pixmap()
            loaded = pixmap is not None and not pixmap.isNull()
            file_path = os.path.join(self.current_directory, self.descriptor.file_by_idx(img_idx))
            if visible and not loaded:
                logging.debug(f"加载图片：{file_path}")
                pixmap = QPixmap(file_path).scaled(self.img_width, self.img_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
            if not visible and loaded:
                logging.debug(f"卸载图片：{file_path}")
                label.setPixmap(QPixmap())

    def directory_changed(self, path):
        # 目录变更处理
        if path == self.current_directory:
            self.populate_files_list(path)

    def scrollbar_value_changed(self):
        self.timer.start(self.view_refresh_throttling)  # 启动定时器重新调整布局

    def resizeEvent(self, event):
        # todo 窗口宽度改变时，重新设置图片grid的布局。
        super().resizeEvent(event)
        self.timer.start(self.view_refresh_throttling)  # 启动定时器重新调整布局

    def handle_img_viewport_change(self):
        self.loadVisibleImages()  # 重新加载可见图片
        self.timer.stop()

    def clear_layout(self, layout):
        # 清空布局中的所有控件
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileViewerApp("/Users/chenweichu/dev/data/test")
    # ex = FileViewerApp("/Volumes/192.168.1.173/pic/鞠婧祎_4999[5_GB]/thumbnail")
    ex.show()
    sys.exit(app.exec_())
