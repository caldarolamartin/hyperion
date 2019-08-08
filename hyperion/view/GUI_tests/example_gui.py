#this is a simple gui to load in a QdockWidget
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from hyperion.instrument.example_instrument import ExampleInstrument

class ExampleGui(QWidget):

    def __init__(self, example_ins):
        super().__init__()
        self.title = 'PyQt5 button - pythonspot.com'
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 200
        self.example_ins = example_ins
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)


        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.red)
        self.setPalette(p)

        button = QPushButton('PyQt5 button', self)
        button.setToolTip('This is an example button')
        button.move(10,10)

        button.clicked.connect(self.on_click)

        self.show()
    def on_click(self):
        print('PyQt5 button click')

if __name__ == '__main__':
    example_ins = ExampleInstrument()
    app = QApplication(sys.argv)
    ex = ExampleGui(example_ins)
    sys.exit(app.exec_())