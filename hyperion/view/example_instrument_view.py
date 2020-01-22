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

    def __init__(self, example_instr, output_gui=None, also_close_output=True):
        super().__init__()
        self.logger = logman.getLogger(__name__)
        self.also_close_output = also_close_output
        self.example_instr = example_instr
        self.output_gui = output_gui
        if self.output_gui is None:
            self.curve = lambda *args, **kwargs: None
        else:
            self.curve = self.output_gui.plot() # initialize plot
        self.title = 'Example Gui'
        self.left = 40
        self.top = 40
        self.width = 320
        self.height = 200
        self.initUI()

        self.cont_plot_timer = QTimer()
        self.cont_plot_timer.timeout.connect(self.show_one_plot)

    def stop(self):
        """
        Stop the instruments activity. This can be used by a measurement or an ExperimentGui to tell an instrument to stop doing what it's doing (so that it can start taking
        """
        if self.cont_plot_timer.isActive():
            self.cont_plot_timer.stop()


    def closeEvent(self, event):
        if self.also_close_output and self.output_gui is not None:
            if self.cont_plot_timer.isActive():
                self.logger.debug('Stop continuous plotting')
                self.cont_plot_timer.stop()
            self.logger.debug('Closing output widget')
            try:
                self.output_gui.close()
            except:
                pass

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
        data = self.example_instr.return_fake_1D_data()
        # update the plot
        self.curve.setData(data)

    def show_continuous_plot(self):
        if not self.cont_plot_timer.isActive():
            self.button_once.setDisabled(True)
            self.button_cont.setText('Stop continuous')
            self.cont_plot_timer.start(100)  # in ms
            self.continuous = True
        else:
            self.continuous = False
            self.cont_plot_timer.stop()
            self.button_once.setDisabled(False)
            self.button_cont.setText('Start continuous plot')


class ExampleInstrumentGuiMultiplePlots(BaseGui):
    def __init__(self, example_ins, output_gui_dict, also_close_output=True):
        super().__init__()
        self.logger = logman.getLogger(__name__)
        self.also_close_output = also_close_output
        self.output_gui_dict = output_gui_dict
        if type(self.output_gui_dict) is not dict:
            self.logger.error('This example needs a dictionary of visualization guis')

        self.plot_a = self.output_gui_dict['Spectrum'].plot()
        self.plot_b = self.output_gui_dict['Power'].plot()

        self.title = 'Example Gui Multiple Plots'
        self.left = 40
        self.top = 40
        self.width = 320
        self.height = 200
        self.example_ins = example_ins
        self.initUI()

        self.cont_plot_timer = QTimer()
        self.cont_plot_timer.timeout.connect(self.show_plot_b)

    def stop(self):
        """
        Stop the instruments activity. This can be used by a measurement or an ExperimentGui to tell an instrument to stop doing what it's doing (so that it can start taking
        """
        if self.cont_plot_timer.isActive():
            self.cont_plot_timer.stop()

    def closeEvent(self, event):
        if self.also_close_output and self.output_gui_dict is not None:
            if self.cont_plot_timer.isActive():
                self.logger.debug('Stop continuous plotting')
                self.cont_plot_timer.stop()
            self.logger.debug('Closing output widgets')
            try:
                for instance in self.output_gui_dict.values():
                    instance.close()
            except:
                pass

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # self.setAutoFillBackground(True)
        # self.p = self.palette()
        # self.set_color(Qt.red)
        self.button_once = QPushButton('Generate random plot')
        self.button_once.clicked.connect(self.show_plot_a)
        self.button_cont = QPushButton('Start continuous plot')
        self.button_cont.clicked.connect(self.show_continuous_plot)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.button_once)
        self.layout.addWidget(self.button_cont)
        self.setLayout(self.layout)
        self.show()

    def show_plot_a(self):
        # Grab data from instrument here (or check if new data is available)
        data = np.random.normal(size=100)
        # update the plot
        self.plot_a.setData(data)

    def show_plot_b(self):
        # Grab data from instrument here (or check if new data is available)
        data = np.random.normal(size=100)
        # update the plot
        self.plot_b.setData(data)


    def show_continuous_plot(self):
        if not self.cont_plot_timer.isActive():
            self.button_cont.setText('Stop continuous')
            self.cont_plot_timer.start(100)  # in ms
            self.continuous = True
        else:
            self.continuous = False
            self.cont_plot_timer.stop()
            self.button_cont.setText('Start continuous plot')


