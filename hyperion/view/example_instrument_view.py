import sys
import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from hyperion.instrument.example_instrument import ExampleInstrument
from hyperion.view.general_worker import WorkThread
from PyQt5.QtCore import QTimer

from hyperion.core import logman
from hyperion.view.base_guis import BaseGui
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg


class ExampleInstrumentGui(BaseGui):
    """"
    This is simple pyqt5 gui with the ability to create threads and stop them,
    that is harder than it sounds.
    """

    def __init__(self, example_ins, output_gui):
        super().__init__()
        self.logger = logman.getLogger(__name__)
        self.output_gui = output_gui
        self.curve = self.output_gui.plot()
        self.title = 'Example Gui'
        self.left = 40
        self.top = 40
        self.width = 320
        self.height = 200
        self.example_ins = example_ins
        self.initUI()
        self.continuous = False

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # self.setAutoFillBackground(True)
        # self.p = self.palette()
        # self.set_color(Qt.red)
        self.button_once = QPushButton('Generate random plot')
        self.button_once.clicked.connect(self.show_one_plot)
        self.button_cont = QPushButton('Start continuous plot')
        self.button_cont.clicked.connect(self.show_continuous_plot)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.button_once)
        self.layout.addWidget(self.button_cont)
        self.setLayout(self.layout)
        self.show()

    def show_one_plot(self):
        # Grab data from instrument here (or check if new data is available)
        data = np.random.normal(size=100)
        # update the plot
        ptr = 0
        self.curve.setData(data)

    def show_continuous_plot(self):
        if not self.continuous:
            self.button_once.setDisabled(True)
            self.button_cont.setText('Stop continuous')
            self.cont_plot_timer = QTimer()
            self.cont_plot_timer.timeout.connect(self.show_one_plot)
            self.cont_plot_timer.start(200)  # in ms
        else:
            self.cont_plot_timer.stop()
            self.button_once.setDisabled(False)
            self.button_cont.setText('Start continuous plot')




class ExampleOutputGui(pg.PlotWidget):
# class ExampleOutput(pg.GraphicsWindow):
    def __init__(self, title):
        super().__init__(title)
        self.show()





if __name__ == '__main__':

    example_ins = ExampleInstrument(settings = {'port':'COM8', 'dummy':False,
                                                'controller': 'hyperion.controller.example_controller/ExampleController'})
    app = QApplication(sys.argv)
    output = ExampleOutputGui('Plotting example')

    ex = ExampleInstrumentGui(example_ins, output)
    sys.exit(app.exec_())