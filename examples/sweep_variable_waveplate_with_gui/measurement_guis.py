"""
================
Measurement GUIs
================

This file contains the code to create different guis, one for each measurement you would like to perform.

"""
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import pyqtSlot
from hyperion.view.base_plot_windows import BaseGraph

class SweepWaveplatePolarimeterGui(QWidget):
    """"
    Simple measurement gui which can only be accessed by making an instance of this class.
    """
    def __init__(self, experiment):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.title = 'Sweep Waveplate Polarimeter'
        self.left = 50
        self.top = 50
        self.width = 320
        self.height = 200
        self.experiment = experiment
        #self.plot_window = plot_window
        self.initUI()

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
        """ Action

        """
        self.logger.debug('Experiment class: {}'.format(self.experiment))
        self.logger.debug('Experiment properties: {}'.format(self.experiment.properties))
        self.experiment.sweep_waveplate_polarimeter()
        self.logger.debug('Experiment done!')