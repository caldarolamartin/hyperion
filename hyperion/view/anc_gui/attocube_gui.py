import sys
import logging
from hyperion import ur
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QComboBox, QGridLayout, QLabel, QLineEdit
from hyperion.instrument.positioner.anc_instrument import Anc350Instrument


class App(QWidget):

    def __init__(self, anc350_instrument):
        super().__init__()
        self.title = 'attocube gui'
        self.left = 50
        self.top = 50
        self.width = 500
        self.height = 250
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.anc350_instrument = anc350_instrument
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.anc350_instrument.initialize()
        self.anc350_instrument.initialize_available_motors()
        self.anc350_instrument.list_devices()

        self.make_labels()
        self.make_textfields()
        self.make_buttons()
        self.make_misc_gui_stuff()
        self.enable_or_disable_scanner_piezo_widgets()

        self.show()

    def make_labels(self):
        self.make_move_to_absolute_position_label()
        self.make_move_to_relative_position_label()
        self.make_piezo_scanner_position_label()
        self.make_single_step_forward_label()
        self.make_single_step_backward_label()
        self.make_move_scanner_label()
        self.make_actual_position_label()
        self.make_step_amount_label()
        self.make_amplitude_label()
        self.make_frequency_label()
    def make_textfields(self):
        self.make_move_to_absolute_position_textfield()
        self.make_move_to_relative_position_textfield()
        self.make_move_scanner_textfield()
        self.make_amplitude_textfield()
        self.make_frequency_textfield()
        self.make_step_amount_textfield()
    def make_buttons(self):
        self.make_move_to_absolute_position_button()
        self.make_move_to_relative_position_button()
        self.make_step_position_forward_button()
        self.make_step_position_backward_button()
        self.make_move_scanner_button()
        self.make_move_scanner_button()
        self.make_configurate_stepper_button()
    def make_misc_gui_stuff(self):
        self.make_scanner_piezo_combobox()

    def make_piezo_scanner_position_label(self):
        self.piezo_scanner_postion_label = QLabel(self)
        self.piezo_scanner_postion_label.setText("Postion: ")
        self.grid_layout.addWidget(self.piezo_scanner_postion_label, 0, 0)
    def make_move_to_absolute_position_label(self):
        self.move_to_absolute_position_label = QLabel(self)
        self.move_to_absolute_position_label.setText("Move to\nabsolute position in nm: ")
        self.grid_layout.addWidget(self.move_to_absolute_position_label, 1, 0)
    def make_move_to_relative_position_label(self):
        self.move_to_relative_position_label = QLabel(self)
        self.move_to_relative_position_label.setText("Move to\nrelative position in nm: ")
        self.grid_layout.addWidget(self.move_to_relative_position_label, 2, 0)
    def make_single_step_forward_label(self):
        self.pos_single_step_forward_label = QLabel(self)
        self.pos_single_step_forward_label.setText("Move single step\nleft: ")
        self.grid_layout.addWidget(self.pos_single_step_forward_label, 3, 0)
    def make_single_step_backward_label(self):
        self.pos_single_step_backward_label = QLabel(self)
        self.pos_single_step_backward_label.setText("Move single step\nright: ")
        self.grid_layout.addWidget(self.pos_single_step_backward_label, 4, 0)
    def make_move_scanner_label(self):
        self.move_scanner_label = QLabel(self)
        self.move_scanner_label.setText("Move scanner in mV\nbetween 0 and 140000 mV: ")
        self.grid_layout.addWidget(self.move_scanner_label, 5, 2)
    def make_actual_position_label(self):
        self.actual_position_label = QLabel(self)
        self.actual_position_label.setText("currently\nunavailable")
        self.grid_layout.addWidget(self.actual_position_label, 0, 1)
    def make_step_amount_label(self):
        self.step_amount_label = QLabel(self)
        self.step_amount_label.setText("amount of steps:")
        self.grid_layout.addWidget(self.step_amount_label, 5, 0)
    def make_amplitude_label(self):
        self.amplitude_label = QLabel(self)
        self.amplitude_label.setText("Amplitude:")
        self.grid_layout.addWidget(self.amplitude_label, 0, 3)
    def make_frequency_label(self):
        self.frequency_label = QLabel(self)
        self.frequency_label.setText("Frequency:")
        self.grid_layout.addWidget(self.frequency_label, 1, 3)

    def make_move_to_absolute_position_textfield(self):
        self.move_to_absolute_position_textfield = QLineEdit(self)
        self.move_to_absolute_position_textfield.setText("0")
        self.grid_layout.addWidget(self.move_to_absolute_position_textfield, 1, 1)
    def make_move_to_relative_position_textfield(self):
        self.move_to_relative_position_textfield = QLineEdit(self)
        self.move_to_relative_position_textfield.setText("0")
        self.grid_layout.addWidget(self.move_to_relative_position_textfield, 2, 1)
    def make_move_scanner_textfield(self):
        self.move_scanner_textfield = QLineEdit(self)
        self.move_scanner_textfield.setText("1000")
        self.grid_layout.addWidget(self.move_scanner_textfield, 5, 3)
    def make_amplitude_textfield(self):
        self.amplitude_textfield = QLineEdit(self)
        self.amplitude_textfield.setText("0")
        self.grid_layout.addWidget(self.amplitude_textfield, 0, 4)
    def make_frequency_textfield(self):
        self.frequency_textfield = QLineEdit(self)
        self.frequency_textfield.setText("0")
        self.grid_layout.addWidget(self.frequency_textfield, 1, 4)
    def make_step_amount_textfield(self):
        self.step_amount_textfield = QLineEdit(self)
        self.step_amount_textfield.setText("1")
        self.grid_layout.addWidget(self.step_amount_textfield, 5, 1)

    def make_move_to_absolute_position_button(self):
        self.move_to_absolute_position_button = QPushButton("absolute position", self)
        self.move_to_absolute_position_button.setToolTip("move to the absolute position")
        self.move_to_absolute_position_button.clicked.connect(self.move_absolute_position)
        self.grid_layout.addWidget(self.move_to_absolute_position_button, 1, 2)
    def make_move_to_relative_position_button(self):
        self.move_to_relative_position_button = QPushButton("relative position", self)
        self.move_to_relative_position_button.setToolTip("move to the relative position")
        self.move_to_relative_position_button.clicked.connect(self.move_relative_position)
        self.grid_layout.addWidget(self.move_to_relative_position_button, 2, 2)
    def make_step_position_forward_button(self):
        self.step_position_forward_button = QPushButton("step left", self)
        self.step_position_forward_button.setToolTip("move a single step to the left")
        self.step_position_forward_button.clicked.connect(self.go_single_step_forward)
        self.grid_layout.addWidget(self.step_position_forward_button, 3, 1)
    def make_step_position_backward_button(self):
        self.step_position_backward_button = QPushButton("step right", self)
        self.step_position_backward_button.setToolTip("move a single step to the right")
        self.step_position_backward_button.clicked.connect(self.go_single_step_backward)
        self.grid_layout.addWidget(self.step_position_backward_button, 4, 1)
    def make_move_scanner_button(self):
        self.move_scanner_button = QPushButton("move scanner", self)
        self.move_scanner_button.setToolTip("Move the scanner as specified in the textfield(which you do, not I)")
        self.move_scanner_button.clicked.connect(self.move_scanner)
        self.grid_layout.addWidget(self.move_scanner_button, 5, 4)
    def make_configurate_stepper_button(self):
        self.configurate_stepper_button = QPushButton("configurate stepper", self)
        self.configurate_stepper_button.setToolTip("In order to configurate the stepper\nthe frequency and amplitude are also needed")
        self.configurate_stepper_button.clicked.connect(self.configurate_current_stepper)
        self.grid_layout.addWidget(self.configurate_stepper_button, 2, 4)



    def make_scanner_piezo_combobox(self):
        self.scanner_piezo_combobox = QComboBox(self)
        print(self.anc350_instrument.attocube_piezo_dict.keys())
        for item in self.anc350_instrument.attocube_piezo_dict.keys():
            self.scanner_piezo_combobox.addItem(item)
        self.scanner_piezo_combobox.currentIndexChanged.connect(self.update_gui)
        self.grid_layout.addWidget(self.scanner_piezo_combobox, 0, 2)

    def update_gui(self):
        self.update_actual_position_label()
        self.enable_or_disable_scanner_piezo_widgets()
    def update_actual_position_label(self):
        try:
            self.actual_position_label.setText("Position in nm: "+str(self.anc350_instrument.controller.getPosition(self.anc350_instrument.attocube_piezo_dict[self.scanner_piezo_combobox.currentText()])))
        except Exception:
            self.actual_position_label.setText("currently\nunavailable")
    def enable_or_disable_scanner_piezo_widgets(self):
        #make sure that if the scanner stuff is enabled that the piezo stuff is disabled and viceversa
        if "Stepper" in self.scanner_piezo_combobox.currentText():
            #set scanner things false
            self.move_scanner_textfield.setEnabled(False)
            self.move_scanner_button.setEnabled(False)
            #set stepper things true
            self.move_to_absolute_position_textfield.setEnabled(True)
            self.move_to_absolute_position_button.setEnabled(True)
            self.move_to_relative_position_textfield.setEnabled(True)
            self.move_to_relative_position_button.setEnabled(True)
            self.step_position_forward_button.setEnabled(True)
            self.step_position_backward_button.setEnabled(True)
            self.amplitude_textfield.setEnabled(True)
            self.frequency_textfield.setEnabled(True)
            self.step_amount_textfield.setEnabled(True)
            self.configurate_stepper_button.setEnabled(True)
        elif "Scanner" in self.scanner_piezo_combobox.currentText():
            #set stepper things false
            self.move_to_absolute_position_textfield.setEnabled(False)
            self.move_to_absolute_position_button.setEnabled(False)
            self.move_to_relative_position_textfield.setEnabled(False)
            self.move_to_relative_position_button.setEnabled(False)
            self.step_position_forward_button.setEnabled(False)
            self.step_position_backward_button.setEnabled(False)
            self.amplitude_textfield.setEnabled(False)
            self.frequency_textfield.setEnabled(False)
            self.step_amount_textfield.setEnabled(False)
            self.configurate_stepper_button.setEnabled(False)
            #set scanner things true
            self.move_scanner_textfield.setEnabled(True)
            self.move_scanner_button.setEnabled(True)
        else:
            print("There should not be a different motor besides a\nStepper and a Scanner, so...you should change the .yml file.")

    def move_absolute_position(self):
        print("move absolute position")
        axis = self.scanner_piezo_combobox.currentText() #axis = XPiezoStepper, YPiezoStepper or ZPiezoStepper
        position = int(self.move_to_absolute_position_textfield.text())* ur('nm') #position = something in nm
        self.anc350_instrument.move_to(axis, position)
        self.update_actual_position_label()

    def move_relative_position(self):
        print("move relative position")
        axis = self.scanner_piezo_combobox.currentText() #the current stepper
        step = int(self.move_to_relative_position_textfield.text())* ur('nm') #step: amount to move in nm, can be both positive and negative
        self.anc350_instrument.move_relative(axis, step)
        self.update_actual_position_label()
    def go_single_step_forward(self):
        print("go a single step to the left")
        axis = self.scanner_piezo_combobox.currentText()  # the current stepper
        direction = 0 # forward = 0
        amount = int(self.step_amount_textfield.text())
        self.anc350_instrument.given_step(axis, direction, amount)
    def go_single_step_backward(self):
        print("go a single step to the right")
        axis = self.scanner_piezo_combobox.currentText()  # the current stepper
        direction = 1 # backward = 1
        amount = int(self.step_amount_textfield.text())
        self.anc350_instrument.given_step(axis, direction, amount)

    def move_scanner(self):
        print("move the scanner by a...value")
        """
        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner or ZPiezoScanner
        :type axis: string

        :param voltage: voltage in mV to move the scanner; from 0-140V
        :type axis: pint quantity
        """
        axis = self.scanner_piezo_combobox.currentText()  # the current scanner
        voltage = self.move_scanner_textfield.text() * ur('mV')
        self.anc350_instrument.move_scanner(axis, voltage)
        self.update_actual_position_label()
    def configurate_current_stepper(self):
        pass


if __name__ == '__main__':
    anc350_instrument = Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350'})
    app = QApplication(sys.argv)
    ex = App(anc350_instrument)
    sys.exit(app.exec_())
