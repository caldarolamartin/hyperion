"""
===============
Polarimeter GUI
======================

This is the variable waveplate GUI.



"""

import logging
import sys, os
from PyQt5 import uic
from PyQt5.QtWidgets import *
from hyperion.instrument.polarimeter.polarimeter import Polarimeter
from hyperion import Q_, ur, root_dir
import pyqtgraph as pg

class PolarimeterGui(QWidget):

    MODES = ['Monitor', 'Time Trace'] # measuring modes

    def __init__(self, polarimeter_ins, draw):      # TRYING SOMETHING: added draw, NOTE that this temporarily breaks running this file directly
        """
        Init of the Polarimeter Gui

        :param polarimeter_ins: instrument
        :type an instance of the polarimeter instrument
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.test = QDoubleSpinBox() # to be removed

        # to load from the UI file
        gui_file = os.path.join(root_dir,'view', 'polarimeter','polarimeter.ui')
        self.logger.info('Loading the GUI file: {}'.format(gui_file))
        self.gui = uic.loadUi(gui_file, self)

        self.draw = draw

        # setup the gui
        self.polarimeter_ins = polarimeter_ins
        self.customize_gui()
        #self.get_device_state()
        #self.set_device_state_to_gui()
        self.show()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.logger.debug('Exiting')

    def plot_data(self):        # TRYING SOMETHING: copied and adapted from osa_view
        raw = self.polarimeter_ins.get_multiple_data(10)
        y = [elem[2] for elem in raw]       # this line might be wrong
        x = range(len(y))
        # import random     # alternative test code to see some change
        # y=[]
        # for i in x:
        #     y.append(random.random())
        self.draw.pg_plot.plot(x, y, clear=True)

    def customize_gui(self):
        """ Make changes to the gui """

        self.logger.debug('Setting channels to plot')
        self._channels_labels = []
        self._channels_check_boxes = []

        # add the channels to detect
        for index, a in enumerate(self.polarimeter_ins.DATA_TYPES_NAME):
            label = QLabel(a)
            box = QCheckBox()
            self._channels_labels.append(label)
            self._channels_check_boxes.append(box)

            self.gui.formLayout_channels.addRow(box, label)

        # set the mode
        self.gui.comboBox_mode.addItems(self.MODES)

        self.gui.pushButton_start.pressed.connect(self.plot_data)

        # self.gui.doubleSpinBox_v1.setDecimals(3)
        # self.gui.doubleSpinBox_v1.setSuffix(' V')
        # self.gui.doubleSpinBox_v1.setSingleStep(self.gui.doubleSpinBox_v1_delta.value())
        #
        # self.gui.doubleSpinBox_v1_delta.setDecimals(3)
        # self.gui.doubleSpinBox_v1_delta.setSuffix(' V')
        # self.gui.doubleSpinBox_v1_delta.valueChanged.connect( lambda value: self.gui.doubleSpinBox_v1.setSingleStep(value) )
        #
        # self.gui.doubleSpinBox_v2.setDecimals(3)
        # self.gui.doubleSpinBox_v2.setSuffix(' V')
        # self.gui.doubleSpinBox_v2.setSingleStep(self.gui.doubleSpinBox_v2_delta.value())
        #
        # self.gui.doubleSpinBox_v2_delta.setDecimals(3)
        # self.gui.doubleSpinBox_v2_delta.setSuffix(' V')
        # self.gui.doubleSpinBox_v2_delta.valueChanged.connect(
        #     lambda value: self.gui.doubleSpinBox_v2.setSingleStep(value))
        #
        # self.gui.doubleSpinBox_frequency_delta.valueChanged.connect(
        #     lambda value: self.gui.doubleSpinBox_frequency.setSingleStep(value))
        #
        # self.gui.doubleSpinBox_wavelength_delta.valueChanged.connect(
        #     lambda value: self.gui.doubleSpinBox_wavelength.setSingleStep(value))
        #
        # # combobox
        # self.gui.comboBox_mode.addItems(self.variable_waveplate_ins.MODES)
        # self.gui.comboBox_mode.currentIndexChanged.connect(self.set_channel_textfield_disabled)
        #
        # # enable
        # self.gui.pushButton_state.clicked.connect(self.state_clicked)
        # self.gui.enabled = QWidget()
        #
        # # connect the voltage and frequency spinbox a function to send the
        # self.gui.doubleSpinBox_v1.valueChanged.connect(self.send_voltage_v1)
        # self.gui.doubleSpinBox_v2.valueChanged.connect(self.send_voltage_v2)
        # self.gui.doubleSpinBox_frequency.valueChanged.connect(self.send_frequency_value)
        # self.gui.doubleSpinBox_wavelength.valueChanged.connect(self.send_qwp)


# this is to create a graph output window to dump our data later.
class Graph(QWidget):
    """
    In this class a widget is created to draw a graph on.
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating the Graph for the polarimeter')
        self.title = 'Graph view: Polarimeter'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.pg_plot= pg.PlotWidget()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        vbox.addWidget(self.pg_plot)
        self.setLayout(vbox)
        self.show()



if __name__ == '__main__':
    from hyperion import _logger_format, _logger_settings, root_dir

    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    logging.info('Running Polarimeter GUI file.')
    with Polarimeter(settings = {'dummy' : False,
                                 'controller': 'hyperion.controller.sk.sk_pol_ana/Skpolarimeter',
                                 'dll_name': 'SKPolarimeter'}) as polarimeter_ins:

        app = QApplication(sys.argv)
        logging.debug('Creating the graph for the GUI.')
        graph_window = Graph() # create the plot window


        #app.setWindowIcon(QIcon(path.join(root_dir,'view','gui','vwp_icon.png')))
#        polarimeter_ins.initialize(wavelength=500 * ur('nm'))
        logging.debug('Now starting the GUI')
        PolarimeterGui(polarimeter_ins, draw=graph_window)

        sys.exit(app.exec_())

