import sys
import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from hyperion.instrument.example_instrument import ExampleInstrument
from hyperion.view.general_worker import WorkThread
import logging

class ExampleGui(QWidget):
    """"
    This is simple pyqt5 gui with the ability to create threads and stop them,
    that is harder than it sounds.
    """

    def __init__(self, example_ins):
        super().__init__()
        self.title = 'example gui'
        self.left = 40
        self.top = 40
        self.width = 320
        self.height = 200
        self.example_ins = example_ins
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.setAutoFillBackground(True)
        self.p = self.palette()
        self.set_color(Qt.red)
        self.make_button_1()
        self.make_button_2()
        self.show()

    def make_button_1(self):
        self.button = QPushButton('start button', self)
        self.button.setToolTip('This is an example button')
        self.button.move(10,10)
        self.button.clicked.connect(self.on_click)
    def make_button_2(self):
        self.button_2 = QPushButton('end button',self)
        self.button_2.setToolTip('end the function')
        self.button_2.move(90, 10)
        self.button_2.clicked.connect(self.stop_on_click_function)


    def set_color(self, color):
        """
        Set the color of the widget
        :param color: a color you want the gui to be
        :type string
        """
        self.p.setColor(self.backgroundRole(), color)
        self.setPalette(self.p)

    def on_click(self):
        #initialize a long(couple of seconds) test function.
        self.worker_thread = WorkThread(self.go_to_sleep)
        self.worker_thread.start()

    def stop_on_click_function(self):
        """
        stop a thread if one is running
        """
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
            print('this function is going to stop the on_click function')
        else:
            return

    def go_to_sleep(self):
        """
        function that starts the thread.
        """
        print('button click')
        self.button.setEnabled(False)
        self.set_color(Qt.yellow)
        time.sleep(4)
        self.set_color(Qt.red)
        self.button.setEnabled(True)

if __name__ == '__main__':
    from hyperion import _logger_format, _logger_settings
    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])


    example_ins = ExampleInstrument()
    app = QApplication(sys.argv)
    ex = ExampleGui(example_ins)
    sys.exit(app.exec_())