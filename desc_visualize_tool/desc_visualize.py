import os
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QListWidgetItem, QMessageBox, QLabel, QGridLayout, QScrollArea, QWidget
from PyQt5.QtCore import Qt, QFileSystemWatcher
from PyQt5.QtGui import QPixmap
from pathlib import Path

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

class FileViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = '文件浏览器'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.current_directory = ''
        self.watcher = QFileSystemWatcher()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)
        vLayout = QVBoxLayout()

        hLayout = QHBoxLayout()
        self.entry_directory = QtWidgets.QLineEdit()
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
        self.image_container.setLayout(self.image_layout)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.file_list)
        splitter.addWidget(self.scroll_area)
        splitter.setSizes([200, 440])

        vLayout.addLayout(hLayout)
        vLayout.addWidget(splitter)
        widget.setLayout(vLayout)

    def open_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if directory:
            self.entry_directory.setText(directory)
            if self.current_directory:
                self.watcher.removePath(self.current_directory)
            self.current_directory = directory
            self.watcher.addPath(directory)
            self.watcher.directoryChanged.connect(self.directory_changed)
            self.populate_files_list(directory)

    def populate_files_list(self, directory):
        self.file_list.clear()
        files = [f for f in os.listdir(directory) if f.endswith('.txt')]
        descriptor_files = [f for f in files if self.is_descriptor_file(os.path.join(directory, f))]
        for file in descriptor_files:
            self.file_list.addItem(QListWidgetItem(file))

    def is_descriptor_file(self, filepath):
        try:
            with open(filepath, 'r') as file:
                first_line = file.readline()
                return "Unique Images:" in first_line
        except Exception as e:
            print(f"Error checking descriptor file: {e}")
            return False

    def display_file_content(self, item):
        filepath = os.path.join(self.current_directory, item.text())
        try:
            descriptor = ImageDescriptor.deserialize(filepath)
            self.update_image_display(descriptor)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法解析文件: {e}")

    def update_image_display(self, descriptor):
        self.clear_layout(self.image_layout)
        
        row = 0
        col = 0
        max_col = self.scroll_area.width() // 260  # assuming each image takes up 260px including spacing

        self.image_layout.addWidget(QLabel("唯一图片"), row, col, 1, max_col)
        row += 1
        for image in descriptor.unique_images:
            if col >= max_col:
                col = 0
                row += 1
            label = QLabel()
            pixmap = QPixmap(str(image))
            if pixmap.isNull():
                label.setText(f"无法加载图片 {image.name}")
            else:
                label.setPixmap(pixmap.scaled(256, 256, Qt.KeepAspectRatio))
            self.image_layout.addWidget(label, row, col)
            col += 1

        row += 1
        col = 0
        self.image_layout.addWidget(QLabel("重复图片组"), row, col, 1, max_col)
        row += 1
        group_number = 1
        for group in descriptor.similar_groups:
            if col >= max_col:
                col = 0
                row += 1
            self.image_layout.addWidget(QLabel(f"第{group_number}组"), row, col, 1, max_col)
            row += 1
            group_number += 1
            for image in group:
                if col >= max_col:
                    col = 0
                    row += 1
                label = QLabel()
                pixmap = QPixmap(str(image))
                if pixmap.isNull():
                    label.setText(f"无法加载图片 {image.name}")
                else:
                    label.setPixmap(pixmap.scaled(256, 256, Qt.KeepAspectRatio))
                self.image_layout.addWidget(label, row, col)
                col += 1

    def directory_changed(self, path):
        if path == self.current_directory:
            self.populate_files_list(path)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileViewerApp()
    ex.show()
    sys.exit(app.exec_())
