"""
======================
Variable waveplate GUI
======================

This is the variable waveplate GUI.



"""

import logging
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QColor, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QComboBox, QLabel, QLineEdit
from hyperion.instrument.variable_waveplate.variable_waveplate import VariableWaveplate
from hyperion import Q_, ur

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
        self.title = 'LCC25 variable waveplate instrument (GUI)'
        self.left = 10
        self.top = 60
        self.width = 850
        self.height = 250
        self.variable_waveplate_ins = variable_waveplate_ins
        self.initUI()

    def set_gui_specifics(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

    def initUI(self):
        """ Initializes the gui elements """
        self.set_gui_specifics()
        self.set_elements_in_gui()
        self.show()

    def set_elements_in_gui(self):
        self.set_labels()
        self.set_textfields()
        self.set_miscelanious_gui_stuff()

    def set_labels(self):
        self.set_mode_label()
        self.set_voltage_1_label()
        self.set_voltage_2_label()
        self.set_quater_waveplate_label()
        self.set_frequency_label()
        self.set_output_label()

    def set_textfields(self):
        self.set_voltage_1_textfield()
        self.set_voltage_2_textfield()
        self.set_quater_waveplate_textfield()
        self.set_frequency_textfield()

    def set_miscelanious_gui_stuff(self):
        self.set_mode_combobox()
        self.set_submit_button()
        self.set_output_dropdown()

    def set_frequency_label(self):
        self.frequency_label = QLabel(self)
        self.frequency_label.setText("Freq in Hz:")
        self.grid_layout.addWidget(self.frequency_label, 0, 2)

    def set_quater_waveplate_label(self):
        self.quater_waveplate_label = QLabel(self)
        self.quater_waveplate_label.setText("Wavelength for \n Quarter-wave plate:")
        self.grid_layout.addWidget(self.quater_waveplate_label, 3, 0)

    def set_voltage_2_label(self):
        self.voltage_2_label = QLabel(self)
        self.voltage_2_label.setText("V2, in (0, 25) V:")
        self.grid_layout.addWidget(self.voltage_2_label, 2, 0)

    def set_voltage_1_label(self):
        self.voltage_1_label = QLabel(self)
        self.voltage_1_label.setText("V1, in (0,25) V:")
        self.grid_layout.addWidget(self.voltage_1_label, 1, 0)

    def set_mode_label(self):
        self.mode_label = QLabel(self)
        self.mode_label.setText("mode:")
        self.grid_layout.addWidget(self.mode_label, 0, 0)

    def set_output_label(self):
        self.output_label = QLabel(self)
        self.output_label.setText("output:")
        self.grid_layout.addWidget(self.output_label, 1, 2)

    def set_frequency_textfield(self):
        self.frequency_textfield = QLineEdit(self)
        self.frequency_textfield.setText(str(self.variable_waveplate_ins.controller.freq))
        self.grid_layout.addWidget(self.frequency_textfield, 0, 3)

    def set_quater_waveplate_textfield(self):
        self.quater_waveplate_textfield = QLineEdit(self)
        self.quater_waveplate_textfield.setText(str(self.variable_waveplate_ins._wavelength))
        self.grid_layout.addWidget(self.quater_waveplate_textfield, 3, 1)

    def set_voltage_1_textfield(self):
        self.voltage_1_textfield = QLineEdit(self)
        self.voltage_1_textfield.setText(str(self.variable_waveplate_ins.get_analog_value(1)))
        self.grid_layout.addWidget(self.voltage_1_textfield, 1, 1)

    def set_voltage_2_textfield(self):
        self.voltage_2_textfield = QLineEdit(self)
        self.voltage_2_textfield.setText(str(self.variable_waveplate_ins.get_analog_value(2)))
        self.grid_layout.addWidget(self.voltage_2_textfield, 2, 1)

    def set_submit_button(self):
        submit_button = QPushButton('Apply', self)
        submit_button.setToolTip('Send all settings to device')
        self.grid_layout.addWidget(submit_button, 3, 3)
        submit_button.clicked.connect(self.submit_button_clicked)

    def set_mode_combobox(self):
        """
        With the combobox all the different modes are shown.
        """
        self.logger.debug('Setting combobox')
        self.mode_combobox = QComboBox(self)
        self.mode_combobox.addItems(["Voltage1", "Voltage2", "Modulation", "QWP"])
        self.mode_combobox.currentIndexChanged.connect(self.set_channel_textfield_disabled)
        self.grid_layout.addWidget(self.mode_combobox, 0, 1)
        self.set_channel_textfield_disabled()

    def set_output_dropdown(self):
        """
        The output parameter is made.
        The letters of the output combobox change depending on if the name is Onn(green) and
        Off(red)
        """
        self.output_combobox = QComboBox(self)
        model = self.output_combobox.model()
        items = ["On", "Off"]
        for row in items:
            item = QStandardItem(str(row))
            if row == "On":
                item.setForeground(QColor('green'))
            elif row == "Off":
                item.setForeground(QColor('red'))
            model.appendRow(item)
        self.grid_layout.addWidget(self.output_combobox, 1, 3)

    def set_channel_textfield_disabled(self):
        """
        if the mode is Voltage1 then it is not possible to
        write something in textbox of Voltage 2 or the others
        """
        if self.mode_combobox.currentText() == "Voltage1":
            self.voltage_1_textfield.setEnabled(True)
            self.voltage_2_textfield.setEnabled(False)
            self.frequency_textfield.setEnabled(False)
            self.quater_waveplate_textfield.setEnabled(False)


        elif self.mode_combobox.currentText() == "Voltage2":
            self.voltage_1_textfield.setEnabled(False)
            self.voltage_2_textfield.setEnabled(True)
            self.frequency_textfield.setEnabled(False)
            self.quater_waveplate_textfield.setEnabled(False)

        elif self.mode_combobox.currentText() == "Modulation":
            self.voltage_1_textfield.setEnabled(True)
            self.voltage_2_textfield.setEnabled(True)
            self.frequency_textfield.setEnabled(True)
            self.quater_waveplate_textfield.setEnabled(False)


        elif self.mode_combobox.currentText() == "QWP":
            self.voltage_1_textfield.setEnabled(False)
            self.voltage_2_textfield.setEnabled(False)
            self.frequency_textfield.setEnabled(False)
            self.quater_waveplate_textfield.setEnabled(True)


    def get_mode(self):
        return self.mode_combobox.currentText()

    def submit_button_clicked(self):
        """
        Get the parameters from the gui and sent these to the
        instrument of the variable waveplate.
        """
        self.logger.debug('Submit button was clicked...')
        self.set_output_mode()

        if self.get_mode() == "Voltage1":
            self.variable_waveplate_ins.mode = 1
            self.variable_waveplate_ins.set_analog_value(1, Q_(self.voltage_1_textfield.text()))
        elif self.get_mode() == "Voltage2":
            self.variable_waveplate_ins.mode = 2
            self.variable_waveplate_ins.set_analog_value(2, Q_(self.voltage_2_textfield.text()))
        elif self.get_mode() == "Modulation":
            self.variable_waveplate_ins.mode = 0
            self.variable_waveplate_ins.freq = Q_(self.frequency_textfield.text())
        elif self.get_mode() == 'QWP':
            self.variable_waveplate_ins.set_quarter_waveplate_voltage(1, Q_(self.quater_waveplate_textfield.text()) )
            self.quater_waveplate_textfield.setText(str(self.variable_waveplate_ins._wavelength))


    def set_output_mode(self):
        """Sets the output on or off deppending on the output_combobox state

        """
        self.logger.info('Setting the output mode to {}'.format(self.output_combobox.currentText()))
        if self.output_combobox.currentText() == "On":
            self.variable_waveplate_ins.output = True
        elif self.output_combobox.currentText() == "Off":
            self.variable_waveplate_ins.output = False


if __name__ == '__main__':
    from hyperion import _logger_format, _logger_settings, root_dir
    from os import path

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    logging.info('Running vairable waveplate GUI file.')
    with VariableWaveplate(settings = {'port':'COM8', 'enable': False, 'dummy' : True,
                                       'controller': 'hyperion.controller.thorlabs.lcc25/Lcc'}) as variable_waveplate_ins:

        variable_waveplate_ins.initialize()
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(path.join(root_dir,'view','gui','vwp_icon.png')))
        ex = VariableWaveplateGui(variable_waveplate_ins)
        #variable_waveplate_ins.finalize()
        sys.exit(app.exec_())
