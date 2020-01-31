"""
=============
Hydraharp GUI
=============

This program builds a gui for the Hydraharp instrument (correlator).

"""

import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from hyperion.instrument.correlator.hydraharp_instrument import HydraInstrument
from hyperion.view.general_worker import WorkThread
from hyperion.view.base_guis import BaseGui, BaseGraph, TimeAxisItem
from hyperion import ur, root_dir
import pyqtgraph as pg
import pyqtgraph.exporters
from pyqtgraph.Qt import QtGui
from hyperion import logging
import numpy as np
import matplotlib.pyplot as plt
import time

class Hydraharp_GUI(BaseGui):
    """
    GUI class for the Hydraharp correlator instrument

    :param hydra_instrument: instrument to control with the GUI
    :type hydra_instrument: instance of the class for the instrument to control
    :param draw: a window where the plotting o the data acquired will be shown.
    :type draw: a plot widget class
    """

    def __init__(self, hydra_instrument, draw=None, also_close_output=False):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.title = 'Hydraharp400 correlator gui'
        self.left = 50
        self.top = 50
        self.width = 320
        self.height = 200
        self.histogram_number = 0
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        self.hydra_instrument = hydra_instrument

        if type(draw) is dict:
            self.draw = list(draw.values())[0]
        else:
            self.draw = draw

        #default values, could be put in a yml file as well
        self.array_length = 65536
        self.resolution = "1ps"
        self.integration_time = 5 * ur('s')
        self.channel = '0'
        self.time_passed = 0*ur('s')     #which also makes sure that the units are the same

        self.max_time = 24*ur('hour')
        self.max_length = 65536

        self.endtime = []
        self.time_axis = []
        self.units = 's'

        self.hydra_instrument.configurate()
        self.initUI()

        #This one is to continuously (= every 100ms) show the remaining time
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_time_passed)

        # timer to update
        self.timer_plot = QTimer()
        self.timer_plot.timeout.connect(self.update_plot)

        self.histogram_thread = WorkThread(self.hydra_instrument.make_histogram, self.integration_time, self.channel)

        self.stop = self.stop_histogram

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.show()

        self.make_groupBoxes()
        self.make_basics()
        self.make_user_input()
        self.make_saving_input()

    def make_groupBoxes(self):
        self.groupBox_basic = QGroupBox()
        self.grid_layout.addWidget(self.groupBox_basic,0,1)

        self.groupBox_basic_layout = QVBoxLayout()
        self.groupBox_basic.setLayout(self.groupBox_basic_layout)
        self.groupBox_basic.setStyleSheet("QGroupBox {border: 1px solid orange; border-radius: 9px;}")

        self.groupBox_values = QGroupBox()
        self.grid_layout.addWidget(self.groupBox_values,0,0)

        self.groupBox_values_layout = QGridLayout()
        self.groupBox_values.setLayout(self.groupBox_values_layout)
        self.groupBox_values.setStyleSheet("QGroupBox {border: 1px solid orange; border-radius: 9px;}")

        self.groupBox_saving = QGroupBox()
        self.grid_layout.addWidget(self.groupBox_saving,1,0,1,2)

        self.groupBox_saving_layout = QGridLayout()
        self.groupBox_saving.setLayout(self.groupBox_saving_layout)
        self.groupBox_saving.setStyleSheet("QGroupBox {border: 1px solid orange; border-radius: 9px;}")

    def make_basics(self):
        self.take_histogram_button = QPushButton('take histogram', self)
        self.take_histogram_button.setToolTip('take the histogram')
        self.take_histogram_button.clicked.connect(self.take_histogram)

        self.stop_histogram_button = QPushButton('stop histogram', self)
        self.stop_histogram_button.setToolTip(('stop your histogram'))
        self.stop_histogram_button.clicked.connect(self.stop_histogram)
        self.stop_histogram_button.setStyleSheet("background-color: red")

        self.showing_remaining_time = QLabel(self)
        self.showing_remaining_time.setText(str(self.time_passed))

        self.progressbar = QProgressBar(self)
        self.progressbar.setMaximum(int(self.integration_time.magnitude))
        self.progressbar.setValue(int(self.time_passed.magnitude))
        self.progressbar.setTextVisible(False)
        self.progressbar.valueChanged.connect(lambda: self.show_time_passed)

        self.groupBox_basic_layout.addWidget(self.take_histogram_button)
        self.groupBox_basic_layout.addWidget(self.stop_histogram_button)
        self.groupBox_basic_layout.addWidget(self.showing_remaining_time)
        self.groupBox_basic_layout.addWidget(self.progressbar)

    def make_user_input(self):
        self.integration_time_label = QLabel("Integration time: ")
        self.resolution_label = QLabel("Resolution: ")
        self.channel_label = QLabel("Channel: ")
        self.array_length_label = QLabel("Array length: ")
        self.array_length_label.setEnabled(False)
        self.time_axis_label = QLabel("Time on axis: ")

        self.integration_time_spinbox = QSpinBox(self)
        self.integration_time_spinbox.setValue(self.integration_time.m_as('s'))
        self.integration_time_spinbox.valueChanged.connect(self.set_integration_time)

        self.time_unit_combobox = QComboBox(self)
        self.time_unit_combobox.addItems(["s", "min", "hour"])
        self.time_unit_combobox.setCurrentText('s')
        self.time_unit_combobox.currentTextChanged.connect(self.set_integration_time)

        self.array_length_spinbox = QSpinBox(self)
        self.array_length_spinbox.setMaximum(999999999)
        self.array_length_spinbox.setValue(self.array_length)
        self.array_length_spinbox.setEnabled(False)
        self.array_length_spinbox.valueChanged.connect(self.set_array_length)

        self.resolution_combobox = QComboBox(self)
        #self.resolution_spinbox.setMaximum(999999999)
        #self.resolution_spinbox.setValue(self.resolution.m_as('ps'))
        #self.resolution_spinbox.setSuffix('ps')
        self.resolution_combobox.addItems(["1ps","2ps","4ps","8ps","16ps","32ps","64ps","128ps","256ps","512ps","1024ps"])
        self.resolution_combobox.setCurrentText(self.resolution)
        self.resolution_combobox.currentTextChanged.connect(self.set_resolution)

        self.endtime_label = QLabel(self)
        self.calculate_axis()

        self.channel_combobox = QComboBox(self)
        self.channel_combobox.addItems(["0", "1"])
        self.channel_combobox.setCurrentText(self.channel)
        self.channel_combobox.currentTextChanged.connect(self.set_channel)

        self.groupBox_values_layout.addWidget(self.integration_time_label, 0, 0)
        self.groupBox_values_layout.addWidget(self.resolution_label, 1, 0)
        self.groupBox_values_layout.addWidget(self.channel_label, 2, 0)
        self.groupBox_values_layout.addWidget(self.array_length_label, 3, 0)
        self.groupBox_values_layout.addWidget(self.time_axis_label, 4, 0)

        self.groupBox_values_layout.addWidget(self.integration_time_spinbox, 0, 1)
        self.groupBox_values_layout.addWidget(self.time_unit_combobox, 0, 2)
        self.groupBox_values_layout.addWidget(self.resolution_combobox, 1, 1)
        self.groupBox_values_layout.addWidget(self.channel_combobox, 2, 1)
        self.groupBox_values_layout.addWidget(self.array_length_spinbox, 3, 1)
        self.groupBox_values_layout.addWidget(self.endtime_label, 4, 1)

    def make_saving_input(self):
        self.export_label = QLabel("Export file: ")

        self.save_histogram_button = QPushButton('save histrogram', self)
        self.save_histogram_button.setToolTip('save your histogram in a file')
        self.save_histogram_button.setEnabled(False)
        self.save_histogram_button.clicked.connect(self.save_histogram)

        self.export_textfield = QLineEdit(self)
        self.export_textfield.setText(root_dir)

        self.groupBox_saving_layout.addWidget(self.export_label, 0, 0)
        self.groupBox_saving_layout.addWidget(self.save_histogram_button, 0, 3)  # 5,4
        self.groupBox_saving_layout.addWidget(self.export_textfield, 0, 1, 1, 2)

    #------------------------------------------------------------------------------------
    def show_time_passed(self):
        """This method asks the remaining time from the instrument level,
        and calculates the progress, so both can be displayed.
        """
        self.time_passed = self.hydra_instrument.time_passed
        self.showing_remaining_time.setText(str(self.time_passed))

        self.progressbar.setMaximum(int(self.integration_time.magnitude))
        self.progressbar.setValue(int(self.time_passed.magnitude))
        #print(self.hydra_instrument.remaining_time)

    # ------------------------------------------------------------------------------------
    def set_channel(self):
        """ This method sets the channel that the user puts, and remembers the string in the init in self.channel.
        """
        self.logger.info('setting the channel')

        self.channel = self.channel_combobox.currentText()
        self.logger.debug('channel: ' + self.channel)

    def set_array_length(self):
        """This method sets the array length that the user puts,
        and remembers the int in the init in self.array_length.
        It compares it to a max and min value.
        """
        self.logger.info('setting the array length')
        self.logger.warning('are you sure you want to change this value?')

        if self.sender().value() > self.max_length:
            self.sender().setValue(self.max_length)
        elif self.sender().value() < 1:
            self.sender().setValue(1)

        self.calculate_axis()
        self.endtime_label.setText(str(self.endtime))

        self.array_length = int(self.sender().value())

    def set_integration_time(self):
        """This method combines the integration time that the user puts in the spinbox with the unit in the combobox,
        and remembers the pint quantity in the init in self.integration_time.
        It compares it to a max (24 hours) and min (1 s) value.
        """
        self.logger.info('setting the integration time')

        tijd = self.integration_time_spinbox.value()
        unit = self.time_unit_combobox.currentText()

        local_time = ur(str(tijd)+unit)

        self.logger.debug('local time value: ' + str(local_time))

        if local_time > self.max_time:
            self.logger.debug('time really too much')
            local_time = self.max_time.to(unit)
            self.logger.debug(str(local_time))
            self.integration_time_spinbox.setValue(local_time.m_as(unit))
        elif local_time < 1*ur('s'):
            self.logger.debug('you need to integrate more time')
            local_time = 1*ur('s')
            self.integration_time_spinbox.setValue(local_time.m_as('s'))

        self.integration_time = local_time
        self.logger.debug('time remembered is: ' + str(self.integration_time))

    def set_resolution(self):
        """| This method takes the chosen resolution by the user and remembers it for the rest of this class.
        | It would be cool if I could make it a spinbox, that only allows values of 2^n, but I couldnt make that work...
        """
        self.logger.info('setting the resolution')

        self.resolution = self.resolution_combobox.currentText()
        self.logger.debug('resolution: ' + self.resolution)

        self.calculate_axis()
        #
        # value = self.sender().value()
        #
        # Array = np.zeros(20)
        # for ii in range(20):
        #     Array[ii] = 2**ii
        #
        # if value not in Array:
        #     self.logger.debug('not in A')
        #     Diff = abs(Array - value)
        #     index = np.where(Diff == min(Diff))
        #     index = index[0][0]
        #     self.sender().setValue(Array[index+1])
        #     self.logger.debug('new value: ' + str(Array[index+1]))
        # else:
        #     index = np.where(Array == value)
        #     index = index[0][0]
        #     self.logger.debug('value: ' + str(Array[index]))
        #
        # #self.sender().setValue(Array[index+1])
        #
        # self.resolution = self.sender().value()*ur('ps')
        #
        #
        # self.endtime_label.setText(str(round(self.endtime.to(self.units), 4)))
        #
        # self.logger.debug(str(self.sender().value()))

    def calculate_axis(self):
        """| This method calculates the axis that should be put on the graph.
        | This end time is both displayed in the gui and used for the graph time axis.
        """
        self.endtime = round(ur(self.resolution).m_as('ns')*self.array_length*ur('s'),4)

        if self.endtime.m_as('s') < 120:  # below two minutes, display in seconds
            self.units = 's'
        elif self.endtime.m_as('s') < 120 * 60:  # below two hours, display in minutes
            self.units = 'min'
        elif self.endtime.m_as('s') < 120 * 60 * 24:  # below two days, display in hours
            self.units = 'hour'
        else:
            self.units = 'days'

        self.endtime_label.setText(str(round(self.endtime.to(self.units), 4)))

        #self.logger.debug('endtime: {}, units: {}, array length: {}'.format(self.endtime, self.units, self.array_length))
        self.time_axis = np.linspace(0, float(self.endtime.m_as(self.units)), self.array_length)
        #self.logger.debug('time axis: {}'.format(self.time_axis))

    #------------------------------------------------------------------------------------
    def take_histogram(self):
        """| In this method there will be made a histogram using the input of the user.
        | All user inputs were stored previously in the values as declared in the init
        | (histogram length, resolution, integration time and channel).
        | A thread is started to be able to also stop the histogram taking.
        | The data gets plot in the DrawHistogram plot(self.draw.histogram_plot.plot()).
        | The time axis is calculated in calculate_axis and used for the plot.
        """
        self.logger.info("Take the histrogram")

        #first, set the array length and resolution of the histogram
        self.logger.debug('chosen histogram length: ' + str(self.array_length))
        self.logger.debug('chosen resolution: ' + str(self.resolution))

        self.hydra_instrument.set_histogram(self.array_length, ur(self.resolution))

        #Then, start the histogram + thread
        self.logger.debug('chosen integration time: ' + str(self.integration_time))
        self.logger.debug('chosen channel: ' + str(self.channel))

        self.timer.start(100)
        self.timer_plot.start(100)
        self.show_time_passed()
        self.histogram_thread = WorkThread(self.hydra_instrument.make_histogram, self.integration_time, self.channel)
        self.histogram_thread.start()

        #make it possible to press the save_histogram_button.(should be True)
        self.save_histogram_button.setEnabled(True)
        self.take_histogram_button.setEnabled(True)

        self.hydra_instrument.time_passed = 0*ur('s')
        self.show_time_passed()

    def update_plot(self):
        pen = pg.mkPen(color=(0, 0, 0))  # makes the plotted lines black
        if self.hydra_instrument.hist_ended:
            self.take_histogram_button.setEnabled(True)
            self.timer_plot.stop()
            self.timer.stop()
            self.histogram = self.hydra_instrument.hist
            self.calculate_axis()
            self.draw.histogram_plot.plot(self.time_axis, self.histogram, clear=True, pen=pen)
            self.draw.histogram_plot.setLabel('bottom',
                                              "<span style=\"color:black;font-size:20px\"> Time ({}) </span>".format(
                                                  self.units))

        else:
            self.take_histogram_button.setEnabled(False)
            self.histogram = self.hydra_instrument.hist

            self.calculate_axis()
            self.logger.debug(
            'length time axis: {}, length histogram: {}'.format(len(self.time_axis), len(self.histogram)))

            if len(self.histogram) > 0:
                self.draw.histogram_plot.plot(self.time_axis, self.histogram, clear=True)
                self.draw.histogram_plot.setLabel('bottom', "<span style=\"color:black;font-size:20px\"> Time ({}) </span>".format(self.units))

    def save_histogram(self):
        """| In this method the made histogram gets saved.
        | This is done with pyqtgraph.exporters. The width and height can be set of the picture below.
        """
        self.logger.info('saving the histogram')
        try:
            plt = pg.plot(self.histogram)
            exporter = pg.exporters.ImageExporter(plt.plotItem)
            # set export parameters if needed
            exporter.parameters()['height'] = 100  # (note this also affects width parameter)
            exporter.parameters()['width'] = 100  # (note this also affects height parameter)
            self.actually_save_histogram(exporter)
            #there must first be made another(or the same) histogram before this method can be accessed.(should be False)
            self.save_histogram_button.setEnabled(False)
            plt.close()
        except Exception:
            self.logger.warning("There is no picture to export...change that by clicking the button above")

    def actually_save_histogram(self, exporter):
        """|  In this method it is defined what the file_name is via checking if there is text in the export textfield.
        |If there is none, than a file_chooser will be used to have a location where the .png's will be saved.

        :param exporter: A exporter object with which you can save data
        :type exporter: pyqtgraph.exporter, doesn't say that much, I know
        """

        if self.export_textfield.text() != "":
            # save to file via the textfield
            file_name = self.export_textfield.text() + "\\histogram_"+str(self.histogram_number)+".png"
            self.histogram_number += 1
            exporter.export(file_name)
        else:
            #a file chooser will be used
            file_name = self.get_file_path_via_filechooser()
            exporter.export(file_name)
        #self.make_progress_label.setText("The histogram has been saved at: \n" + str(file_name))

    def get_file_path_via_filechooser(self):
        """| This is code plucked from the internet...so I have no clou what is happening and that is fine really.
        | If the code breaks, go to: https://pythonspot.com/pyqt5-file-dialog/

        :return: the filepath, .png needs to be attached in order to save the picture as a...picture
        :rtype: string
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "All Files (*);;Text Files (*.txt)", options=options)
        return fileName + ".png"

    def stop_histogram(self):
        """| Here the self.hydra_instrument.stop is set to True, which means the while loop in the instrument breaks.
        | Afterwards, the hydraharp itself is actually set to stop.
        | To avoid errors, it is important to quit the thread.
        """
        self.logger.info('Histogram should stop here')
        self.hydra_instrument.stop = True
        self.hydra_instrument.stop_histogram()

        if self.histogram_thread.isRunning:
            self.logger.debug('histogram thread was running')
            self.histogram_thread.quit()

        self.hydra_instrument.time_passed = 0*ur('s')
        self.show_time_passed()
        self.hydra_instrument.stop = False

class DrawHistogram(pg.PlotWidget):
    """This will make a graph for the histogram.
    Since it is a pg.PlotWidget, it can be used both by the Hydraharp_GUI and by the ExpGUI (mastergui) outside of hyperion.
    The title and labels are already set, as is the layout. The units on the x-axis are changed in update plot, since they depend on the chosen resolution.
    """

    def __init__(self):
        super().__init__()
        self.histogram_plot = self
        self.initUI()

    def initUI(self):
        self.layout_plot()

    def layout_plot(self):
        self.histogram_plot.setBackground('w')
        self.histogram_plot.setTitle("<span style=\"color:orange;font-size:30px\">Histogram</span>")
        #self.histogram_plot.setTitle("Histogram", color=(255,0,0))
        #self.histogram_plot.setLabel('left','Correlated counts','a.u.')

        Xaxis = TimeAxisItem(orientation = 'bottom')
        Xaxis.attachToPlotItem(self.histogram_plot.getPlotItem())
        Xaxis.setPen(color = (0,0,0))

        Yaxis = TimeAxisItem(orientation = 'left')
        Yaxis.attachToPlotItem(self.histogram_plot.getPlotItem())
        Yaxis.setPen(color = (0,0,0))

        self.histogram_plot.setLabel('left', "<span style=\"color:black;font-size:20px\"> Correlated counts </span>")
        self.histogram_plot.setLabel('bottom', "<span style=\"color:black;font-size:20px\"> Time </span>")

        font = QtGui.QFont()
        font.setPixelSize(20)
        self.histogram_plot.getAxis("bottom").tickFont = font
        self.histogram_plot.getAxis("left").tickFont = font


if __name__ == '__main__':
    import hyperion

    with HydraInstrument(settings={'devidx': 0, 'mode': 'Histogram', 'clock': 'Internal','controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'}) as hydra_instrument:
        app = QApplication(sys.argv)
        draw = DrawHistogram()
        draw.show()
        ex = Hydraharp_GUI(hydra_instrument, draw)
        sys.exit(app.exec_())
