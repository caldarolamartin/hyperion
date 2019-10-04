"""
================
Measurement GUIs
================

This file contains the code to create different guis, one for each measurement you would like to perform.

"""
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import pyqtSlot, QTimer
from hyperion.view.base_plot_windows import BaseGraph

class SweepWaveplatePolarimeterGui(QWidget):
    """"
    Simple measurement gui which can only be accessed by making an instance of this class.
    """
    def __init__(self, experiment, plot_window):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.title = 'Sweep Waveplate Polarimeter'
        self.left = 50
        self.top = 50
        self.width = 320
        self.height = 200
        self.experiment = experiment
        self.plot_window = plot_window

        self.initUI()
        self.plot_window.pg_plot.setData(range(10),[1]*10)


        # timer to update
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self._is_measuring = False

    def initUI(self):
        self.logger.debug('Setting up the Measurement GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        button = QPushButton('Start', self)
        button.setToolTip('This is an example button')
        button.move(100, 70)
        button.clicked.connect(self.on_click)

        self.show()

    @pyqtSlot()
    def on_click(self):
        """ Start the measurement and the update of the plot

        """
        self.logger.info('Starting experiment: Sweep waveplate polarimeter')
        self.timer.start(50)
        self.experiment.sweep_waveplate_polarimeter()
        self.logger.info('Experiment done!')
        self.timer.stop()

    def update_plot(self):

        x = self.experiment.xdata
        y = self.experiment.ydata
        print(y)
        self.plot_window.pg_plot.setData(x,y)

class SweepWaveplatePolarimeterGraph(BaseGraph):
    """
    In this class a widget is created to draw a graph on.
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating the Graph for the polarimeter vs vwp voltage')
        self.title = 'Graph view: Polarimeter vs VWP voltage'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.initUI()