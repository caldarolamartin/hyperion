import sys
import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from hyperion.instrument.example_instrument import ExampleInstrument
from hyperion.view.general_worker import WorkThread


class ExampleGui(QWidget):
    """"
    This is a very simple pyqt5 gui with little more than basic functionality.
    """

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
        self.p = self.palette()
        self.p.setColor(self.backgroundRole(), Qt.red)
        self.setPalette(self.p)

        self.button = QPushButton('start button', self)
        self.button.setToolTip('This is an example button')
        self.button.move(10,10)
        self.button.clicked.connect(self.on_click)

        self.button_2 = QPushButton('end button',self)
        self.button_2.setToolTip('end the function')
        self.button_2.move(90, 10)
        #self.button_2.setEnabled(False)
        self.button_2.clicked.connect(self.stop_on_click_function)
        self.show()
    def on_click(self):
        #disable the ability to press the button multiple times
        #self.button.setEnabled(False)
        #self.button_2.setEnabled(True)
        #make this a long function.
        self.worker_thread = WorkThread(self.go_to_sleep)
        self.worker_thread.start()

    def stop_on_click_function(self):
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
            print('this function is going to stop the on_click function')
        else:
            return

    def go_to_sleep(self):
        self.button.setEnabled(False)
        self.p.setColor(self.backgroundRole(), Qt.yellow)
        self.setPalette(self.p)
        time.sleep(4)
        print('button click')
        self.p.setColor(self.backgroundRole(), Qt.red)
        self.setPalette(self.p)
        self.button.setEnabled(True)

if __name__ == '__main__':
    example_ins = ExampleInstrument()
    app = QApplication(sys.argv)
    ex = ExampleGui(example_ins)
    sys.exit(app.exec_())