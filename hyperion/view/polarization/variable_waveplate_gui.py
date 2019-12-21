"""
======================
Variable waveplate GUI
======================

This is the variable waveplate GUI.



"""
from hyperion import logging
import sys, os
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QDoubleSpinBox
from hyperion.instrument.polarization.variable_waveplate import VariableWaveplate
from hyperion import Q_


#todo checkout if the device is on the computer if this class can work with the variablewaveplate/lcc25


class VariableWaveplateGui(QWidget):

    def __init__(self, variable_waveplate_ins):
        """
        Init of the VariableWaveplateGui

        :param variable_waveplate_ins: instrument
        :type an instance of the variable_waveplate instrument
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.test = QDoubleSpinBox() # to be removed


        # to load from the UI file
        gui_file = os.path.join(root_dir,'view', 'polarization','variable_waveplate_instrument.ui')
        self.logger.info('Loading the GUI file: {}'.format(gui_file))
        self.gui = uic.loadUi(gui_file, self)
        # define internal variables to update the GUI
        self._output = None
        self._mode = None
        self._analog_value_1 = None
        self._analog_value_2 = None

        # setup the gui
        self.variable_waveplate_ins = variable_waveplate_ins
        self.customize_gui()
        self.get_device_state()
        self.set_device_state_to_gui()
        self.show()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.logger.debug('Exiting')

    def customize_gui(self):
        """ Make changes to the gui """
        self.logger.debug('Setting Voltage spinboxes settings')
        self.gui.doubleSpinBox_v1.setDecimals(3)
        self.gui.doubleSpinBox_v1.setSuffix(' V')
        self.gui.doubleSpinBox_v1.setSingleStep(self.gui.doubleSpinBox_v1_delta.value())

        self.gui.doubleSpinBox_v1_delta.setDecimals(3)
        self.gui.doubleSpinBox_v1_delta.setSuffix(' V')
        self.gui.doubleSpinBox_v1_delta.valueChanged.connect( lambda value: self.gui.doubleSpinBox_v1.setSingleStep(value) )

        self.gui.doubleSpinBox_v2.setDecimals(3)
        self.gui.doubleSpinBox_v2.setSuffix(' V')
        self.gui.doubleSpinBox_v2.setSingleStep(self.gui.doubleSpinBox_v2_delta.value())

        self.gui.doubleSpinBox_v2_delta.setDecimals(3)
        self.gui.doubleSpinBox_v2_delta.setSuffix(' V')
        self.gui.doubleSpinBox_v2_delta.valueChanged.connect(
            lambda value: self.gui.doubleSpinBox_v2.setSingleStep(value))

        self.gui.doubleSpinBox_frequency_delta.valueChanged.connect(
            lambda value: self.gui.doubleSpinBox_frequency.setSingleStep(value))

        self.gui.doubleSpinBox_wavelength_delta.valueChanged.connect(
            lambda value: self.gui.doubleSpinBox_wavelength.setSingleStep(value))

        # combobox
        self.gui.comboBox_mode.addItems(self.variable_waveplate_ins.MODES)
        self.gui.comboBox_mode.currentIndexChanged.connect(self.set_channel_textfield_disabled)

        # enable
        self.gui.pushButton_state.clicked.connect(self.state_clicked)
        self.gui.enabled = QWidget()

        # connect the voltage and frequency spinbox a function to send the
        self.gui.doubleSpinBox_v1.valueChanged.connect(self.send_voltage_v1)
        self.gui.doubleSpinBox_v2.valueChanged.connect(self.send_voltage_v2)
        self.gui.doubleSpinBox_frequency.valueChanged.connect(self.send_frequency_value)
        self.gui.doubleSpinBox_wavelength.valueChanged.connect(self.send_qwp)

    def send_voltage_v1(self, value):
        """ Sets the voltage 1 to the device"""
        self.variable_waveplate_ins.set_analog_value(1, Q_(value, self.gui.doubleSpinBox_v1.suffix()))

    def send_voltage_v2(self, value):
        """ Sets the voltage 2 to the device"""
        self.variable_waveplate_ins.set_analog_value(2, Q_(value, self.gui.doubleSpinBox_v2.suffix()))

    def send_frequency_value(self, value):
        """Gets the value from the spinbox in the gui and sends it to the device """
        freq = Q_(value, self.gui.doubleSpinBox_frequency.suffix())
        self.logger.debug('Frequency to set: {}'.format(freq))

        if freq.m_as('Hz') != self.variable_waveplate_ins._freq.m_as('Hz'):
            self.variable_waveplate_ins.freq = freq

    def send_qwp(self, value):
        """ Sets the QWP wavelength to the device"""
        self.variable_waveplate_ins.set_quarter_waveplate_voltage(Q_(value, self.gui.doubleSpinBox_wavelength.suffix()))
        self._analog_value_1 = self.variable_waveplate_ins.get_analog_value(1)
        self.gui.doubleSpinBox_v1.setValue(self._analog_value_1.m_as('volt'))

    def get_device_state(self):
        """ Gets the state for all the settings form the device """
        self._output = self.variable_waveplate_ins.output
        self._mode = self.variable_waveplate_ins.mode
        self._analog_value_1 = self.variable_waveplate_ins.get_analog_value(1)
        self._analog_value_2 = self.variable_waveplate_ins.get_analog_value(2)

    def set_device_state_to_gui(self):
        """ Sets the device state to the GUI """
        self.state_clicked(self._output)
        self.gui.pushButton_state.setChecked(self._output)
        self.gui.doubleSpinBox_v1.setValue(self._analog_value_1.m_as('volt'))
        self.gui.doubleSpinBox_v2.setValue(self._analog_value_2.m_as('volt'))
        self.gui.doubleSpinBox_frequency.setValue(self.variable_waveplate_ins.freq.m_as('Hz'))
        self.gui.comboBox_mode.setCurrentIndex(self.variable_waveplate_ins.MODES.index(self.variable_waveplate_ins.mode))
        self.gui.doubleSpinBox_wavelength.setValue(self.variable_waveplate_ins._wavelength.m_as('nm'))

    def state_clicked(self, state):
        """ Enable output"""
        self.logger.debug('Send the state to the device')
        self.variable_waveplate_ins.output = state
        self._output = state
        self.logger.debug('Changing apearence of the button')
        self.gui.pushButton_state.setText(['Disabled','Enabled'][state])
        self.gui.pushButton_state.setStyleSheet("background-color: "+['red','green'][state])
        return state

    def change_step_v1(self, v, obj):
        self.gui.doubleSpinBox_v1.setDecimals(3)

    def set_channel_textfield_disabled(self, v):
        """
        if the mode is Voltage1 then it is not possible to
        write something in textbox of Voltage 2 or the others
        """
        if self.gui.comboBox_mode.currentText() == "Voltage1":
            self.gui.doubleSpinBox_v1.setEnabled(True)
            self.gui.doubleSpinBox_v1_delta.setEnabled(True)
            self.gui.doubleSpinBox_v2.setEnabled(False)
            self.gui.doubleSpinBox_v2_delta.setEnabled(False)
            self.gui.doubleSpinBox_frequency.setEnabled(False)
            self.gui.doubleSpinBox_frequency_delta.setEnabled(False)
            self.gui.doubleSpinBox_wavelength.setEnabled(False)
            self.gui.doubleSpinBox_wavelength_delta.setEnabled(False)

        elif self.gui.comboBox_mode.currentText() == "Voltage2":
            self.gui.doubleSpinBox_v1.setEnabled(False)
            self.gui.doubleSpinBox_v1_delta.setEnabled(False)
            self.gui.doubleSpinBox_v2.setEnabled(True)
            self.gui.doubleSpinBox_v2_delta.setEnabled(True)
            self.gui.doubleSpinBox_frequency.setEnabled(False)
            self.gui.doubleSpinBox_frequency_delta.setEnabled(False)
            self.gui.doubleSpinBox_wavelength.setEnabled(False)
            self.gui.doubleSpinBox_wavelength_delta.setEnabled(False)

        elif self.gui.comboBox_mode.currentText() == "Modulation":
            self.gui.doubleSpinBox_v1.setEnabled(True)
            self.gui.doubleSpinBox_v1_delta.setEnabled(True)
            self.gui.doubleSpinBox_v2.setEnabled(True)
            self.gui.doubleSpinBox_v2_delta.setEnabled(True)
            self.gui.doubleSpinBox_frequency.setEnabled(True)
            self.gui.doubleSpinBox_frequency_delta.setEnabled(True)
            self.gui.doubleSpinBox_wavelength.setEnabled(False)
            self.gui.doubleSpinBox_wavelength_delta.setEnabled(False)


        elif self.gui.comboBox_mode.currentText() == "QWP":
            self.gui.doubleSpinBox_v1.setEnabled(False)
            self.gui.doubleSpinBox_v1_delta.setEnabled(False)
            self.gui.doubleSpinBox_v2.setEnabled(False)
            self.gui.doubleSpinBox_v2_delta.setEnabled(False)
            self.gui.doubleSpinBox_frequency.setEnabled(False)
            self.gui.doubleSpinBox_frequency_delta.setEnabled(False)
            self.gui.doubleSpinBox_wavelength.setEnabled(True)
            self.gui.doubleSpinBox_wavelength_delta.setEnabled(True)


if __name__ == '__main__':
    from hyperion import root_dir
    from os import path
    log = logging.getLogger(__name__)

    log.info('Running vairable waveplate GUI file.')
    with VariableWaveplate(settings = {'port':'COM8', 'enable': False, 'dummy' : False,
                                       'controller': 'hyperion.controller.thorlabs.lcc25/Lcc'}) as variable_waveplate_ins:

        # variable_waveplate_ins.initialize() this should already happen in the __init__
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(path.join(root_dir,'view','polarization','vwp_icon.png')))
        with VariableWaveplateGui(variable_waveplate_ins) as GUI:
            print('hello')

        sys.exit(app.exec_())


