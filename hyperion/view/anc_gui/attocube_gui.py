import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QComboBox, QGridLayout


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'attocube gui, '
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 200
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.scanner_piezo_combobox = QComboBox(self)
        self.scanner_piezo_combobox.addItems(["dit","komt","later"])
        self.grid_layout.addWidget(self.scanner_piezo_combobox, 0, 4)




        button = QPushButton('', self)
        button.setToolTip('This is an example button')
        button.move(100, 70)
        button.clicked.connect(self.on_click)

        self.show()

    def on_click(self):
        print('PyQt5 button click')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
