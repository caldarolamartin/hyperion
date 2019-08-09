import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QComboBox, QLabel, QLineEdit
from hyperion.instrument.variable_waveplate.variable_waveplate import VariableWaveplate
from hyperion import Q_
#todo checkout if the device is on the computer if this class can work with the variablewaveplate/lcc25

class VariableWaveplateGui(QWidget):
    """"
    The variable_waveplate gui
    """

    def __init__(self, variable_waveplate_ins):
        super().__init__()
        self.title = 'variable waveplate gui'
        self.left = 40
        self.top = 40
        self.width = 320
        self.height = 200
        self.variable_waveplate_ins = variable_waveplate_ins
        self.initUI()
    def set_gui_specifics(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

    def initUI(self):
        self.set_gui_specifics()

        self.set_elements_in_gui()

        self.show()

    def set_elements_in_gui(self):
        # addWidget (self, QWidget, row, column, rowSpan, columnSpan, Qt.Alignment alignment = 0)
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
    def set_frequency_label(self):
        self.frequency_label = QLabel(self)
        self.frequency_label.setText("freq:")
        self.grid_layout.addWidget(self.frequency_label, 0, 2)
    def set_quater_waveplate_label(self):
        self.quater_waveplate_label = QLabel(self)
        self.quater_waveplate_label.setText("qw:")
        self.grid_layout.addWidget(self.quater_waveplate_label, 3, 0)
    def set_voltage_2_label(self):
        self.voltage_2_label = QLabel(self)
        self.voltage_2_label.setText("V 2:")
        self.grid_layout.addWidget(self.voltage_2_label, 2, 0)
    def set_voltage_1_label(self):
        self.voltage_1_label = QLabel(self)
        self.voltage_1_label.setText("V 1:")
        self.grid_layout.addWidget(self.voltage_1_label, 1, 0)
    def set_mode_label(self):
        self.mode_label = QLabel(self)
        self.mode_label.setText("mode:")
        self.grid_layout.addWidget(self.mode_label, 0, 0)
    def set_output_label(self):
        self.output_label = QLabel(self)
        self.output_label.setText("output:")
        self.grid_layout.addWidget(self.output_label, 1, 2)

    def set_textfields(self):
        self.set_voltage_1_textfield()
        self.set_voltage_2_textfield()
        self.set_quater_waveplate_textfield()
        self.set_frequency_textfield()
    def set_frequency_textfield(self):
        self.frequency_textfield = QLineEdit(self)
        self.frequency_textfield.setText(str(self.variable_waveplate_ins.freq))
        self.grid_layout.addWidget(self.frequency_textfield, 0, 3)
    def set_quater_waveplate_textfield(self):
        self.quater_waveplate_textfield = QLineEdit(self)
        self.grid_layout.addWidget(self.quater_waveplate_textfield, 3, 1)
    def set_voltage_2_textfield(self):
        self.voltage_2_textfield = QLineEdit(self)
        #self.voltage_2_textfield.setText(self.variable_waveplate_ins.)
        self.grid_layout.addWidget(self.voltage_2_textfield, 2, 1)
    def set_voltage_1_textfield(self):
        self.voltage_1_textfield = QLineEdit(self)
        self.grid_layout.addWidget(self.voltage_1_textfield, 1, 1)

    def set_miscelanious_gui_stuff(self):
        self.set_mode_combobox()
        self.set_submit_button()
        self.set_output_dropdown()
    def set_submit_button(self):
        submit_button = QPushButton('submit_button', self)
        submit_button.setToolTip('This is an example submit_button')
        self.grid_layout.addWidget(submit_button, 3, 3)
        submit_button.clicked.connect(self.submit_button_clicked)
    def set_mode_combobox(self):
        self.mode_combobox = QComboBox(self)
        self.mode_combobox.addItems(["Voltage1", "Voltage2", "Modulation"])
        self.grid_layout.addWidget(self.mode_combobox, 0, 1)
    def set_output_dropdown(self):
        self.output_combobox = QComboBox(self)
        self.output_combobox.addItems(["On", "Off"])
        self.grid_layout.addWidget(self.output_combobox, 1, 3)

    def get_mode(self):
        return self.mode_combobox.currentText()

    def submit_button_clicked(self):
        self.set_output_mode()

        if self.get_mode() == "Voltage1":
            # self.variable_waveplate_ins.set_analog_value(1, (20 * Q_("V")))
            self.variable_waveplate_ins.mode = 1
            self.variable_waveplate_ins.set_analog_value(1, (self.voltage_1_textfield.text() * Q_("V")))
        elif self.get_mode() == "Voltage2":
            self.variable_waveplate_ins.mode = 2
            self.variable_waveplate_ins.set_analog_value(2, (self.voltage_2_textfield.text() * Q_("V")))
        elif self.get_mode() == "Modulation":
            self.variable_waveplate_ins.mode = 0
    def set_output_mode(self):
        if self.output_combobox.currentText() == "On":
            self.variable_waveplate_ins.output = True
        elif self.output_combobox.currentText() == "Off":
            self.variable_waveplate_ins.output = False

if __name__ == '__main__':
    variable_waveplate_ins = VariableWaveplate()
    variable_waveplate_ins.initialize()
    app = QApplication(sys.argv)
    ex = VariableWaveplateGui(variable_waveplate_ins)
    variable_waveplate_ins.finalize()
    sys.exit(app.exec_())
