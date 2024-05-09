import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QScrollArea, QLabel, QGridLayout
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ImageGallery(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

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
        mainLayout.addWidget(self.scrollArea)

        self.imageContainer = QWidget()
        self.imageLayout = QGridLayout()
        self.imageContainer.setLayout(self.imageLayout)
        self.scrollArea.setWidget(self.imageContainer)

        self.setWindowTitle('图片浏览器')
        self.setGeometry(100, 100, 800, 600)
        self.show()

    def openDirectory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_path:
            self.directoryInput.setText(dir_path)
            self.loadImages(dir_path)

    def loadImages(self, dir_path):
        try:
            logging.info(f"加载目录 {dir_path}")
            for i in reversed(range(self.imageLayout.count())): 
                self.imageLayout.itemAt(i).widget().setParent(None)

            images = [f for f in os.listdir(dir_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            row, col = 0, 0
            for idx, image in enumerate(images):
                try:
                    img_path = os.path.join(dir_path, image)
                    img = mpimg.imread(img_path)
                    figure = Figure(figsize=(2.56, 2.56))  # 创建一个大概8.192x8.192英寸的Figure，dpi默认为100
                    canvas = FigureCanvas(figure)
                    ax = figure.add_subplot(111)
                    ax.imshow(img, aspect='equal', interpolation='none')  # 使用'equal'和'none'以确保图像比例和质量
                    ax.set_xlim(0, 256)
                    ax.set_ylim(256, 0)
                    ax.axis('off')  # 不显示坐标轴

                    filename = os.path.splitext(image)[0]  # 文件名，不包括扩展名
                    label = QLabel(filename)
                    label.setAlignment(Qt.AlignCenter)

                    layout = QVBoxLayout()
                    layout.addWidget(canvas)
                    layout.addWidget(label)

                    container = QWidget()
                    container.setLayout(layout)
                    self.imageLayout.addWidget(container, row, col)

                    col += 1
                    if col >= self.width() // 256:
                        row += 1
                        col = 0
                except Exception as e:
                    logging.error(f"无法加载图片 {image}: {str(e)}")
        except Exception as e:
            logging.error(f"读取目录错误: {str(e)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.directoryInput.text():  # 确保目录输入框不为空
            self.loadImages(self.directoryInput.text())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageGallery()
    sys.exit(app.exec_())
