# 迭代编号：4
from pathlib import Path
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QScrollArea, QLabel, QGridLayout, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer, QFileSystemWatcher

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ImageDescriptor:
    def __init__(self, unique_images, similar_groups):
        self.unique_images = set(unique_images)
        self.similar_groups = similar_groups

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

class ImageGallery(QWidget):
    def __init__(self, default_directory=None):
        super().__init__()
        self.spacing = 10  # 每个图片间的间隙
        self.image_width = 128  # 图片宽度
        self.image_height = 128  # 图片高度
        self.label_height = 30 # 标签高度
        self.image_files = {}  # 存储文件路径
        self.image_labels = {}  # 存储图片标签
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.handleVisibilityChange)  # 连接超时信号到处理函数
        self.watcher = QFileSystemWatcher()

        self.initUI()  # 初始化用户界面

        if default_directory and os.path.exists(default_directory) and os.path.isdir(default_directory):
            self.directoryInput.setText(default_directory)
            self.prepareImages(default_directory)

    def initUI(self):
        # 主布局
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        # 顶部布局：目录输入与选择按钮
        topLayout = QHBoxLayout()
        mainLayout.addLayout(topLayout)
        self.directoryInput = QLineEdit()
        self.directoryInput.setPlaceholderText("请输入或选择一个目录...")
        topLayout.addWidget(self.directoryInput)
        self.openButton = QPushButton("打开")
        self.openButton.clicked.connect(self.openDirectory)
        topLayout.addWidget(self.openButton)

        # 图片显示区域
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.verticalScrollBar().valueChanged.connect(self.scrollbarValueChanged)  # 滚动时加载可见图片
        self.scrollArea.horizontalScrollBar().valueChanged.connect(self.scrollbarValueChanged)  # 滚动时加载可见图片
        mainLayout.addWidget(self.scrollArea)

        self.imageContainer = QWidget()
        self.imageLayout = QGridLayout()
        self.imageLayout.setHorizontalSpacing(self.spacing)
        self.imageLayout.setVerticalSpacing(self.spacing)
        self.imageLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.imageLayout.setContentsMargins(0, 0, 0, 0)
        self.imageContainer.setLayout(self.imageLayout)
        self.scrollArea.setWidget(self.imageContainer)

        self.setWindowTitle('图片浏览器')
        self.setGeometry(100, 100, 800, 600)
        self.show()

    def openDirectory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_path:
            self.directoryInput.setText(dir_path)
            self.prepareImages(dir_path)

    def prepareImages(self, dir_path):
        logging.info(f"准备目录 {dir_path} 中的图片")
        image_files = [f for f in os.listdir(dir_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        self.image_files = {f: os.path.join(dir_path, f) for f in image_files}
        print(f"找到 {len(self.image_files)} 张图片")
        self.displayPlaceholderImages()

    def displayPlaceholderImages(self):
        row, col = 0, 0
        num_columns = max(1, self.scrollArea.viewport().width() // (self.image_width + self.spacing))
        for filename in self.image_files:
            label = QLabel()
            label.setFixedSize(self.image_width, self.image_height)
            label.setStyleSheet("background-color: gray")  # 灰色占位图
            textLabel = QLabel(filename.split('.')[0])
            textLabel.setAlignment(Qt.AlignCenter)
            textLabel.setFixedHeight(self.label_height)
            self.imageLayout.addWidget(label, row, col)
            self.imageLayout.addWidget(textLabel, row + 1, col)
            self.image_labels[filename] = label

            col += 1
            if col >= num_columns:
                row += 2  # 为文件名标签留出空间
                col = 0

        print("图片标签准备完成")
        self.timer.start(200)  # 启动定时器重新调整布局

    def loadVisibleImages(self):
        logging.debug("加载可见图片")
        visible_rect = self.scrollArea.viewport().rect()
        for filename, label in self.image_labels.items():
            label_rect = label.geometry().translated(-self.scrollArea.horizontalScrollBar().value(), -self.scrollArea.verticalScrollBar().value())
            visible = visible_rect.intersects(label_rect)
            pixmap = label.pixmap()
            loaded = pixmap is not None and not pixmap.isNull()
            if visible and not loaded:
                logging.debug(f"加载图片：{filename}")
                pixmap = QPixmap(self.image_files[filename]).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
            if not visible and loaded:
                logging.debug(f"卸载图片：{filename}")
                label.setPixmap(QPixmap())
    
    def scrollbarValueChanged(self):
        self.timer.start(200)  # 启动定时器重新调整布局

    def resizeEvent(self, event):
        # 清除现有的图片显示以响应窗口大小变化
        super().resizeEvent(event)
        self.timer.start(200)  # 启动定时器重新调整布局

    def handleVisibilityChange(self):
        self.loadVisibleImages()  # 重新加载可见图片
        self.timer.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageGallery("/Users/chenweichu/dev/data/test_副本/thumbnail")
    # ex = ImageGallery("/Volumes/192.168.1.173/pic/鞠婧祎_4999[5_GB]/thumbnail")
    sys.exit(app.exec_())
