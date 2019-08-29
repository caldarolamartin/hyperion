import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot


class App(QWidget):
    """"
    Simple measurement gui which can only be accessed by making an instance of this class.
    """
    def __init__(self, experiment):
        super().__init__()
        self.title = 'measurement gui'
        self.left = 50
        self.top = 50
        self.width = 320
        self.height = 200
        self.experiment = experiment
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        button = QPushButton('click me', self)
        button.setToolTip('This is an example button')
        button.move(100, 70)
        button.clicked.connect(self.on_click)

        self.show()

    @pyqtSlot()
    def on_click(self):
        print("button clicked\nyeah, that is the measurement")