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
from datetime import datetime
from hyperion import ur
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from hyperion.instrument.correlator.hydraharp_instrument import HydraInstrument
from hyperion.view.base_guis import BaseGui, BaseGraph, TimeAxisItem
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
        self.pausetime = 50*ur('ms')
        self.lengthaxis = 10*ur('s')
        self.sync = True
        self.chan1 = False
        self.chan2 = False

        self.sync_counts = 0.0
        self.counts1 = 0.0
        self.counts2 = 0.0

        self.running = False
        self.Sync_counts_array = []
        self.Counts1_array = []
        self.Counts2_array = []
        self.time_axis = []

        self.default_name = 'counts.txt'
        self.path = 'D:\\LabSoftware\\Data\\'

        self.something_selected = False

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
        self.gui.pushButton_save.setEnabled(False)

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

        self.set_name_path()
        self.gui.lineEdit_name.textChanged.connect(self.get_name_path)
        self.gui.lineEdit_path.textChanged.connect(self.get_name_path)

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

    def set_name_path(self):
        self.gui.lineEdit_name.setText(self.default_name)
        self.gui.lineEdit_path.setText(self.path)

    def get_name_path(self):
        self.default_name = self.gui.lineEdit_name.text()
        self.path = self.gui.lineEdit_path.text()

        print(self.gui.lineEdit_name.text())
        print(self.gui.lineEdit_path.text())

    #Actual methods doing something
    #-----------------------------------------------------------------------------------------
    def ask_counts(self):
        """ | Connects to the device and read out the count rate of either the sync or on of the count channels.
        | Displays this on the labels on the gui, which are updated via the timer in the init.
        """
        #self.logger.debug('Asking for counts')

        self.something_selected = False

        if self.sync:
            self.sync_counts = self.hydra_instrument.sync_rate()
            #self.logger.debug("{}".format(self.sync_counts))
            self.gui.label_counts_sync.setText(str(self.sync_counts))
            self.something_selected = True
        else:
            self.gui.label_counts_sync.setText('currently unavailable')

        if self.chan1:
            self.counts1 = self.hydra_instrument.count_rate(0)
            #self.logger.debug("{}".format(self.counts1))
            self.something_selected = True
            self.gui.label_counts1.setText(str(self.counts1))
        else:
            self.gui.label_counts1.setText('currently unavailable')

        if self.chan2:
            self.counts2 = self.hydra_instrument.count_rate(1)
            #self.logger.debug("{}".format(self.counts2))
            self.gui.label_counts2.setText(str(self.counts2))
            self.something_selected = True
        else:
            self.gui.label_counts2.setText('currently unavailable')

        if self.something_selected == False:
            self.logger.warning('Nothing is selected')


    def start_plotting(self):
        """| Prepares for plotting by making a time axis based on the axis length and pause time, and starts an empty counts array.
        | Then opens 1 to 3 plot windows and a thread to plot them, depending on the selected channels.
        """
        self.logger.info('Should start counting here')

        self.logger.debug('Settings: {}, {}, {}'.format(self.exp_type, self.pausetime, self.lengthaxis))

        self.time_axis = np.linspace(0, self.lengthaxis.m_as('s') * self.pausetime.m_as('s'), int(self.lengthaxis.m_as('s'))) * ur('s')
        self.logger.debug("{}".format(self.time_axis))

        if self.something_selected:
            if self.sync:
                self.draw0 = DrawCounts()
                self.draw0.counts_plot.setTitle("<span style=\"color:yellow;font-size:30px\">Counts on sync channel </span>")
                #self.draw0.counts_plot.plot(self.time_axis.m_as('s'), Counts, clear=True, pen=self.pen)

            if self.chan1:
                self.draw1 = DrawCounts()
                self.draw1.counts_plot.setTitle("<span style=\"color:orange;font-size:30px\">Counts on channel 1 </span>")
                #self.draw1.counts_plot.plot(self.time_axis.m_as('s'), Counts, clear=True, pen=self.pen)

            if self.chan2:
                self.draw2 = DrawCounts()
                self.draw2.counts_plot.setTitle("<span style=\"color:red;font-size:30px\">Counts on channel 2 </span>")
                #self.draw2.counts_plot.plot(self.time_axis.m_as('s'), Counts, clear=True, pen=self.pen)

            self.plotting_thread = WorkThread(self.update_plot)
            self.plotting_thread.start()

        else:
            self.logger.warning('You have to select something first, before making a graph.')


    def update_plot(self):
        """| This method is called and threaded from start_plotting, depending on the selected channels it plots in 1 to 3 graphs.
        | It either works for a Finite amount of time or works infinitely, to make aligning possible.
        | It draws the plot with the time axis, which is the same for all channels,
        | and the Counts, that are a numpy array that is constantly filled with the current Rate.
        | Depending on the channel, the counts are plotted in three different self.draw windows.
        | After the plotting is finished, the prepare_save method is started, so the name to be given to a potential file is set.

        :param Counts: array of the size of the axis length
        :type Counts: numpy array
        """
        self.running = True

        self.Sync_counts_array = np.zeros(int(self.lengthaxis.m_as('s')))
        self.Counts1_array = np.zeros(int(self.lengthaxis.m_as('s')))
        self.Counts2_array = np.zeros(int(self.lengthaxis.m_as('s')))

        if self.exp_type == 'Finite':

            for ii in range(0, int(self.lengthaxis.m_as('s'))):
                if self.running == False:
                    break
                else:
                    if self.sync:
                        curr_sync_Rate = self.sync_counts
                        self.Sync_counts_array[ii] = curr_sync_Rate.m_as('cps')
                        self.logger.debug('Counts: {}'.format(self.Sync_counts_array))

                        self.draw0.counts_plot.plot(self.time_axis, self.Sync_counts_array, clear = True,pen=self.pen)

                    if self.chan1:
                        currRate1 = self.counts1
                        self.Counts1_array[ii] = currRate1.m_as('cps')
                        self.logger.debug('Counts: {}'.format(self.Counts1_array))

                        self.draw1.counts_plot.plot(self.time_axis, self.Counts1_array, clear = True, pen=self.pen)

                    if self.chan2:
                        currRate2 = self.counts2
                        self.Counts2_array[ii] = currRate2.m_as('cps')
                        self.logger.debug('Counts: {}'.format(self.Counts2_array))

                        self.draw2.counts_plot.plot(self.time_axis, self.Counts2_array, clear = True, pen=self.pen)

                    time.sleep(self.pausetime.m_as('s'))

        elif self.exp_type == 'Infinite':
            ii=0
            while self.running:
                if self.sync:
                    curr_sync_Rate = self.sync_counts
                    if ii < int(self.lengthaxis.m_as('s')):
                        self.Sync_counts_array[ii] = curr_sync_Rate.m_as('cps')
                    else:
                        self.Sync_counts_array = np.roll(self.Sync_counts_array, -1)
                        self.Sync_counts_array[-1] = curr_sync_Rate.m_as('cps')
                        self.logger.debug('{}'.format(self.Sync_counts_array))

                    self.draw0.counts_plot.plot(self.time_axis, self.Sync_counts_array, clear=True, pen=self.pen)

                if self.chan1:
                    currRate1 = self.counts1
                    if ii < int(self.lengthaxis.m_as('s')):
                        self.Counts1_array[ii] = currRate1.m_as('cps')
                    else:
                        self.Counts1_array = np.roll(self.Counts1_array, -1)
                        self.Counts1_array[-1] = currRate1.m_as('cps')
                        self.logger.debug('{}'.format(self.Counts1_array))
                    self.draw1.counts_plot.plot(self.time_axis, self.Counts1_array, clear=True, pen=self.pen)

                if self.chan2:
                    currRate2 = self.counts2
                    if ii < int(self.lengthaxis.m_as('s')):
                        self.Counts2_array[ii] = currRate2.m_as('cps')
                    else:
                        self.Counts2_array = np.roll(self.Counts2_array, -1)
                        self.Counts2_array[-1] = currRate2.m_as('cps')
                        self.logger.debug('{}'.format(self.Counts2_array))
                    self.draw2.counts_plot.plot(self.time_axis, self.Counts2_array, clear=True, pen=self.pen)

                ii+=1
                time.sleep(self.pausetime.m_as('s'))

        self.running = False
        self.prepare_save()

    def stop_plotting(self):
        """| Stops the thread and the plotting, if there was actually something running.
        | Does not stop the showing of the counts, that happens no matter what.
        """
        if self.running:
            self.logger.info('Should stop counting here')
            self.running = False

            self.plotting_thread.quit()
        else:
            self.logger.warning('There is nothing to stop.')

    def prepare_save(self):
        """| Enables the save button and prepares for saving by constructing a filename based on the data taken,
        | and filling that name in the input.
        | The data always have 4 columns, some of which might just contain zeros.

        """
        self.gui.pushButton_save.setEnabled(True)

        rowlength = len(self.time_axis)
        self.data = np.zeros([rowlength, 4])  # first column will be time, the others counts on different channels

        self.data[:, 0] = self.time_axis.m_as('s')
        channels = ''

        if self.sync:
            self.data[:, 1] = self.Sync_counts_array
            channels += 'sync_'

        if self.chan1:
            self.data[:, 2] = self.Counts1_array
            channels += 'counts1_'

        if self.chan2:
            self.data[:, 3] = self.Counts2_array
            channels += 'counts2_'

        total_time = int(self.pausetime.m_as('ms') * self.lengthaxis.m_as('s'))

        now = datetime.now()
        datum = str(now.year) + '_' + str(now.month) + '_' + str(now.day) + '_'

        filename = '{}counts_{}time{}ms'.format(datum, channels, total_time)
        self.logger.debug('filename: {}'.format(filename))

        self.default_name = filename
        self.set_name_path()

        self.logger.debug(self.path + filename + '.txt')

    def save_counts(self):
        self.logger.info('Saving the last plot')
        np.savetxt(self.path + self.default_name + '.txt',self.data)

        self.gui.pushButton_save.setEnabled(False)


class DrawCounts(BaseGraph):
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

if __name__ == '__main__':
    import hyperion

    with HydraInstrument(settings={'devidx': 0, 'mode': 'Histogram', 'clock': 'Internal','controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'}) as hydra_instrument:
        app = QApplication(sys.argv)
        ex = Hydraharp_aligning_GUI(hydra_instrument)
        sys.exit(app.exec_())

