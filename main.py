from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget, QAction
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui

from src.gui import ControllerWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PlayerTracker")

        self.central_widget = ControllerWidget("/disk1/zhangmeng/basketball/basketball_20220626/dynamic4D_format/training")
        self.central_widget.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.central_widget)
        self.central_widget.setFocus(True)

        self.statusBar()

        mainMenu = self.menuBar()

        fileMenu = mainMenu.addMenu('&File')
        helpMenu = mainMenu.addMenu('&Help')

        close = QAction('Close window', self)
        close.setShortcut('Ctrl+W')
        close.triggered.connect(self.close)
        fileMenu.addAction(close)
        self.setCentralWidget(self.central_widget)

        self.show()
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):
        print("exiting")

if __name__ == '__main__':
    app = QApplication([])
    main_window = MainWindow()
    app.exec()