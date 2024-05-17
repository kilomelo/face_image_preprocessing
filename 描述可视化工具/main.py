import sys
from PyQt5.QtWidgets import QApplication
from descriptor_viewer import DescripterViewer
from utils import setup_logging

def main():
    app = QApplication(sys.argv)
    setup_logging()
    # viewer = DescripterViewer("/Users/chenweichu/dev/data/test_副本")
    # viewer = DescripterViewer("/Volumes/192.168.1.173/pic/陈都灵_503[167_MB]")
    viewer = DescripterViewer("/Volumes/192.168.1.173/pic/鞠婧祎_4999[5_GB]")
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()