"""
=================
Base Plot windows
=================

This file contains different base classes to make several types of plots.

* BaseGraph: This is a base class for creating a plot windows.

Still rudimentary and in progress

"""
import logging
import pyqtgraph as pg
from PyQt5.QtWidgets import *

class BaseGraph(QWidget):
    """
    In this class a widget is created to draw a graph on.
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating the BaseGraph ')
        self.title = 'BaseGraph Plot'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.pg_plot_widget = pg.PlotWidget()
        self.pg_plot = self.pg_plot_widget.plot([0],[0])
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        vbox.addWidget(self.pg_plot_widget)
        self.setLayout(vbox)
        self.show()


