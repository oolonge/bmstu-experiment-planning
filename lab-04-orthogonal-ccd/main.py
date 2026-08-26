# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import QLibraryInfo
os.environ.setdefault(
    'QT_PLUGIN_PATH',
    QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath),
)

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