class ExampleInstrumentGui2D(BaseGui):
    """"
    This is simple pyqt5 gui with the ability to create threads and stop them,
    that is harder than it sounds.
    """

    def __init__(self, example_instr, output_gui=None, also_close_output=True):
        super().__init__()
        self.logger = logman.getLogger(__name__)
        self.also_close_output = also_close_output
        self.example_instr = example_instr

        # if output_gui is dict, just grab the first value
        if type(output_gui) is dict:
            self.imv = list(output_gui.values())[0]
        else:
            self.imv = output_gui

        colors = [
            (0, 0, 0),
            (45, 5, 61),
            (84, 42, 55),
            (150, 87, 60),
            (208, 171, 141),
            (255, 255, 255)
        ]
        cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)
        self.imv.setColorMap(cmap)

        self.title = 'Example Gui'
        self.left = 40
        self.top = 40
        self.width = 320
        self.height = 200
        self.initUI()

        self.cont_plot_timer = QTimer()
        self.cont_plot_timer.timeout.connect(self.show_one_plot)

    def stop(self):
        """
        Stop the instruments activity. This can be used by a measurement or an ExperimentGui to tell an instrument to stop doing what it's doing (so that it can start taking
        """
        if self.cont_plot_timer.isActive():
            # self.cont_plot_timer.stop()  # stop the thread
            self.show_continuous_plot()  # "pretent" to hit the stop continuous button



    def closeEvent(self, event):
        if self.also_close_output and self.output_gui is not None:
            if self.cont_plot_timer.isActive():
                self.logger.debug('Stop continuous plotting')
                self.cont_plot_timer.stop()
            self.logger.debug('Closing output widget')
            try:
                self.output_gui.close()
            except:
                pass

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # self.setAutoFillBackground(True)
        # self.p = self.palette()
        # self.set_color(Qt.red)
        self.button_once = QPushButton('Generate random image')
        self.button_once.clicked.connect(self.show_one_plot)
        self.button_cont = QPushButton('Start random video')
        self.button_cont.clicked.connect(self.show_continuous_plot)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.button_once)
        self.layout.addWidget(self.button_cont)
        self.setLayout(self.layout)
        self.show()

    def show_one_plot(self):
        # Grab data from instrument here (or check if new data is available))
        data = self.example_instr.return_fake_2D_data()
        # update the plot
        self.imv.setImage(data.transpose(), xvals=np.linspace(1., 3., data.shape[0]))

    def show_continuous_plot(self):
        if not self.cont_plot_timer.isActive():
            self.button_once.setDisabled(True)
            self.button_cont.setText('Stop continuous')
            self.cont_plot_timer.start(100)  # in ms
            self.continuous = True
        else:
            self.continuous = False
            self.cont_plot_timer.stop()
            self.button_once.setDisabled(False)
            self.button_cont.setText('Start continuous plot')


class ExampleOutputGui(pg.PlotWidget):
# class ExampleOutput(pg.GraphicsWindow):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        # self.show()




if __name__ == '__main__':

    example_ins = ExampleInstrument(settings = {'port':'COM8', 'dummy':False,
                                                'controller': 'hyperion.controller.example_controller/ExampleController'})
    app = QApplication(sys.argv)
    output = ExampleOutputGui()

    # win = pg.GraphicsWindow(title="Basic plotting examples")
    # output = win.addPlot(title = 'Plot Window Title')
    # win.show()

    output = pg.PlotWidget(title='Title')
    output.show()

    ex = ExampleInstrumentGui(example_ins, output)
    sys.exit(app.exec_())