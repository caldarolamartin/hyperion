"""
    ===============
    Polarimeter GUI
    ===============

    This is the variable waveplate GUI.

    :copyright: 2019 by Hyperion Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import logging
import sys, os
import numpy as np
import pyqtgraph as pg
from time import time
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import *
import hyperion
from hyperion import root_dir, _colors, Q_
from hyperion.instrument.polarization.polarimeter import Polarimeter
from hyperion.view.base_plot_windows import BaseGraph

class PolarimeterGui(QWidget):
    """
        This is the Polarimeter GUI class.
        It builds the GUI for the instrument: polarimeter

        :param polarimeter_ins: instrument
        :type an instance of the polarization instrument
    """

    MODES = ['Monitor', 'Time Trace'] # measuring modes

    def __init__(self, polarimeter_ins, plot_window):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # to load from the UI file
        gui_file = os.path.join(root_dir,'view', 'polarization','polarimeter.ui')
        self.logger.info('Loading the GUI file: {}'.format(gui_file))
        self.gui = uic.loadUi(gui_file, self)
        # set location in screen
        self.left = 700
        self.top = 100
        # change location
        self.gui.move(self.left, self.top)

        self.plot_window = plot_window


        # setup the gui
        self.polarimeter_ins = polarimeter_ins
        self.customize_gui()
        #self.get_device_state()
        #self.set_device_state_to_gui()
        self.show()

        #
        self._is_measuring = False
        # data vector creation
        self._buffer_size_factor = 20
        self.data = np.zeros((len(self.polarimeter_ins.DATA_TYPES_NAME),
                              int(self.gui.doubleSpinBox_measurement_length.value()*self._buffer_size_factor)))   # length of the buffer
        self.data_time = np.zeros((int(self.gui.doubleSpinBox_measurement_length.value()*self._buffer_size_factor)))  # length of the buffer
        # to handle the update of the plot we use a timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        # to be able to plot only the ticked fields
        self.index_to_plot = []
        self.Plots = []
        self.Plots.append(self.plot_window.pg_plot)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.logger.debug('Exiting the with')

    def closeEvent(self, event):
        """ Actions to take when you press the X in the main window.

        """
        self.polarimeter_ins.finalize()
        self.plot_window.close()
        event.accept() # let the window close

    def customize_gui(self):
        """ Make changes to the gui """
        self.setWindowIcon(QIcon(os.path.join(root_dir, 'view', 'logo_hyperion.png')))
        self.logger.debug('Setting channels to plot')
        self._channels_labels = []
        self._channels_check_boxes = []

        self.gui.pushButton_apply_wavelength.clicked.connect(self.change_wavelength)

        # add the channels to detect
        for index, a in enumerate(self.polarimeter_ins.DATA_TYPES_NAME):
            label = QLabel(a)
            label.setStyleSheet('color: {}'.format(_colors[index]))
            box = QCheckBox()
            self._channels_labels.append(label)
            self._channels_check_boxes.append(box)
            self.gui.formLayout_channels.addRow(box, label)
            self._channels_check_boxes[-1].stateChanged.connect(self.update_start_button_status)

        # set the mode
        self.gui.comboBox_mode.addItems(self.MODES)
        # clear plot
        self.gui.pushButton_clear_plot.clicked.connect(self.clear_plot)
        # save
        self.gui.pushButton_save.clicked.connect(self.data_save)
        # start monitor button
        self.gui.pushButton_start.clicked.connect(self.start_button)
        self.gui.pushButton_start.setEnabled(False)



    def update_dummy_data(self):
        """ Dummy data update"""
        raw = np.random.rand(13)
        self.data[:, :-1] = self.data[:, 1:]
        self.data[:, -1] = np.array(raw)

    def update_data(self):
        """ Getting data from polarimeter and put it in the matrix self.data (gets all the posible values)

        """
        raw = self.polarimeter_ins.get_data()
        t = time()
        # shift data
        self.data[:,1:] =self.data[:,0:-1]
        self.data_time[1:] = self.data_time[0:-1]
        # add new data
        self.data[:,0] = np.array(raw)
        self.data_time[0] = t - self.stat_time
        # self.logger.debug('Time vector: {}'.format(self.data_time))
        # self.logger.debug('Data vector S1: {}'.format(self.data[0,:]))

    def update_plot(self):
        """ This updates the plot """
        self.update_data() # get new data
        # self.logger.debug('Indexes selected to plot: {}'.format(self.index_to_plot))

        # make data to plot
        x = np.array(range(len(self.data[0,:])))
        # Update the data shown in all the plots that are checked
        for index, value in enumerate(self.index_to_plot):
            #self.logger.debug('Plotting for variable: {}'.format(self.polarimeter_ins.DATA_TYPES_NAME[value]))
            y = self.data[value, :]
            self.Plots[index].setData(self.data_time, y, pen=pg.mkPen(_colors[value], width=2))

        self.plot_window.pg_plot_widget.setXRange(self.data_time[0]-self.gui.doubleSpinBox_measurement_length.value(),
                                                  self.data_time[0])

    def data_save(self):
        """ To save data in memory """
        self.polarimeter_ins.save_data(self.data, file_path='test.txt')


    def clear_plot(self):
        """To clear the plot"""
        self.plot_window.pg_plot_widget.clear()

    def update_start_button_status(self):
        """To make the start button be disabled or enabled depending on the checkbox status. """

        self.logger.debug('Updating start button and making the initial plot.')
        # get the index number of the channels ticked to be measured and put them in an array
        self.index_to_plot = []
        label = ''
        for ind, a in enumerate(self._channels_check_boxes):
            if a.isChecked():
                self.index_to_plot.append(ind)
                label += '{} [{}], '.format(self.polarimeter_ins.DATA_TYPES_NAME[ind],
                                            self.polarimeter_ins.DATA_TYPES_UNITS[ind])
        self.logger.debug('Total set of index to plot in the monitor: {}'.format(self.index_to_plot))
        self.plot_window.pg_plot_widget.setLabel('left', label[:-2])
        self.logger.debug('Setting the right range for the plot: {}'.format(self.gui.doubleSpinBox_measurement_length.value()))
        self.plot_window.pg_plot_widget.setXRange(self.data_time[0]-self.gui.doubleSpinBox_measurement_length.value(),
                                                  self.data_time[0])

        if len(self.index_to_plot)==0:
            self.gui.pushButton_start.setEnabled(False)
        else:
            self.gui.pushButton_start.setEnabled(True)

    def start_button(self):
        """ Action when you press start """

        # add the extra plots needed with one data point
        self.Plots = []
        for i in range(len(self.index_to_plot)):
            self.logger.debug('Adding a new plot. Index: {}'.format(i))
            p = self.plot_window.pg_plot_widget.plot([0], [0])
            self.Plots.append(p)
        #lenth = self.gui.doubleSpinBox_measurement_length
        if self._is_measuring:
            self.logger.debug('Stopping sweep')
            self._is_measuring = False
            # change the button text
            self.gui.pushButton_start.setText('Start')
            # Enable the checkboxes when stopping
            for a in self._channels_check_boxes:
                a.setEnabled(True)

            self.timer.stop()

        else:
            self.logger.debug('Re-setting to zero the data')
            # create the data set
            self.data = np.zeros((len(self.polarimeter_ins.DATA_TYPES_NAME),
                                  int(
                                      self.gui.doubleSpinBox_measurement_length.value() * self._buffer_size_factor)))  # length of the buffer
            self.data_time = np.zeros((int(
                self.gui.doubleSpinBox_measurement_length.value() * self._buffer_size_factor)))  # length of the buffer

            self.stat_time = time()  #
            self.logger.debug('Starting measurement')
            self._is_measuring = True
            # change the button text
            self.gui.pushButton_start.setText('Stop')
            # Disable the checkboxes while running
            for a in self._channels_check_boxes:
                a.setEnabled(False)

            self.timer.start(50)  # in ms
            # self.measurement_thread = WorkThread(self.continuous_data)
            # self.measurement_thread.start()

    def change_wavelength(self):
        """ Gui method to set the wavelength to the device

        """
        w = Q_(self.doubleSpinBox_wavelength.value(), self.doubleSpinBox_wavelength.suffix())
        self.logger.info('Setting the wavelength: {}'.format(w))
        self.polarimeter_ins.change_wavelength(w)

# this is to create a graph output window to dump our data later.
class Graph(BaseGraph):
    """
    In this class a widget is created to draw a graph on.
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating the Graph for the polarization')
        self.title = 'Graph view: Polarimeter'
        self.left = 50
        self.top = 100
        self.width = 640
        self.height = 480

        self.plot_title = 'Data from SK polarimeter'
        self.initialize_plot()
        #self.pg_plot_widget.setYRange(min=-1,max=1)
        self.pg_plot_widget.setLabel('bottom',text='Time', units='seconds')

        self.initUI()       # This should be called here (not in the parent)

if __name__ == '__main__':
    import hyperion
    hyperion.file_logger.setLevel( logging.DEBUG )
    hyperion.stream_logger.setLevel( logging.INFO )

    logging.info('Running Polarimeter GUI file.')

    # Create the Instrument (in this case we use the with statement)
    with Polarimeter(settings = {'dummy' : False,
                                 'controller': 'hyperion.controller.sk.sk_pol_ana/Skpolarimeter',
                                 'dll_name': 'SKPolarimeter'}) as polarimeter_ins:
        # Mandatory line for gui
        app = QApplication(sys.argv)

        logging.debug('Creating the graph for the GUI.')
        plot_window = Graph()

        logging.debug('Now starting the GUI')
        PolarimeterGui(polarimeter_ins, plot_window)

        # Mandatory line for gui
        # app.exec_()               # if you don't want it to close the python kernel afterwards
        sys.exit(app.exec_())       # if you do want it to close the python kernal afterwards

