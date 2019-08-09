import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QComboBox, QLabel, QLineEdit
from hyperion.instrument.variable_waveplate.variable_waveplate import VariableWaveplate
#todo checkout if the device is on the computer if this class can work with the variablewaveplate/lcc25

class VariableWaveplateGui(QWidget):
    """"
    The variable_waveplate gui
    """

    def __init__(self):
        super().__init__()
        self.title = 'variable waveplate gui'
        self.left = 40
        self.top = 40
        self.width = 320
        self.height = 200
        #self.variable_waveplate_ins = variable_waveplate_ins
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.initUI()
    def set_gui_specifics(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

    def initUI(self):
        self.set_gui_specifics()

        self.set_elements_in_gui()

        self.show()

    def set_elements_in_gui(self):

        #labels
        self.mode_label = QLabel(self)
        self.mode_label.setText("mode:")
        self.grid_layout.addWidget(self.mode_label, 0, 0)
        self.voltage_1_label = QLabel(self)
        self.voltage_1_label.setText("V 1:")
        self.grid_layout.addWidget(self.voltage_1_label, 1, 0)

        self.voltage_2_label = QLabel(self)
        self.voltage_2_label.setText("V 2:")
        self.grid_layout.addWidget(self.voltage_2_label, 2, 0)

        self.quater_waveplate_label = QLabel(self)
        self.quater_waveplate_label.setText("qw:")
        self.grid_layout.addWidget(self.quater_waveplate_label, 3, 0)

        self.frequency_label = QLabel(self)
        self.frequency_label.setText("freq:")
        self.grid_layout.addWidget(self.frequency_label, 0, 2)

        #textfields
        self.voltage_1_textfield = QLineEdit(self)
        self.grid_layout.addWidget(self.voltage_1_textfield, 1, 1)

        self.voltage_2_textfield = QLineEdit(self)
        self.grid_layout.addWidget(self.voltage_2_textfield, 2, 1)

        self.quater_waveplate_textfield = QLineEdit(self)
        self.grid_layout.addWidget(self.quater_waveplate_textfield, 3, 1)

        self.frequency_textfield = QLineEdit(self)
        self.grid_layout.addWidget(self.frequency_textfield, 0, 3)
        # addWidget (self, QWidget, row, column, rowSpan, columnSpan, Qt.Alignment alignment = 0)

        #miscelanious:
        self.mode_combobox = QComboBox(self)
        self.mode_combobox.addItems(["piano", "gitaar", "trompet"])
        self.grid_layout.addWidget(self.mode_combobox, 0, 1)

        submit_button = QPushButton('PyQt5 submit_button', self)
        submit_button.setToolTip('This is an example submit_button')
        self.grid_layout.addWidget(submit_button, 3, 3)
        submit_button.clicked.connect(self.submit_button_clicked)

    def submit_button_clicked(self):
        print('PyQt5 button click')

if __name__ == '__main__':
    #variable_waveplate_ins = VariableWaveplate()
    app = QApplication(sys.argv)
    ex = VariableWaveplateGui()
    sys.exit(app.exec_())
