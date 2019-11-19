"""
=============
Hydraharp GUI
=============

This is to build a gui for the Hydraharp instrument (correlator).

"""

import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import *
    #QApplication, QWidget, QPushButton, QGridLayout, QLabel, QLineEdit, QComboBox, QVBoxLayout,QFileDialog
from hyperion.instrument.correlator.hydraharp_instrument import HydraInstrument
from hyperion.view.general_worker import WorkThread
from hyperion.view.base_guis import BaseGui
from hyperion import ur, root_dir
import pyqtgraph as pg
import pyqtgraph.exporters
import logging
import numpy as np

class Hydraharp_GUI(BaseGui):
    """
    GUI class for the Hydraharp correlator instrument

    :param hydra_instrument: instrument to control with the GUI
    :type hydra_instrument: instance of the class for the instrument to control
    :param draw: a window where the plotting o the data acquired will be shown.
    :type draw: a plot widget class
    """

    def __init__(self, hydra_instrument, draw):
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
        self.draw = draw

        #default values, could be put in a yml file as well
        self.array_length = 65536
        self.resolution = 1.0*ur('ps')
        self.integration_time = 20 * ur('s')
        self.channel = '0'
        self.remaining_time = self.integration_time     #which also makes sure that the units are the same

        self.max_time = 24*ur('hour')
        self.max_length = 65536

        self.endtime = []
        self.time_axis = []

        self.hydra_instrument.configurate()

        self.initUI()

        #This one is to continuously (= every 100ms) show the remaining time
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_remaining_time)
        self.timer.start(100)       #time in ms

        self.histogram_thread = WorkThread(self.hydra_instrument.make_histogram, self.integration_time, self.channel)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.setAutoFillBackground(True)
        #p = self.palette()
        #p.setColor(self.backgroundRole(), Qt.magenta)
        #p.setStyleSheet("QGroupBox {border: 1px solid magenta;}")

        #self.setPalette(p)

        self.show()

        self.make_buttons()
        self.make_labels()
        self.make_textfields()

    def make_buttons(self):
        self.make_save_histogram_button()
        self.make_take_histogram_button()
        self.make_stop_histogram_button()
    def make_labels(self):
        self.make_array_length_label()
        self.make_resolution_label()
        self.make_integration_time_label()
        self.make_channel_label()
        self.make_export_label()
        self.make_showing_remaining_time()
        self.make_time_axis_label()
        self.make_endtime()
        self.make_progressbar()
    def make_textfields(self):
        self.make_array_length_spinbox()
        self.make_resolution_spinbox()
        self.make_integration_time_spinbox()
        self.make_time_unit_combobox()
        self.make_channel_combobox()
        self.make_export_textfield()
        self.show_remaining_time()

    # ------------------------------------------------------------------------------------
    def make_save_histogram_button(self):
        self.save_histogram_button = QPushButton('save histrogram', self)
        self.save_histogram_button.setToolTip('save your histogram in a file')
        #The maek_save_button should be setEnabled False
        self.save_histogram_button.setEnabled(False)
        self.save_histogram_button.clicked.connect(self.save_histogram)
        self.grid_layout.addWidget(self.save_histogram_button, 5, 4)
    def make_take_histogram_button(self):
        self.take_histogram_button = QPushButton('take histogram', self)
        self.take_histogram_button.setToolTip('take the histogram')
        self.take_histogram_button.clicked.connect(self.take_histogram)
        self.grid_layout.addWidget(self.take_histogram_button, 0, 4)
    def make_stop_histogram_button(self):
        self.stop_histogram_button = QPushButton('stop histogram', self)
        self.stop_histogram_button.setToolTip(('stop your histogram'))
        self.stop_histogram_button.clicked.connect(self.stop_histogram)
        self.grid_layout.addWidget(self.stop_histogram_button, 1, 4)
        self.stop_histogram_button.setStyleSheet("background-color: red")
    def make_array_length_label(self):
        self.array_length_label = QLabel(self)
        self.array_length_label.setText("Array length: ")
        self.grid_layout.addWidget(self.array_length_label, 3, 0)
    def make_resolution_label(self):
        self.resolution_label = QLabel(self)
        self.resolution_label.setText("Resolution: ")
        self.grid_layout.addWidget(self.resolution_label, 1, 0)
    def make_integration_time_label(self):
        self.integration_time_label = QLabel(self)
        self.integration_time_label.setText("Integration time: ")
        self.grid_layout.addWidget(self.integration_time_label, 0, 0)
    def make_channel_label(self):
        self.channel_label = QLabel(self)
        self.channel_label.setText("Channel: ")
        self.grid_layout.addWidget(self.channel_label, 2, 0)
    def make_export_label(self):
        self.export_label = QLabel(self)
        self.export_label.setText("Export file: ")
        self.grid_layout.addWidget(self.export_label, 5, 0)
    def make_showing_remaining_time(self):
        self.showing_remaining_time = QLabel(self)
        self.showing_remaining_time.setText(str(self.remaining_time))
        self.grid_layout.addWidget(self.showing_remaining_time, 3, 4)
    def make_progressbar(self):
        self.progressbar = QProgressBar(self)
        self.progressbar.setMaximum(int(self.integration_time.magnitude))
        self.progressbar.setValue(int(self.remaining_time.magnitude))
        self.progressbar.setTextVisible(False)
        self.progressbar.valueChanged.connect(lambda: self.show_remaining_time)
        self.grid_layout.addWidget(self.progressbar, 4,4)
    def make_time_axis_label(self):
        self.time_axis_label = QLabel(self)
        self.time_axis_label.setText("Time on axis: ")
        self.grid_layout.addWidget(self.time_axis_label, 4, 0)
    def make_endtime(self):
        self.endtime_label = QLabel(self)
        self.calculate_axis()
        self.endtime_label.setText(str(self.endtime))
        self.grid_layout.addWidget(self.endtime_label, 4, 1)

    # ------------------------------------------------------------------------------------
    def make_array_length_spinbox(self):
        self.array_length_spinbox = QSpinBox(self)
        self.array_length_spinbox.setMaximum(999999999)
        self.array_length_spinbox.setValue(self.array_length)
        self.array_length_spinbox.valueChanged.connect(self.set_array_length)
        self.grid_layout.addWidget(self.array_length_spinbox, 3, 1)

    def make_resolution_spinbox(self):
        self.resolution_spinbox = QDoubleSpinBox(self)
        self.resolution_spinbox.setMaximum(999999999)
        self.resolution_spinbox.setValue(self.resolution.m_as('ps'))
        self.resolution_spinbox.setSuffix('ps')
        self.grid_layout.addWidget(self.resolution_spinbox, 1, 1)
        self.resolution_spinbox.valueChanged.connect(self.set_resolution)

    def make_integration_time_spinbox(self):
        self.integration_time_spinbox = QSpinBox(self)
        self.integration_time_spinbox.setValue(self.integration_time.m_as('s'))
        self.grid_layout.addWidget(self.integration_time_spinbox, 0, 1)
        self.integration_time_spinbox.valueChanged.connect(self.set_integration_time)
    def make_time_unit_combobox(self):
        self.time_unit_combobox = QComboBox(self)
        self.time_unit_combobox.addItems(["s","min","hour"])
        self.time_unit_combobox.setCurrentText('s')
        self.grid_layout.addWidget(self.time_unit_combobox, 0, 2)
        self.time_unit_combobox.currentTextChanged.connect(self.set_integration_time)

    def make_channel_combobox(self):
        self.channel_combobox = QComboBox(self)
        self.channel_combobox.addItems(["0","1"])
        self.channel_combobox.setCurrentText(self.channel)
        self.grid_layout.addWidget(self.channel_combobox, 2, 1)
        self.channel_combobox.currentTextChanged.connect(self.set_channel)

    def make_export_textfield(self):
        self.export_textfield = QLineEdit(self)
        self.export_textfield.setText(root_dir)
        self.grid_layout.addWidget(self.export_textfield, 5, 1, 1, 2)


    #------------------------------------------------------------------------------------
    def show_remaining_time(self):
        """This method asks the remaining time from the instrument level,
        and calculates the progress, so both can be displayed.
        """
        self.remaining_time = self.hydra_instrument.remaining_time
        self.showing_remaining_time.setText(str(self.remaining_time))

        self.progressbar.setMaximum(int(self.integration_time.magnitude))
        self.progressbar.setValue(int(self.remaining_time.magnitude))

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
        """| This method tries to take the user input and only allow resolutions from 2^n, where n = 1 to 20.
        | It doesnt work very well though.
        | The resolution is remembered in the init in self.resolution.
        """
        self.logger.info('setting the resolution')

        value = self.sender().value()

        Array = np.zeros(20)
        for ii in range(20):
            Array[ii] = 2**ii

        if value not in Array:
            self.logger.debug('not in A')
            Diff = abs(Array - value)
            index = np.where(Diff == min(Diff))
            index = index[0][0]
            self.sender().setValue(Array[index+1])
            self.logger.debug('new value: ' + str(Array[index+1]))
        else:
            index = np.where(Array == value)
            index = index[0][0]
            self.logger.debug('value: ' + str(Array[index]))

        #self.sender().setValue(Array[index+1])

        self.resolution = self.sender().value()*ur('ps')

        self.calculate_axis()
        self.endtime_label.setText(str(self.endtime))

        self.logger.debug(str(self.sender().value()))

    def calculate_axis(self):
        """| This method calculates the axis that should be put on the graph.
        | **Unused**, because I don't know how to communicate with the graph class.
        """
        self.endtime = round(self.resolution.m_as('ns')*self.array_length*ur('s'),4)

        if self.endtime.m_as('s') < 60:  # below one minute, display in seconds
            units = 's'
        elif self.endtime.m_as('s') < 60 * 60:  # below one hour, display in minutes
            units = 'min'
        elif self.endtime.m_as('s') < 60 * 60 * 24:  # below one day, display in hours
            units = 'hour'
        else:
            units = 'days'

        self.logger.debug(str(self.endtime))
        #self.endtime = self.endtime.m_as(units)
        self.time_axis = np.linspace(0, self.endtime.m_as(units), int(self.resolution.m_as('ns')))

    #------------------------------------------------------------------------------------
    def take_histogram(self):
        """| In this method there will be made a histogram using the input of the user.
        | All user inputs were stored previously in the values as declared in the init
        | (histogram length, resolution, integration time and channel).
        | A thread is started to be able to also stop the histogram taking.
        | The data gets plot in the DrawHistogram plot(self.draw.random_plot.plot()).
        """
        self.logger.info("Take the histrogram")

        self.show_remaining_time()

        #first, set the array length and resolution of the histogram
        self.logger.debug('chosen histogram length: ' + str(self.array_length))
        self.logger.debug('chosen resolution: ' + str(self.resolution))

        self.hydra_instrument.set_histogram(self.array_length, self.resolution)

        #Then, start the histogram + thread
        self.logger.debug('chosen integration time: ' + str(self.integration_time))
        self.logger.debug('chosen channel: ' + str(self.channel))

        self.histogram_thread = WorkThread(self.hydra_instrument.make_histogram, self.integration_time, self.channel)
        self.histogram_thread.start()

        self.histogram = self.hydra_instrument.hist

        while self.hydra_instrument.hist_ended == False:
            self.take_histogram_button.setEnabled(False)

        #self.histogram= self.hydra_instrument.make_histogram(self.integration_time, self.channel)

        self.draw.random_plot.plot(self.histogram, clear=True)

        #make it possible to press the save_histogram_button.(should be True)
        self.save_histogram_button.setEnabled(True)
        self.take_histogram_button.setEnabled(True)
        #self.make_progress_label("Done, the histogram has been made")

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

        self.hydra_instrument.stop = False


class DrawHistogram(QWidget):

    """
    In this class a widget is created to draw a graph on.
    """

    def __init__(self):
        super().__init__()
        self.title = 'draw correlator gui'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.random_plot = pg.PlotWidget()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        vbox.addWidget(self.random_plot)
        self.setLayout(vbox)
        self.show()


if __name__ == '__main__':
    import hyperion

    with HydraInstrument(settings={'devidx': 0, 'mode': 'Histogram', 'clock': 'Internal','controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'}) as hydra_instrument:
        app = QApplication(sys.argv)
        draw = DrawHistogram()
        ex = Hydraharp_GUI(hydra_instrument, draw)
        sys.exit(app.exec_())
