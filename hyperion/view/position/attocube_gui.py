"""
============
Attocube GUI
============

This is to build a gui for the instrument piezo motor attocube.


"""
import sys, os
import logging
import time
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

        self.max_amplitude_V = 60
        self.max_frequency = 2000
        self.max_dclevel_V = 140

        self.current_positionX = round(self.anc350_instrument.controller.getPosition(0)*ur('nm').to('mm'),6)
        self.current_positionY = round(self.anc350_instrument.controller.getPosition(2)*ur('nm').to('mm'),6)
        self.current_positionZ = round(self.anc350_instrument.controller.getPosition(1)*ur('nm').to('mm'),6)
        self.current_axis = 'X,Y Piezo Stepper'
        self.current_move = 'continuous'
        self.direction = 'left'

        self.stepper_settings = {'amplitude X': 30, 'amplitude Y': 40, 'amplitude Z': 30,
                                       'frequency X': 100, 'frequency Y': 100, 'frequency Z': 100}

        self.scanner_settings = {'dc X': 1, 'dc Y': 1, 'dc Z': 1}

        self.initUI()


    def initUI(self):
        """Connect all buttons, comboBoxes and doubleSpinBoxes to methods
        """
        self.logger.debug('Setting up the Measurement GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.show()

        #combobox basic
        self.gui.comboBox_axis.setCurrentText(self.current_axis)
        self.gui.comboBox_axis.currentTextChanged.connect(self.get_axis)
        self.gui.pushButton_stop.clicked.connect(self.stop_moving)

        self.gui.groupBox_moving.setEnabled(False)
        self.gui.groupBox_scanner.setEnabled(False)

        self.gui.label_actualPositionX.setText(str(self.current_positionX))
        self.gui.label_actualPositionY.setText(str(self.current_positionY.to('mm')))

        #combobox configurate
        self.gui.doubleSpinBox_amplitudeX.setValue(self.stepper_settings['amplitude X'])
        self.gui.doubleSpinBox_frequencyX.setValue(self.stepper_settings['frequency X'])

        self.gui.doubleSpinBox_amplitudeY.setValue(self.stepper_settings['amplitude Y'])
        self.gui.doubleSpinBox_frequencyY.setValue(self.stepper_settings['frequency Y'])

        #self.gui.doubleSpinBox_amplitudeX.valueChanged.connect(self.set_value)
        self.gui.doubleSpinBox_frequencyX.valueChanged.connect(lambda: self.set_frequency('frequency X'))
        self.gui.doubleSpinBox_amplitudeX.valueChanged.connect(lambda: self.set_amplitude('amplitude X'))

        self.gui.doubleSpinBox_amplitudeY.valueChanged.connect(lambda: self.set_amplitude('amplitude Y'))
        self.gui.doubleSpinBox_frequencyY.valueChanged.connect(lambda: self.set_frequency('frequency Y'))

        self.gui.pushButton_configurateStepper.clicked.connect(self.configurate_stepper)

        #combobox movements of stepper
        self.gui.comboBox_kindOfMove.currentTextChanged.connect(self.get_move)

        self.gui.doubleSpinBox_distance.setValue(0)
        self.gui.doubleSpinBox_distance.valueChanged.connect(self.set_value)

        self.gui.comboBox_unit.currentTextChanged.connect(self.set_value)

        self.gui.pushButton_left.clicked.connect(lambda: self.move('left'))
        self.gui.pushButton_right.clicked.connect(lambda: self.move('right'))
        self.gui.pushButton_up.clicked.connect(lambda: self.move('up'))
        self.gui.pushButton_down.clicked.connect(lambda: self.move('down'))

        #combobox scanner
        self.gui.doubleSpinBox_scannerX.setValue(self.scanner_settings['dc X'])
        self.gui.doubleSpinBox_scannerY.setValue(self.scanner_settings['dc Y'])

        self.gui.doubleSpinBox_scannerX.valueChanged.connect(lambda: self.set_scanner('dc X'))
        self.gui.doubleSpinBox_scannerY.valueChanged.connect(lambda: self.set_scanner('dc Y'))

        #self.gui.pushButton_moveScannerX.clicked.connect(lambda: self.move_scanner('dc X'))
        #self.gui.pushButton_moveScannerY.clicked.connect(lambda: self.move_scanner('dc Y'))

    # def update_gui(self):
    #     self.update_actual_position_label()
    #     self.enable_or_disable_scanner_piezo_widgets()


    def show_position(self, axis):
        pass

    def get_axis(self):
        """| Depending on the selected axis, the gui looks differently
        | The basic box is always enabled
        | If one of the Steppers is selected, only the configuration box is enabled
        | After configuration, also the box with all the moves will be enabled
        | If one of the Scanners is selected, only the scanner box is enabled
        | When the Z Piezo Stepper is selected, all of the X values change to Z, and the Y values are disabled
        | When the Z Piezo Scanner is selected, similar but now only for the two boxes in the scanner part
        | self.current_axis is saved here and used in the whole program
        """

        self.current_axis = self.gui.comboBox_axis.currentText()
        print(self.current_axis)

        if 'Stepper' in self.current_axis:
            self.gui.groupBox_scanner.setEnabled(False)
            self.gui.groupBox_configurate.setEnabled(True)
            self.gui.groupBox_moving.setEnabled(False)
            if 'Z' in self.current_axis:
                self.gui.label_xposition.setText('Z position')
                self.gui.label_actualPositionX.setText(str(self.current_positionZ))
                self.gui.label_yposition.setEnabled(False)

                self.gui.label_amplitudeX.setText('Amplitude Z')
                self.gui.label_frequencyX.setText('Frequency Z')
                self.gui.label_amplitudeY.setEnabled(False)
                self.gui.doubleSpinBox_amplitudeY.setEnabled(False)
                self.gui.label_frequencyY.setEnabled(False)
                self.gui.doubleSpinBox_frequencyY.setEnabled(False)

                self.gui.pushButton_up.setEnabled(False)
                self.gui.pushButton_down.setEnabled(False)
                self.gui.pushButton_left.setText('closer')
                self.gui.pushButton_right.setText('away')

                self.gui.label_speed_stepX.setText('speed Z')
                self.gui.label_speed_stepY.setEnabled(False)
                self.gui.label_speedsize_stepsizeY.setEnabled(False)

            else:
                self.gui.label_xposition.setText('X position')
                self.gui.label_actualPositionX.setText(str(self.current_positionX))
                self.gui.label_yposition.setEnabled(True)

                self.gui.label_amplitudeX.setText('Amplitude X')
                self.gui.label_frequencyX.setText('Frequency X')
                self.gui.label_amplitudeY.setEnabled(True)
                self.gui.doubleSpinBox_amplitudeY.setEnabled(True)
                self.gui.label_frequencyY.setEnabled(True)
                self.gui.doubleSpinBox_frequencyY.setEnabled(True)

                self.gui.pushButton_up.setEnabled(True)
                self.gui.pushButton_down.setEnabled(True)
                self.gui.pushButton_left.setText('left')
                self.gui.pushButton_right.setText('right')

                self.gui.label_speed_stepX.setText('speed X')
                self.gui.label_speed_stepY.setEnabled(True)
                self.gui.label_speedsize_stepsizeY.setEnabled(True)

        elif 'Scanner' in self.current_axis:
            self.gui.groupBox_scanner.setEnabled(True)
            self.gui.groupBox_configurate.setEnabled(False)
            self.gui.groupBox_moving.setEnabled(False)

            if 'Z' in self.current_axis:
                self.gui.label_scannerY.setEnabled(False)
                #self.gui.pushButton_moveScannerY.setEnabled(False)
                self.gui.doubleSpinBox_scannerY.setEnabled(False)
                self.gui.label_scannerX.setText('move scanner Z')
                #self.gui.pushButton_moveScannerX.setText('move scanner Z')
            else:
                self.gui.label_scannerY.setEnabled(True)
                #self.gui.pushButton_moveScannerY.setEnabled(True)
                self.gui.doubleSpinBox_scannerY.setEnabled(True)
                #self.gui.pushButton_moveScannerX.setText('move scanner X')
                self.gui.label_scannerX.setText('move scanner X')

    def set_amplitude(self, axis):
        """| Reads the amplitude that the user filled in
        | Sets either the user input or the default amplitudes as in the dictionary
        | If X and Y Stepper are selected, amplitudes are set separately
        | The amplitude is saved in self.stepper_settings

        :param axis: axis as they are called in the dictionary self.stepper_settings: amplitude X, amplitude Y, amplitude Z
        :type axis: string
        """

        self.logger.info('changing the amplitude')
        if 'Z' in self.current_axis:
            axis = 'amplitude Z'

        if self.sender().value() > self.max_amplitude_V:
            self.sender().setValue(self.max_amplitude_V)
        elif self.sender().value() < 0:
            self.sender().setValue(0)

        # Store the new value in the experiment:
        self.stepper_settings[axis] = self.sender().value()
        self.logger.debug('axis changed: ' + str(axis))
        self.logger.debug('value put: '+str(self.stepper_settings[axis]))


    def set_frequency(self, axis):
        """| Reads the frequency that the user filled in
        | Sets either the user input or the default amplitudes as in the dictionary
        | If X and Y Stepper are selected, frequencies are set separately
        | The frequency is saved in self.stepper_settings

        :param axis: axis as they are called in the dictionary self.stepper_settings: frequency X, frequency Y, frequency Z
        :type axis: string
        """

        self.logger.info('changing the frequency')
        if 'Z' in self.current_axis:
            axis = 'frequency Z'

        if self.sender().value() > self.max_frequency:
            self.sender().setValue(self.max_frequency)
        elif self.sender().value() < 0:
            self.sender().setValue(0)

        # Store the new value in the experiment:
        self.stepper_settings[axis] = int(self.sender().value())
        self.logger.debug('axis changed: ' + str(axis))
        self.logger.debug('value put: '+str(self.stepper_settings[axis]))


    def set_scanner(self, axis):
        """| Reads the amplitude on the scanner that the user filled in
        | Moves the scanner as soon as the user clicks Enter
        | Sets either the user input or the default amplitudes as in the dictionary
        | If X and Y Scanner are selected, amplitudes are set separately
        | The scanner amplitude is saved in self.scanner_settings

        :param axis: axis as they are called in the dictionary self.stepper_settings: dc X, dc Y, dc Z
        :type axis: string
        """

        self.logger.info('changing the scanner amplitude level')
        if 'Z' in self.current_axis:
            axis = 'dc Z'

        if self.sender().value() > self.max_dclevel_V:
            self.sender().setValue(self.max_dclevel_V)
        elif self.sender().value() < 0:
            self.sender().setValue(0)

        # Store the new value in the experiment:
        self.scanner_settings[axis] = self.sender().value()
        self.logger.debug('axis changed: ' + str(axis))
        self.logger.debug('value put: '+str(self.scanner_settings[axis]))

        self.move_scanner(axis)


    def configurate_stepper(self):
        """| Configurates the stepper, using the amplitude and frequency that had been set in set_frequency and set_amplitude
        | After configuration, the box with all the different moves is enabled
        """
        self.logger.info('configurating stepper')
        if 'Z' in self.current_axis:
            self.anc350_instrument.configurate_stepper('ZPiezoStepper', self.stepper_settings['amplitude Z']*ur('V'),self.stepper_settings['frequency Z']*ur('Hz'))
        else:
            self.anc350_instrument.configurate_stepper('XPiezoStepper', self.stepper_settings['amplitude X']*ur('V'),self.stepper_settings['frequency X']*ur('Hz'))
            self.anc350_instrument.configurate_stepper('YPiezoStepper', self.stepper_settings['amplitude Y'] * ur('V'), self.stepper_settings['frequency Y'] * ur('Hz'))

        self.gui.groupBox_moving.setEnabled(True)


    def move_scanner(self, axis):
        """| Moves the scanner
        | Is called by set_scanner, moves as soon as the user clicked Enter

        :param axis: axis as they are called in the dictionary self.stepper_settings: dc X, dc Y, dc Z
        :type axis: string

        """
        if 'Z' in self.current_axis:
            axis = 'dc Z'

        self.logger.info('moving the scanner ' + axis)
        print(self.scanner_settings)
        if 'Z' in axis:
            self.anc350_instrument.move_scanner('ZPiezoScanner',self.scanner_settings[axis]*ur('V'))
        elif 'X' in axis:
            self.anc350_instrument.move_scanner('XPiezoScanner', self.scanner_settings[axis] * ur('V'))
        elif 'Y' in axis:
            self.anc350_instrument.move_scanner('YPiezoScanner', self.scanner_settings[axis] * ur('V'))

    def get_move(self):
        """| Similar to the get_axis, the box with all the moves has lots of options that get disabled or enabled
        | When continuous is selected, it gives you the speed in the selected axes
        | When step is selected, it gives you the stepsize of the selected axes
        | When move absolute or move relative are selected, the user can enter the desired position/distance

        """
        self.current_move = self.gui.comboBox_kindOfMove.currentText()
        self.logger.debug('current way of moving: ' + str(self.current_move))

        if self.current_move == 'move relative':
            self.gui.label_sortMove.setText('to relative distance')
            self.gui.groupBox_info.setEnabled(False)
            self.gui.groupBox_distance.setEnabled(True)
        elif self.current_move == 'move absolute':
            self.gui.label_sortMove.setText('to absolute position')
            self.gui.groupBox_info.setEnabled(False)
            self.gui.groupBox_distance.setEnabled(True)

        elif self.current_move == 'continuous':
            if 'Z' in self.current_axis:
                self.gui.label_speedsize_stepsizeX.setText(str(self.anc350_instrument.Speed[1] * ur('nm/s').to('um/s')))

            else:
                self.gui.label_speed_stepX.setText('speed X')
                self.gui.label_speed_stepY.setText('speed Y')

                self.gui.label_speedsize_stepsizeX.setText(str(self.anc350_instrument.Speed[0]*ur('nm/s').to('um/s')))
                self.gui.label_speedsize_stepsizeY.setText(str(self.anc350_instrument.Speed[2] * ur('nm/s').to('um/s')))

            self.gui.groupBox_info.setEnabled(True)
            self.gui.groupBox_distance.setEnabled(False)

        elif self.current_move == 'step':
            if 'Z' in self.current_axis:
                self.gui.label_speed_stepX.setText('step size Z')
                print(type(str(self.anc350_instrument.Stepwidth[1]*ur('nm'))))
                self.gui.label_speedsize_stepsizeX.setText(str(self.anc350_instrument.Stepwidth[1]*ur('nm')))
            else:
                self.gui.label_speed_stepX.setText('step size X')
                self.gui.label_speed_stepY.setText('step size Y')
                self.gui.label_speedsize_stepsizeX.setText(str(self.anc350_instrument.Stepwidth[0] * ur('nm')))
                self.gui.label_speedsize_stepsizeY.setText(str(self.anc350_instrument.Stepwidth[2] * ur('nm')))

            self.gui.groupBox_info.setEnabled(True)
            self.gui.groupBox_distance.setEnabled(False)


    def move(self, direction):
        """| Here the actual move takes place, after the user clicked on one of the four directional buttons
        | The clicked button determines the direction that is chosen
        | For the continuous and step move, that is than converted to 0 or 1
        | This is correct as it is written right now, I checked it
        | For the relative move, the direction is than converted in adding a minus sign or not

        :param direction: direction of move, left, right, up, down
        :type direction: string
        """

        self.direction = direction
        self.logger.debug('current direction: ' + direction)

        if self.current_move == 'move absolute':
            distance = self.gui.doubleSpinBox_distance.value()
            unit = self.gui.comboBox_unit.currentText()
            print(distance, unit)
        elif self.current_move == 'move relative':
            distance = self.gui.doubleSpinBox_distance.value()
            unit = self.gui.comboBox_unit.currentText()
            print(distance, unit)

        elif self.current_move == 'continuous' or self.current_move == 'step':
            if 'Z' in self.current_axis:
                axis_string = 'ZPiezoStepper'
                if self.direction == 'left':
                    direction_int = 0       # correct direction, corresponds to labels closer and away
                elif self.direction == 'right':
                    direction_int = 1       # correct direction, corresponds to labels closer and away
            else:
                if self.direction == 'left':
                    axis_string = 'XPiezoStepper'
                    direction_int = 0
                elif self.direction == 'right':
                    axis_string = 'XPiezoStepper'
                    direction_int = 1
                elif self.direction == 'up':
                    axis_string = 'YPiezoStepper'
                    direction_int = 1
                elif self.direction == 'down':
                    axis_string = 'YPiezoStepper'
                    direction_int = 0

            if self.current_move == 'continuous':
                self.logger.debug('moving for 1 s continuously')
                self.anc350_instrument.move_continuous(axis_string, direction_int)
                time.sleep(1)
                self.anc350_instrument.stop_moving(axis_string)

            elif self.current_move == 'step':
                self.logger.debug('making a step')
                self.anc350_instrument.given_step(axis_string, direction_int, 1)


    def stop_moving(self):
        """|Stops movement of all steppers
        | Does not work yet, since there are not threads
        """

        self.logger.info('stop moving')
        self.anc350_instrument.stop_moving('XPiezoStepper')
        self.anc350_instrument.stop_moving('YPiezoStepper')
        self.anc350_instrument.stop_moving('ZPiezoStepper')


    def set_value(self):
        pass






if __name__ == '__main__':
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350'}) as anc350_instrument:
        app = QApplication(sys.argv)
        ex = Attocube_GUI(anc350_instrument)
        sys.exit(app.exec_())

