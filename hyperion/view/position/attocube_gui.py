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
        self.max_distance = 5*ur('mm')

        self.current_positionX = round(self.anc350_instrument.controller.getPosition(0)*ur('nm').to('mm'),6)
        self.current_positionY = round(self.anc350_instrument.controller.getPosition(2)*ur('nm').to('mm'),6)
        self.current_positionZ = round(self.anc350_instrument.controller.getPosition(1)*ur('nm').to('mm'),6)
        self.current_axis = 'X,Y Piezo Stepper'
        self.current_move = 'continuous'
        self.direction = 'left'
        self.distance = 0*ur('um')

        self.stepper_settings = {'amplitudeX': 30, 'amplitudeY': 40, 'amplitudeZ': 30,
                                       'frequencyX': 100, 'frequencyY': 100, 'frequencyZ': 100}
        self.scanner_settings = {'dcX': 1, 'dcY': 1, 'dcZ': 1}

        self.initUI()


    def initUI(self):
        """Connect all buttons, comboBoxes and doubleSpinBoxes to methods
        """
        self.logger.debug('Setting up the Measurement GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.show()

        self.gui.groupBox_basic.setObjectName("Colored_basic")
        self.gui.groupBox_basic.setStyleSheet("QGroupBox#Colored_basic {border: 1px solid blue;}")

        self.gui.groupBox_configurate.setStyleSheet("QGroupBox {border: 1px solid blue;}")

        #combobox basic
        self.gui.comboBox_axis.setCurrentText(self.current_axis)
        self.gui.comboBox_axis.currentTextChanged.connect(self.get_axis)
        self.gui.pushButton_stop.clicked.connect(self.stop_moving)

        self.gui.groupBox_moving.setEnabled(False)
        self.gui.groupBox_scanner.setEnabled(False)

        self.gui.label_actualPositionX.setText(str(self.current_positionX))
        self.gui.label_actualPositionY.setText(str(self.current_positionY))
        self.gui.label_actualPositionZ.setText(str(self.current_positionZ))

        self.pushButton_stop.setStyleSheet("background-color: red")

        #combobox configurate
        self.gui.doubleSpinBox_amplitudeX.setValue(self.stepper_settings['amplitudeX'])
        self.gui.doubleSpinBox_frequencyX.setValue(self.stepper_settings['frequencyX'])

        self.gui.doubleSpinBox_amplitudeY.setValue(self.stepper_settings['amplitudeY'])
        self.gui.doubleSpinBox_frequencyY.setValue(self.stepper_settings['frequencyY'])

        #self.gui.doubleSpinBox_amplitudeX.valueChanged.connect(self.set_value)
        self.gui.doubleSpinBox_frequencyX.valueChanged.connect(lambda: self.set_value('X','frequency'))
        self.gui.doubleSpinBox_amplitudeX.valueChanged.connect(lambda: self.set_value('X','amplitude'))

        self.gui.doubleSpinBox_amplitudeY.valueChanged.connect(lambda: self.set_value('Y','amplitude'))
        self.gui.doubleSpinBox_frequencyY.valueChanged.connect(lambda: self.set_value('Y','frequency'))

        self.gui.pushButton_configurateStepper.clicked.connect(self.configurate_stepper)

        #combobox movements of stepper
        self.gui.comboBox_kindOfMove.currentTextChanged.connect(self.get_move)

        self.gui.comboBox_unit.setCurrentText('um')
        self.gui.doubleSpinBox_distance.setValue(self.distance.m_as('um'))
        self.gui.doubleSpinBox_distance.valueChanged.connect(self.set_distance)
        self.gui.comboBox_unit.currentTextChanged.connect(self.set_distance)

        self.gui.pushButton_left.clicked.connect(lambda: self.move('left'))
        self.gui.pushButton_right.clicked.connect(lambda: self.move('right'))
        self.gui.pushButton_up.clicked.connect(lambda: self.move('up'))
        self.gui.pushButton_down.clicked.connect(lambda: self.move('down'))

        #combobox scanner
        self.gui.doubleSpinBox_scannerX.setValue(self.scanner_settings['dcX'])
        self.gui.doubleSpinBox_scannerY.setValue(self.scanner_settings['dcY'])

        self.gui.doubleSpinBox_scannerX.valueChanged.connect(lambda: self.set_value('X','dc'))
        self.gui.doubleSpinBox_scannerY.valueChanged.connect(lambda: self.set_value('Y','dc'))

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
            self.gui.groupBox_scanner.setStyleSheet("QGroupBox default")

            self.gui.groupBox_configurate.setEnabled(True)
            self.gui.groupBox_configurate.setStyleSheet("QGroupBox {border: 1px solid blue;}")

            self.gui.groupBox_moving.setEnabled(False)
            self.gui.groupBox_moving.setStyleSheet("QGroupBox default")

            if 'Z' in self.current_axis:
                # self.gui.label_xposition.setText('Z position')
                # self.gui.label_actualPositionX.setText(str(self.current_positionZ))
                # self.gui.label_yposition.setEnabled(False)
                # self.gui.label_xposition.setEnabled(False)
                self.gui.groupBox_XY.setEnabled(False)
                self.gui.groupBox_Z.setEnabled(True)

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
                # self.gui.label_xposition.setText('X position')
                # self.gui.label_actualPositionX.setText(str(self.current_positionX))
                # self.gui.label_yposition.setEnabled(True)
                # self.gui.label_xposition.setEnabled(True)
                self.gui.groupBox_XY.setEnabled(True)
                self.gui.groupBox_Z.setEnabled(False)

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

            self.gui.groupBox_configurate.setStyleSheet("QGroupBox default")
            self.gui.groupBox_moving.setStyleSheet("QGroupBox default")
            self.gui.groupBox_scanner.setStyleSheet("QGroupBox {border: 1px solid blue;}")

            if 'Z' in self.current_axis:
                self.gui.label_scannerY.setEnabled(False)
                self.gui.doubleSpinBox_scannerY.setEnabled(False)
                self.gui.label_scannerX.setText('move scanner Z')
            else:
                self.gui.label_scannerY.setEnabled(True)
                self.gui.doubleSpinBox_scannerY.setEnabled(True)
                self.gui.label_scannerX.setText('move scanner X')



    def set_value(self, axis, value_type):
        """| Reads the value that the user filled in: amplitude, frequency or dc level on scanner
        | Sets either the user input or the default amplitudes/frequencies as in the dictionary
        | The value is saved in self.scanner_settings or self.stepper_settings
        | If X and Y Scanner are selected, values are set separately; with Z, there is only one spinbox to fill in
        | Values from dictionary are used in configurate stepper, but only if the user clicks configurate
        | If scanner values were changed, this method calls to moving of the the scanner as soon as the user clicks Enter
        | axis and value_type are locally changed into the name as known in the dictionaries, like amplitudeX or dcZ

        :param axis: axis X, Y, Z
        :type axis: string

        :param value_type: amplitude, frequency or dc
        :type value_type: string
        """
        self.logger.info('changing a value')

        if 'Z' in self.current_axis:
            local_axis_name = value_type + 'Z'
        else:
            local_axis_name = value_type + axis

        if value_type == 'amplitude':
            self.logger.debug('changing the amplitude')
            max_value = self.max_amplitude_V
        elif value_type == 'frequency':
            self.logger.debug('changing the frequency')
            max_value = self.max_frequency
        elif value_type == 'dc':
            self.logger.debug('changing the dc level on scanner')
            max_value = self.max_dclevel_V

        if self.sender().value() > max_value:
            self.sender().setValue(max_value)
        elif self.sender().value() < 0:
            self.sender().setValue(0)

        # Store the new value in the experiment:
        print(local_axis_name)
        self.stepper_settings[local_axis_name] = int(self.sender().value())
        print(self.stepper_settings)
        self.logger.debug('axis changed: ' + str(local_axis_name))
        self.logger.debug('value put: ' + str(self.stepper_settings[local_axis_name]))

        if value_type == 'dc':
            self.move_scanner(local_axis_name)

    def set_distance(self):
        """| Works similar to set_value method, but now only for the distance spinBox and unit
        | Combines value of spinbox with unit and checks against maximum value defined up
        | Either applies the dictionary value of the distance, or changes that dictionary value and than applies it
        """

        distance = self.gui.doubleSpinBox_distance.value()
        unit = self.gui.comboBox_unit.currentText()

        local_distance = ur(str(distance)+unit)
        self.logger.debug('local distance value: ' + str(local_distance))

        if local_distance > self.max_distance:
            self.logger.debug('value too high')
            local_max = self.max_distance.to(unit)
            print(local_max)
            self.gui.doubleSpinBox_distance.setValue(local_max.m_as(unit))
        elif local_distance < 0:
            self.logger.debug('value too low')
            self.gui.doubleSpinBox_distance.setValue(0)

        self.distance = local_distance
        self.logger.debug('dictionary distance changed to: ' + str(self.distance))


    def configurate_stepper(self):
        """| Configurates the stepper, using the amplitude and frequency that had been set in set_frequency and set_amplitude
        | After configuration, the box with all the different moves is enabled
        """
        self.logger.info('configurating stepper')
        if 'Z' in self.current_axis:
            self.anc350_instrument.configurate_stepper('ZPiezoStepper', self.stepper_settings['amplitudeZ']*ur('V'),self.stepper_settings['frequencyZ']*ur('Hz'))
        else:
            self.anc350_instrument.configurate_stepper('XPiezoStepper', self.stepper_settings['amplitudeX']*ur('V'),self.stepper_settings['frequencyX']*ur('Hz'))
            self.anc350_instrument.configurate_stepper('YPiezoStepper', self.stepper_settings['amplitudeY'] * ur('V'), self.stepper_settings['frequencyY'] * ur('Hz'))

        self.gui.groupBox_moving.setEnabled(True)
        self.gui.groupBox_configurate.setStyleSheet("QGroupBox default")
        self.gui.groupBox_moving.setObjectName("ColoredGroupBox")
        self.gui.groupBox_moving.setStyleSheet("QGroupBox#ColoredGroupBox {border: 1px solid blue;}")

    def move_scanner(self, axis):
        """| Moves the scanner
        | Is called by set_value, moves as soon as the user clicked Enter

        :param axis: axis as they are called in the dictionary self.stepper_settings: dcX, dcY, dcZ
        :type axis: string
        """
        if 'Z' in self.current_axis:
            axis = 'dcZ'

        self.logger.info('moving the scanner ' + axis)
        #self.logger.debug(self.scanner_settings)
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

        if 'Z' in self.current_axis:
            axis_string = 'ZPiezoStepper'
        else:
            if self.direction == 'left' or self.direction == 'right':
                axis_string = 'XPiezoStepper'
            else:
                axis_string = 'YPiezoStepper'

        if self.current_move == 'move absolute':
            distance = self.gui.doubleSpinBox_distance.value()
            unit = self.gui.comboBox_unit.currentText()
            print(distance, unit)

        elif self.current_move == 'move relative':
            self.logger.info('moving relative')
            distance = self.gui.doubleSpinBox_distance.value()
            unit = self.gui.comboBox_unit.currentText()
            self.logger.debug('axis:' + axis_string)
            self.logger.debug('direction: '+ direction)

            if self.direction == 'left' or self.direction == 'down':
                local_distance = ur(str(distance) + unit)
                self.logger.debug(local_distance)
            elif self.direction == 'right' or self.direction == 'up':
                local_distance = ur(str(-1 * distance) + unit)
                self.logger.debug(local_distance)

            self.anc350_instrument.move_relative(axis_string, local_distance)

        elif self.current_move == 'continuous' or self.current_move == 'step':
            if self.direction == 'left':
                direction_int = 0       # correct direction, corresponds to labels closer and away
            elif self.direction == 'right':
                direction_int = 1       # correct direction, corresponds to labels closer and away
            elif self.direction == 'up':
                direction_int = 1
            elif self.direction == 'down':
                direction_int = 0

            if self.current_move == 'continuous':
                self.logger.info('moving for 1 s continuously')
                self.anc350_instrument.move_continuous(axis_string, direction_int)
                time.sleep(1)
                self.anc350_instrument.stop_moving(axis_string)

            elif self.current_move == 'step':
                self.logger.info('making a step')
                self.anc350_instrument.given_step(axis_string, direction_int, 1)


    def stop_moving(self):
        """|Stops movement of all steppers
        | Does not work yet, since there are not threads
        """

        self.logger.info('stop moving')
        self.anc350_instrument.stop_moving('XPiezoStepper')
        self.anc350_instrument.stop_moving('YPiezoStepper')
        self.anc350_instrument.stop_moving('ZPiezoStepper')









if __name__ == '__main__':
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350'}) as anc350_instrument:
        app = QApplication(sys.argv)
        ex = Attocube_GUI(anc350_instrument)
        sys.exit(app.exec_())

