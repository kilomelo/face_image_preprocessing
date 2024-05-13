from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal

class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(ClickableLabel, self).__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignCenter)

    def mousePressEvent(self, event):
        self.clicked.emit()