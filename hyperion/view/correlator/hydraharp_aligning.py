"""
===================
Attocube GUI
===================

This is to build a gui for the instrument piezo motor attocube.


"""
import sys, os
import logging
import numpy as np
import time
from hyperion import ur
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from hyperion.instrument.correlator.hydraharp_instrument import HydraInstrument
from hyperion.view.base_guis import BaseGui
from hyperion.view.general_worker import WorkThread

class Hydraharp_aligning_GUI(BaseGui):
    """

    :param
    :type

    """
    def __init__(self, hydra_instrument):
        """Hydraharp aligning
        """

        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.title = 'Hydraharp Aligning GUI'
        self.left = 50
        self.top = 50
        self.width = 500
        self.height = 250
        self.hydra_instrument = hydra_instrument

        self.exp_type = 'Finite'
        self.pausetime = 500*ur('ms')
        self.lengthaxis = 10*ur('s')
        self.sync = True
        self.chan1 = False
        self.chan2 = False

        self.sync_counts = 0.0
        self.counts1 = 0.0
        self.counts2 = 0.0

        self.running = False
        self.data = []
        self.counts = [[],[],[],[]]     #first column will be time, the others counts on different channels
        #self.tijd = []
        # self.chan_name = {'sync':0, 'counts1':1, 'counts2':2}
        self.time_axis = []

        self.pen = pg.mkPen(color=(0, 0, 0))  # makes the plotted lines black

        name = 'aligning.ui'
        gui_folder = os.path.dirname(os.path.abspath(__file__))
        gui_file = os.path.join(gui_folder, name)
        self.logger.info('Loading the GUI file: {}'.format(gui_file))
        self.gui = uic.loadUi(gui_file, self)

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.ask_counts)
        self.timer.start(100)       #time in ms

    def initUI(self):
        """Connect all buttons, comboBoxes and doubleSpinBoxes to methods
        """
        self.logger.debug('Setting up the Measurement GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.show()

        self.gui.pushButton_start.clicked.connect(self.start_plotting)
        self.gui.pushButton_stop.clicked.connect(self.stop_plotting)
        self.pushButton_stop.setStyleSheet("background-color: red")

        self.gui.pushButton_save.clicked.connect(self.save_counts)

        self.gui.comboBox_finite.setCurrentText(self.exp_type)
        self.gui.comboBox_finite.currentTextChanged.connect(self.get_exp_type)

        self.gui.doubleSpinBox_pause.setValue(self.pausetime.m_as('ms'))
        self.gui.doubleSpinBox_pause.valueChanged.connect(self.set_pausetime)

        self.gui.doubleSpinBox_timeaxis.setValue(self.lengthaxis.m_as('s'))
        self.gui.doubleSpinBox_timeaxis.valueChanged.connect(self.set_lengthaxis)

        self.gui.checkBox_sync.setChecked(self.sync)
        self.gui.checkBox_sync.stateChanged.connect(self.set_channel)

        self.gui.checkBox_chan1.setChecked(self.chan1)
        self.gui.checkBox_chan1.stateChanged.connect(self.set_channel)

        self.gui.checkBox_chan2.setChecked(self.chan2)
        self.gui.checkBox_chan2.stateChanged.connect(self.set_channel)

    #Read user inputs
    # -----------------------------------------------------------------------------------------
    def get_exp_type(self):
        self.logger.debug('Should read the experiment type here')
        self.exp_type = self.gui.comboBox_finite.currentText()
        self.logger.debug('Chosen type: {}'.format(self.exp_type))

    def set_pausetime(self):
        self.logger.debug('Should set the pause time here')
        self.pausetime = self.gui.doubleSpinBox_pause.value()*ur('ms')
        self.logger.debug('Chosen time: {}'.format(self.pausetime))

    def set_lengthaxis(self):
        self.logger.debug('Should set the length of the axis here')
        self.lengthaxis = self.gui.doubleSpinBox_timeaxis.value()*ur('s')
        self.logger.debug('Chosen length of axis: {}'.format(self.lengthaxis))

    def set_channel(self):
        self.sync = self.checkBox_sync.isChecked()
        self.chan1 = self.gui.checkBox_chan1.isChecked()
        self.chan2 = self.gui.checkBox_chan2.isChecked()
        self.logger.debug('Sync channel: {}, channel 1: {}, channel 2: {}'.format(self.sync, self.chan1, self.chan2))

    #Actual methods doing something
    #-----------------------------------------------------------------------------------------
    def ask_counts(self):
        """ | Connects to the device and read out the count rate of either the sync or on of the count channels.
        | Displays this on the labels on the gui, which are updated via the timer in the init.
        """
        self.logger.debug('Asking for counts')

        something_selected = False

        if self.sync:
            self.sync_counts = self.hydra_instrument.sync_rate()
            #self.logger.debug("{}".format(self.sync_counts))
            self.gui.label_counts_sync.setText(str(self.sync_counts))
            something_selected = True

        if self.chan1:
            self.counts1 = self.hydra_instrument.count_rate(0)
            #self.logger.debug("{}".format(self.counts1))
            something_selected = True
            self.gui.label_counts1.setText(str(self.counts1))

        if self.chan2:
            self.counts2 = self.hydra_instrument.count_rate(1)
            #self.logger.debug("{}".format(self.counts2))
            self.gui.label_counts2.setText(str(self.counts2))
            something_selected = True

        if something_selected == False:
            self.logger.warning('Nothing is selected')


    def start_plotting(self):
        """| Prepares for plotting by making a time axis based on the axis length and pause time, and starts an empty counts array.
        | Then opens 1 to 3 plot windows and threads, depending on the selected channels.

        """
        self.logger.debug('Should start counting here')

        self.logger.debug('Settings: {}, {}, {}'.format(self.exp_type, self.pausetime, self.lengthaxis))

        self.time_axis = np.linspace(0, self.lengthaxis.m_as('s') * self.pausetime.m_as('s'), int(self.lengthaxis.m_as('s'))) * ur('s')
        self.logger.debug("{}".format(self.time_axis))

        Counts = np.zeros(int(self.lengthaxis.m_as('s')))

        if self.sync:
            channel = 'sync'

            self.draw0 = DrawCounts()
            self.draw0.counts_plot.setTitle("<span style=\"color:orange;font-size:30px\">{} channel </span>".format(channel))

            self.draw0.counts_plot.plot(self.time_axis.m_as('s'), Counts, clear=True, pen=self.pen)

            self.plotting_sync_thread = WorkThread(self.update_plot, Counts, channel)
            self.plotting_sync_thread.start()

        if self.chan1:
            channel = 'counts1'

            self.draw1 = DrawCounts()
            self.draw1.counts_plot.setTitle("<span style=\"color:orange;font-size:30px\">{} channel </span>".format(channel))

            self.draw1.counts_plot.plot(self.time_axis.m_as('s'), Counts, clear=True, pen=self.pen)

            self.plotting_counts1_thread = WorkThread(self.update_plot, Counts, channel)
            self.plotting_counts1_thread.start()

        if self.chan2:
            channel = 'counts2'

            self.draw2 = DrawCounts()
            self.draw2.counts_plot.setTitle("<span style=\"color:orange;font-size:30px\">{} channel </span>".format(channel))

            self.draw2.counts_plot.plot(self.time_axis.m_as('s'), Counts, clear=True, pen=self.pen)

            self.plotting_counts2_thread = WorkThread(self.update_plot, Counts, channel)
            self.plotting_counts2_thread.start()


    def update_plot(self, Counts, channel):
        """| This method is called and threaded from start_plotting, depending on the selected channels can be started 1 to 3 times.
        | It either works for a Finite amount of time or works infinitely, to make aligning possible.
        | It draws the plot with the time axis, which is the same for all channels,
        | and the Counts, that are a numpy array that is constantly filled with the current Rate.
        | Depending on the channel, the counts are plotted in three different self.draw windows.

        :param Counts: array of the size of the axis length
        :type Counts: numpy array

        :param channel: sync, counts1 or counts2
        :type channel: string
        """
        self.running = True

        self.logger.debug('channel: {}'.format(channel))

        if self.exp_type == 'Finite':

            for ii in range(0, int(self.lengthaxis.m_as('s'))):
                if self.running == False:
                    break
                else:
                    if channel == 'sync':
                        currRate = self.sync_counts
                        Counts[ii] = currRate.m_as('cps')
                        self.logger.debug('Counts: {}'.format(Counts[ii]))

                        self.draw0.counts_plot.plot(self.time_axis, Counts, clear=True, pen=self.pen)

                    elif channel == 'counts1':
                        currRate = self.counts1
                        Counts[ii] = currRate.m_as('cps')
                        self.logger.debug('Counts: {}'.format(Counts[ii]))

                        self.draw1.counts_plot.plot(self.time_axis, Counts, clear=True, pen=self.pen)

                    elif channel == 'counts2':
                        currRate = self.counts2
                        Counts[ii] = currRate.m_as('cps')
                        self.logger.debug('Counts: {}'.format(Counts[ii]))

                        self.draw2.counts_plot.plot(self.time_axis, Counts, clear=True, pen=self.pen)

                    time.sleep(self.pausetime.m_as('s'))

        elif self.exp_type == 'Infinite':
            ii=0
            while self.running:
                if ii < int(self.lengthaxis.m_as('s')):
                    Counts[ii] = currRate.m_as('cps')

                else:
                    Counts = np.roll(Counts, -1)
                    Counts[-1] = currRate.m_as('cps')
                    self.logger.debug('{}'.format(Counts))

                if channel == 'sync':
                    currRate = self.sync_counts
                    self.draw0.counts_plot.plot(self.time_axis, Counts, clear=True, pen=self.pen)

                elif channel == 'counts1':
                    currRate = self.counts1
                    self.draw1.counts_plot.plot(self.time_axis, Counts, clear=True, pen=self.pen)

                elif channel == 'counts2':
                    currRate = self.counts2
                    self.draw2.counts_plot.plot(self.time_axis, Counts, clear=True, pen=self.pen)

                ii+=1
                time.sleep(self.pausetime.m_as('s'))

        self.running = False

        # self.counts[0] = Tijd
        # self.counts[self.chan_name[channel]+1]=Counts   #change this back again
        # self.tijd = (pausetime.m_as('s') * lengthaxis)*ur('s')

    def stop_plotting(self):
        if self.running:
            self.logger.debug('Should stop counting here')
            self.running = False

            if self.sync:
                self.plotting_sync_thread.quit()

            if self.chan1:
                self.plotting_counts1_thread.quit()

            if self.chan2:
                self.plotting_counts2_thread.quit()

        else:
            self.logger.warning('There is nothing to stop here')


    def save_counts(self):
        self.logger.debug('Should save all plots here')

class DrawCounts(QWidget):

    """
    In this class a widget is created to draw a graph on.
    """

    def __init__(self):
        super().__init__()
        self.title = 'Count rate on channel'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.counts_plot = pg.PlotWidget()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        vbox.addWidget(self.counts_plot)

        self.layout_plot()

        self.setLayout(vbox)
        self.show()

    def layout_plot(self):
        self.counts_plot.setBackground('w')

        #self.histogram_plot.setTitle("Histogram", color=(255,0,0))
        #self.histogram_plot.setLabel('left','Correlated counts','a.u.')

        Xaxis = TimeAxisItem(orientation = 'bottom')
        Xaxis.attachToPlotItem(self.counts_plot.getPlotItem())
        Xaxis.setPen(color = (0,0,0))

        Yaxis = TimeAxisItem(orientation = 'left')
        Yaxis.attachToPlotItem(self.counts_plot.getPlotItem())
        Yaxis.setPen(color = (0,0,0))

        self.counts_plot.setLabel('left', "<span style=\"color:black;font-size:20px\"> Counts [1/s] </span>")
        self.counts_plot.setLabel('bottom', "<span style=\"color:black;font-size:20px\"> Time [s] </span>")

        font = QtGui.QFont()
        font.setPixelSize(20)
        self.counts_plot.getAxis("bottom").tickFont = font
        self.counts_plot.getAxis("left").tickFont = font

class TimeAxisItem(pg.AxisItem):
    """This code I found on the internet to change the color of the axes.
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


if __name__ == '__main__':
    import hyperion

    with HydraInstrument(settings={'devidx': 0, 'mode': 'Histogram', 'clock': 'Internal','controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'}) as hydra_instrument:
        app = QApplication(sys.argv)
        # draw1 = DrawCounts()
        #draw2 = DrawCounts()
        ex = Hydraharp_aligning_GUI(hydra_instrument)
        sys.exit(app.exec_())

