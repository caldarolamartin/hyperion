"""
============
Attocube GUI
============

This is to build a gui for the instrument piezo motor attocube.


"""
import sys, os
import logging
from hyperion import ur
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QComboBox, QGridLayout, QLabel, QLineEdit
from hyperion.instrument.position.anc_instrument import Anc350Instrument
import numpy as np

class Attocube_GUI(QWidget):
    """
    Attocube motor GUI for the instrument


    :param anc350_instrument: class for the instrument to control.
    :type anc350_instrument: instance of the instrument class

    """
    def __init__(self, anc350_instrument):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.title = 'Attocube GUI'
        self.left = 50
        self.top = 50
        self.width = 500
        self.height = 250
        # self.grid_layout = QGridLayout()
        # self.setLayout(self.grid_layout)
        self.anc350_instrument = anc350_instrument

        name = 'attocube.ui'
        gui_folder = os.path.dirname(os.path.abspath(__file__))
        gui_file = os.path.join(gui_folder, name)
        self.logger.info('Loading the GUI file: {}'.format(gui_file))
        self.gui = uic.loadUi(gui_file, self)

        self.max_dclevel_V = 140

        self.current_axis = []
        self.current_move = []
        self.direction = []

            #self.anc350_instrument.controller.max_dcLevel_mV / 1000

        self.initUI()


    def initUI(self):
        self.logger.debug('Setting up the Measurement GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.show()

        #combobox basic
        self.gui.comboBox_axis.setCurrentText('X,Y Piezo Stepper')
        self.gui.comboBox_axis.currentTextChanged.connect(self.get_axis)
        self.gui.pushButton_stop.clicked.connect(self.stop_moving)

        #combobox configurate
        self.gui.doubleSpinBox_amplitudeX.setValue(30)
        self.gui.doubleSpinBox_frequencyX.setValue(500)

        self.gui.doubleSpinBox_amplitudeY.setValue(40)
        self.gui.doubleSpinBox_frequencyY.setValue(500)

        #self.gui.doubleSpinBox_amplitudeX.valueChanged.connect(self.set_value)
        self.gui.doubleSpinBox_frequencyX.valueChanged.connect(self.set_value)

        self.gui.doubleSpinBox_amplitudeX.valueChanged.connect(lambda: self.read_value('Xsettings'))

        self.gui.doubleSpinBox_amplitudeY.valueChanged.connect(self.set_value)
        self.gui.doubleSpinBox_frequencyY.valueChanged.connect(self.set_value)

        self.gui.pushButton_configurateStepper.clicked.connect(self.configurate_stepper)

        #combobox movements of stepper
        self.gui.comboBox_kindOfMove.currentTextChanged.connect(self.get_move)

        self.gui.doubleSpinBox_distance.setValue(0)
        self.gui.doubleSpinBox_distance.valueChanged.connect(self.set_value)

        self.gui.comboBox_unit.currentTextChanged.connect(self.set_value)

        self.gui.pushButton_left.clicked.connect(self.move)
        self.gui.pushButton_right.clicked.connect(self.move)
        self.gui.pushButton_up.clicked.connect(self.move)
        self.gui.pushButton_down.clicked.connect(self.move)


    # def update_gui(self):
    #     self.update_actual_position_label()
    #     self.enable_or_disable_scanner_piezo_widgets()


    def show_position(self, axis):
        pass

    def get_axis(self):
        self.current_axis = self.gui.comboBox_axis.currentText()
        print(self.current_axis)

        if 'Stepper' in self.current_axis:
            self.gui.groupBox_scanner.setEnabled(False)
            self.gui.groupBox_configurate.setEnabled(True)
            self.gui.groupBox_moving.setEnabled(True)
            if 'Z' in self.current_axis:
                self.gui.pushButton_up.setEnabled(False)
                self.gui.pushButton_down.setEnabled(False)
                self.gui.pushButton_left.setText('closer')
                self.gui.pushButton_right.setText('away')
                self.gui.label_xposition.setText('Z position')
                self.gui.label_yposition.setEnabled(False)
                self.gui.label_amplitudeX.setText('Amplitude Z')
                self.gui.label_frequencyX.setText('Frequency Z')
                self.gui.label_amplitudeY.setEnabled(False)
                self.gui.doubleSpinBox_amplitudeY.setEnabled(False)
                self.gui.label_frequencyY.setEnabled(False)
                self.gui.doubleSpinBox_frequencyY.setEnabled(False)
            else:
                self.gui.pushButton_up.setEnabled(True)
                self.gui.pushButton_down.setEnabled(True)
                self.gui.pushButton_left.setText('left')
                self.gui.pushButton_right.setText('right')
                self.gui.label_xposition.setText('X position')
                self.gui.label_yposition.setEnabled(True)
                self.gui.label_amplitudeX.setText('Amplitude X')
                self.gui.label_frequencyX.setText('Frequency X')
                self.gui.label_amplitudeY.setEnabled(True)
                self.gui.doubleSpinBox_amplitudeY.setEnabled(True)
                self.gui.label_frequencyY.setEnabled(True)
                self.gui.doubleSpinBox_frequencyY.setEnabled(True)
        elif 'Scanner' in self.current_axis:
            self.gui.groupBox_scanner.setEnabled(True)
            self.gui.groupBox_configurate.setEnabled(False)
            self.gui.groupBox_moving.setEnabled(False)


    def configurate_stepper(self):
        print('configurate stepper')
        if 'Z' in self.current_axis:
            ampl = self.gui.doubleSpinBox_amplitudeX.value()
            freq = self.gui.doubleSpinBox_frequencyX.value()
            print(ampl)
            self.anc350_instrument.configurate_stepper('ZPiezoStepper',int(ampl)*ur('V'),int(freq)*ur('Hz'))


    def get_move(self):
        self.current_move = self.gui.comboBox_kindOfMove.currentText()
        print(self.current_move)

        if self.current_move == 'move relative':
            self.gui.label_sortMove.setText('to relative distance')
            self.gui.groupBox_info.setEnabled(False)
            self.gui.groupBox_distance.setEnabled(True)
        elif self.current_move == 'move absolute':
            self.gui.label_sortMove.setText('to absolute position')
            self.gui.groupBox_info.setEnabled(False)
            self.gui.groupBox_distance.setEnabled(True)
        elif self.current_move == 'continuous':
            self.gui.label_speed_step.setText('speed: ')
            self.gui.groupBox_info.setEnabled(True)
            self.gui.groupBox_distance.setEnabled(False)
        elif self.current_move == 'step':
            self.gui.label_speed_step.setText('step size: ')
            self.gui.groupBox_info.setEnabled(True)
            self.gui.groupBox_distance.setEnabled(False)

    def left(self):
        self.direction = 'left'
        self.move()

    def move(self):
        if self.current_move == 'move absolute':
            distance = self.gui.doubleSpinBox_distance.value()
            unit = self.gui.comboBox_unit.currentText()
            print(distance, unit)
        elif self.current_move == 'move relative':
            distance = self.gui.doubleSpinBox_distance.value()
            unit = self.gui.comboBox_unit.currentText()
            print(distance, unit)
        elif self.current_move == 'continuous':
            print('continuous')
        elif self.current_move == 'step':
            print('step')


    def stop_moving(self):
        print('stop moving')


    def read_value(self, box, axis):
        if box.value() > self.max_dclevel_V:
            box.setValue(self.max_dclevel_V)
        elif box.value() < 0:
            box.setValue(0)

        info = str(self.sender().value())+'V'
        print(axis)
        print(info)





    def set_value(self):
        #print(self.sender())
        #self.read_value(self.gui.doubleSpinBox_amplitude, axis)
        #print()
        print('hello world')






if __name__ == '__main__':
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350'}) as anc350_instrument:
        app = QApplication(sys.argv)
        ex = Attocube_GUI(anc350_instrument)
        sys.exit(app.exec_())

