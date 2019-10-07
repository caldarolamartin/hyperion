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
from hyperion.view.general_worker import WorkThread

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
        # self.plot_window.pg_plot.setData(range(10),[1]*10)  # trying this out


        # timer to update
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        # self._is_measuring = False

    def initUI(self):
        self.logger.debug('Setting up the Measurement GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.start_button = QPushButton('Start sweep', self)
        self.start_button.setToolTip('This is an example button')
        self.start_button.move(100, 70)
        self.start_button.clicked.connect(self.start_button_clicked)

        self.show()

    # # @pyqtSlot() # not sure if this is necessary
    # def on_click(self):
    #     """ Start the measurement and the update of the plot
    #
    #     """
    #     self._is_measuring = True
    #     self.logger.info('Starting experiment: Sweep waveplate polarimeter')
    #     self.timer.start(50)
    #     self.experiment.sweep_waveplate_polarimeter()
    #     self.logger.info('Experiment done!')
    #     # self.timer.stop()

    def start_button_clicked(self):

        if self.experiment._sweep_waveplate_polarimeter_in_progress:
            self.logger.debug('Aborting sweep')
            self.experiment._sweep_waveplate_polarimeter_in_progress = False
            # change the button text
            # self.start_button.setText('Abort sweep')
            # self.timer.stop()

        else:
            self.logger.debug('Starting sweep')
            self.sweep_thread = WorkThread(self.experiment.sweep_waveplate_polarimeter)
            self.sweep_thread.start()
            self.start_button.setText('Abort sweep')
            self.timer.start(50)  # in ms
            # change the button text
            # self.start_button.setText('Start sweep')
            # self.measurement_thread = WorkThread(self.continuous_data)
            # self.measurement_thread.start()

    def update_plot(self):

        if not self.experiment._sweep_waveplate_polarimeter_in_progress:
            # The sweep has ended: reset button text and stop updating graph
            self.start_button.setText('Start sweep')
            self.timer.stop()
        else:
            x = self.experiment.xdata
            y = self.experiment.ydata
            self.plot_window.pg_plot.setData(x, y)

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