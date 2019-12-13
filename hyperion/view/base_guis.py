"""
=============
Base for GUIS
=============

This file contains different base classes to make several types of guis.

'hyperion.view.BaseGui' is for building Qwidget guis.

'hyperion.view.BaseGraph' is for building Qwidget that contains creating a plot.


"""
import traceback
from hyperion import logging
import sys
from hyperion import root_dir
import pyqtgraph as pg
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from os import path


class BaseGui(QWidget):
    """Base class to build a gui that can be loaded in the master gui.


    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # To avoid the crash when there is an error
        sys.excepthook = self.excepthook  # This is very handy in case there are exceptions that force the program to quit.

    def excepthook(self, etype, value, tb):
        """This is what it gets executed when there is an error. Here we build an
        error dialog box

        """
        self.logger.error('An error occurred. NameError: {} '.format(value))
        self.error_dialog(etype, value, tb)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.logger.debug('Exiting the with for the gui class')

    def error_dialog(self, etype, value, tb):
        """ Builds an error dialog box that pops up when there is an error. It shows the error in the details.
        It has two buttons: Ignore and Abort. Ignore continues and Abort closes

        """
        traceback.print_exception(etype, value, tb) # this prints the error in the terminal.
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)

        msg.setText("There was an error. \n Press Ignore or (x) to continue and Abort to exit the GUI.")
        msg.setWindowTitle("Error Box")
        text = ''
        for a in traceback.format_exception(etype, value, tb):
            text += '{}'.format(a)

        msg.setDetailedText("{}".format(text))
        msg.setStandardButtons(QMessageBox.Ignore | QMessageBox.Abort)
        msg.setDefaultButton(QMessageBox.Abort)
        msg.setEscapeButton(QMessageBox.Ignore)
        msg.buttonClicked.connect(self.error_dialog_btn)
        msg.exec_()

    def error_dialog_btn(self, i):
        """ Function that decides what to do when you press the buttons in the error dialog box.

        :param i: event when the QMessageBox buttons are pressed

        """
        self.logger.debug("Button pressed is: {}".format(i.text()))
        if i.text() == 'Abort':
            self.close() # to close the Qwidget


class BaseGraph(BaseGui):
    """
    In this class a widget is created to draw a graph on.
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating the BaseGraph ')
        self.title = 'BaseGraph Plot'
        self.left = 50
        self.top = 50
        self.width = 640
        self.height = 480
        self.plot_title = None

    def initialize_plot(self):
        """ This actually plots in the window. """
        if self.plot_title is None:
            self.plot_title = 'Title plot'
        # make the plot
        self.pg_plot_widget = pg.PlotWidget(title=self.plot_title)
        self.pg_plot = self.pg_plot_widget.plot([0],[0])

        # self.initUI()     # Removed this. It should be called by the child

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(path.join(root_dir,'view','base_plot_windows_icon.png')))
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        vbox.addWidget(self.pg_plot_widget)
        self.setLayout(vbox)
        self.show()

class TimeAxisItem(pg.AxisItem):
    """This code I found on the internet to change things of the axes, for instance the color or the size of the numbers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def attachToPlotItem(self, plotItem):
        """Add this axis to the given PlotItem
        :param plotItem: (PlotItem)
        """
        self.setParentItem(plotItem)
        viewBox = plotItem.getViewBox()
        self.linkToView(viewBox)
        self._oldAxis = plotItem.axes[self.orientation]['item']
        self._oldAxis.hide()
        plotItem.axes[self.orientation]['item'] = self
        pos = plotItem.axes[self.orientation]['pos']
        plotItem.layout.addItem(self, *pos)
        self.setZValue(-1000)


