"""
===================
Attocube GUI
===================

This is to build a gui for the instrument piezo motor attocube.


"""
import sys, os
import logging
import time
from hyperion import ur
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget
from hyperion.instrument.position.anc_instrument import Anc350Instrument

class Attocube_GUI(QWidget):
    """
    Attocube piezo GUI for the instrument

    :param anc350_instrument: class for the instrument to control.
    :type anc350_instrument: instance of the instrument class

    """
    def __init__(self, anc350_instrument):
        """Attocube
        """

        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.title = 'Attocube GUI'
        self.left = 50
        self.top = 50
        self.width = 500
        self.height = 250
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

        self.settings = {'amplitudeX': 30, 'amplitudeY': 40, 'amplitudeZ': 30,
                                       'frequencyX': 100, 'frequencyY': 100, 'frequencyZ': 100, 'dcX': 1, 'dcY': 1, 'dcZ': 1}

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

        self.gui.groupBox_configurate.setObjectName("Colored_configure")
        self.gui.groupBox_configurate.setStyleSheet("QGroupBox#Colored_configure {border: 1px solid blue;}")

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
        self.gui.groupBox_XY.setEnabled(True)
        self.gui.groupBox_Z.setEnabled(False)

        #combobox configurate
        self.gui.doubleSpinBox_amplitudeX.setValue(self.settings['amplitudeX'])
        self.gui.doubleSpinBox_frequencyX.setValue(self.settings['frequencyX'])

        self.gui.doubleSpinBox_amplitudeY.setValue(self.settings['amplitudeY'])
        self.gui.doubleSpinBox_frequencyY.setValue(self.settings['frequencyY'])

        self.gui.doubleSpinBox_amplitudeZ.setValue(self.settings['amplitudeZ'])
        self.gui.doubleSpinBox_frequencyZ.setValue(self.settings['frequencyZ'])

        # self.gui.groupBox_amplZ.setEnabled(False)
        # self.gui.groupBox_amplXY.setEnabled(True)

        self.gui.doubleSpinBox_frequencyX.valueChanged.connect(lambda: self.set_value('X','frequency'))
        self.gui.doubleSpinBox_amplitudeX.valueChanged.connect(lambda: self.set_value('X','amplitude'))

        self.gui.doubleSpinBox_amplitudeY.valueChanged.connect(lambda: self.set_value('Y','amplitude'))
        self.gui.doubleSpinBox_frequencyY.valueChanged.connect(lambda: self.set_value('Y','frequency'))

        self.gui.doubleSpinBox_amplitudeY.valueChanged.connect(lambda: self.set_value('Z','amplitude'))
        self.gui.doubleSpinBox_frequencyY.valueChanged.connect(lambda: self.set_value('Z','frequency'))

        self.gui.pushButton_configurateStepper.clicked.connect(self.configure_stepper)

        #combobox movements of stepper
        self.gui.comboBox_kindOfMove.setCurrentText(self.current_move)
        self.gui.comboBox_kindOfMove.currentTextChanged.connect(self.get_move)

        self.gui.comboBox_unit.setCurrentText('um')
        self.gui.doubleSpinBox_distance.setValue(self.distance.m_as('um'))
        self.gui.doubleSpinBox_distance.valueChanged.connect(self.set_distance)
        self.gui.comboBox_unit.currentTextChanged.connect(self.set_distance)

        self.gui.pushButton_left.clicked.connect(lambda: self.move('left'))
        self.gui.pushButton_right.clicked.connect(lambda: self.move('right'))
        self.gui.pushButton_up.clicked.connect(lambda: self.move('up'))
        self.gui.pushButton_down.clicked.connect(lambda: self.move('down'))

        # self.gui.label_speed_stepX.setText('speed X')
        # self.gui.label_speed_stepY.setText('speed Y')
        #
        # self.gui.label_speedsize_stepsizeX.setText(str(self.anc350_instrument.Speed[0] * ur('nm/s').to('um/s')))
        # self.gui.label_speedsize_stepsizeY.setText(str(self.anc350_instrument.Speed[2] * ur('nm/s').to('um/s')))
        # self.gui.label_speedsize_stepsizeZ.setText(str(self.anc350_instrument.Speed[1] * ur('nm/s').to('um/s')))

        # self.gui.groupBox_infoXY.setEnabled(True)
        # self.gui.groupBox_infoZ.setEnabled(False)
        # self.gui.groupBox_distance.setEnabled(False)

        #combobox scanner
        self.gui.doubleSpinBox_scannerX.setValue(self.settings['dcX'])
        self.gui.doubleSpinBox_scannerY.setValue(self.settings['dcY'])
        self.gui.doubleSpinBox_scannerZ.setValue(self.settings['dcZ'])

        self.gui.doubleSpinBox_scannerX.valueChanged.connect(lambda: self.set_value('X','dc'))
        self.gui.doubleSpinBox_scannerY.valueChanged.connect(lambda: self.set_value('Y','dc'))
        self.gui.doubleSpinBox_scannerZ.valueChanged.connect(lambda: self.set_value('Z','dc'))

    def show_position(self, axis):
        "Would be nice if this function would keep the position updated"
        pass

    def update_gui(self):
        "Would be nice if this method would keep the gui updated"
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
        self.logger.debug('current axis:' + str(self.current_axis))

        if 'Stepper' in self.current_axis:
            #Disable the scanner box, enable the configure box + show blue edge
            self.gui.groupBox_scanner.setEnabled(False)
            self.gui.groupBox_scanner.setStyleSheet("QGroupBox default")

            self.gui.groupBox_configurate.setEnabled(True)
            self.gui.groupBox_configurate.setStyleSheet("QGroupBox#Colored_configure {border: 1px solid blue;}")

            self.gui.groupBox_moving.setEnabled(False)
            self.gui.groupBox_moving.setStyleSheet("QGroupBox default")

            if 'Z' in self.current_axis:
                #Disable the xy groupboxes, enable the z groupboxes
                self.gui.groupBox_XY.setEnabled(False)
                self.gui.groupBox_Z.setEnabled(True)

                self.gui.groupBox_amplZ.setEnabled(True)
                self.gui.groupBox_amplXY.setEnabled(False)

                self.gui.pushButton_up.setEnabled(False)
                self.gui.pushButton_down.setEnabled(False)
                self.gui.pushButton_left.setText('closer')
                self.gui.pushButton_right.setText('away')

                self.gui.groupBox_infoXY.setEnabled(False)
                self.gui.groupBox_infoZ.setEnabled(True)
            else:
                #Enable the xy groupboxes, disable the z groupboxes
                self.gui.groupBox_XY.setEnabled(True)
                self.gui.groupBox_Z.setEnabled(False)

                self.gui.groupBox_amplZ.setEnabled(False)
                self.gui.groupBox_amplXY.setEnabled(True)

                self.gui.pushButton_up.setEnabled(True)
                self.gui.pushButton_down.setEnabled(True)
                self.gui.pushButton_left.setText('left')
                self.gui.pushButton_right.setText('right')

                self.gui.groupBox_infoXY.setEnabled(True)
                self.gui.groupBox_infoZ.setEnabled(False)

        elif 'Scanner' in self.current_axis:
            #Enable the scanner box, disable the stepper boxes
            self.gui.groupBox_scanner.setEnabled(True)
            self.gui.groupBox_configurate.setEnabled(False)
            self.gui.groupBox_moving.setEnabled(False)

            self.gui.groupBox_configurate.setStyleSheet("QGroupBox default")
            self.gui.groupBox_moving.setStyleSheet("QGroupBox default")

            self.gui.groupBox_scanner.setObjectName("Colored_scanner")
            self.gui.groupBox_scanner.setStyleSheet("QGroupBox#Colored_scanner {border: 1px solid blue;}")

            if 'Z' in self.current_axis:
                self.gui.groupBox_scanXY.setEnabled(False)
                self.gui.groupBox_scanZ.setEnabled(True)
            else:
                self.gui.groupBox_scanXY.setEnabled(True)
                self.gui.groupBox_scanZ.setEnabled(False)


    def set_value(self, axis, value_type):
        """| Reads the value that the user filled in: amplitude, frequency or dc level on scanner
        | Sets either the user input or the default amplitudes/frequencies as in the dictionary
        | The value is saved in self.settings
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

        # Store the new value in the dictionary in the init
        self.logger.debug(local_axis_name)
        self.settings[local_axis_name] = int(self.sender().value())
        self.logger.debug(self.settings)
        self.logger.debug('axis changed: ' + str(local_axis_name))
        self.logger.debug('value put: ' + str(self.settings[local_axis_name]))

        if value_type == 'dc':
            self.move_scanner(local_axis_name)

    def set_distance(self):
        """| Works similar to set_value method, but now only for the distance spinBox and unit
        | Combines value of spinbox with unit to make pint quantity and checks against maximum value defined up
        | Either applies the dictionary value of the distance, or changes that dictionary value and than applies it
        """
        distance = self.gui.doubleSpinBox_distance.value()
        unit = self.gui.comboBox_unit.currentText()

        local_distance = ur(str(distance)+unit)
        self.logger.debug('local distance value: ' + str(local_distance))

        if local_distance > self.max_distance:
            self.logger.debug('value too high')
            local_max = self.max_distance.to(unit)
            self.logger.debug(local_max)
            self.gui.doubleSpinBox_distance.setValue(local_max.m_as(unit))
        elif local_distance < 0:
            self.logger.debug('value too low')
            self.gui.doubleSpinBox_distance.setValue(0)

        self.distance = local_distance
        self.logger.debug('dictionary distance changed to: ' + str(self.distance))


    def configure_stepper(self):
        """| Configurates the stepper, using the amplitude and frequency that had been set in set_frequency and set_amplitude
        | After configuration, the box with all the different moves is enabled
        """
        self.logger.info('configurating stepper')
        if 'Z' in self.current_axis:
            self.anc350_instrument.configure_stepper('ZPiezoStepper', self.settings['amplitudeZ'] * ur('V'), self.settings['frequencyZ'] * ur('Hz'))
        else:
            self.anc350_instrument.configure_stepper('XPiezoStepper', self.settings['amplitudeX'] * ur('V'), self.settings['frequencyX'] * ur('Hz'))
            self.anc350_instrument.configure_stepper('YPiezoStepper', self.settings['amplitudeY'] * ur('V'), self.settings['frequencyY'] * ur('Hz'))

        self.gui.groupBox_moving.setEnabled(True)
        self.gui.groupBox_moving.setObjectName("ColoredGroupBox")
        self.gui.groupBox_moving.setStyleSheet("QGroupBox#ColoredGroupBox {border: 1px solid blue;}")

        self.gui.groupBox_configurate.setStyleSheet("QGroupBox default")


    def move_scanner(self, axis):
        """| Moves the scanner
        | Is called by set_value, moves as soon as the user clicked Enter

        :param axis: axis as they are called in the dictionary self.stepper_settings: dcX, dcY, dcZ
        :type axis: string
        """
        self.logger.info('moving the scanner ' + axis)
        self.logger.debug(self.settings)
        if 'Z' in axis:
            self.anc350_instrument.move_scanner('ZPiezoScanner',self.settings[axis]*ur('V'))
        elif 'X' in axis:
            self.anc350_instrument.move_scanner('XPiezoScanner', self.settings[axis] * ur('V'))
        elif 'Y' in axis:
            self.anc350_instrument.move_scanner('YPiezoScanner', self.settings[axis] * ur('V'))

    def get_move(self):
        """| Similar to the get_axis, the box with all the moves has lots of options that get disabled or enabled
        | When continuous is selected, it gives you the speed in the selected axes
        | When step is selected, it gives you the stepsize of the selected axes
        | When move absolute or move relative are selected, the user can enter the desired position/distance
        """

        self.current_move = self.gui.comboBox_kindOfMove.currentText()
        self.logger.debug('current way of moving: ' + str(self.current_move))

        if 'absolute' in self.current_move:
            #disable all buttons, except for one, to move
            self.gui.pushButton_left.setEnabled(False)
            self.gui.pushButton_up.setEnabled(False)
            self.gui.pushButton_down.setEnabled(False)
            self.gui.pushButton_right.setText('move')
        else:
            #enable the buttons that were disabled in move absolute
            if 'Z' in self.current_axis:
                self.gui.pushButton_left.setEnabled(True)
                self.gui.pushButton_up.setEnabled(False)
                self.gui.pushButton_down.setEnabled(False)
                self.gui.pushButton_right.setText('away')
            else:
                self.gui.pushButton_left.setEnabled(True)
                self.gui.pushButton_up.setEnabled(True)
                self.gui.pushButton_down.setEnabled(True)
                self.gui.pushButton_right.setText('right')

        if self.current_move == 'move relative':
            #disable the info box (with speed or step size), enable user input posibility
            self.gui.label_sortMove.setText('to relative distance')
            self.gui.groupBox_infoXY.setEnabled(False)
            self.gui.groupBox_infoZ.setEnabled(False)
            self.gui.groupBox_distance.setEnabled(True)

        elif self.current_move == 'move absolute':
            # disable the info box (with speed or step size), enable user input posibility
            self.gui.label_sortMove.setText('to absolute position')
            self.gui.groupBox_infoXY.setEnabled(False)
            self.gui.groupBox_infoZ.setEnabled(False)
            self.gui.groupBox_distance.setEnabled(True)

        elif self.current_move == 'continuous':
            #disable the user input possibility, show either the speed of current axes (depends on amplitude)
            if 'Z' in self.current_axis:
                self.gui.label_speedsize_stepsizeZ.setText(str(self.anc350_instrument.Speed[1] * ur('nm/s').to('um/s')))
                self.gui.groupBox_infoXY.setEnabled(False)
                self.gui.groupBox_infoZ.setEnabled(True)
            else:
                self.gui.label_speed_stepX.setText('speed X')
                self.gui.label_speed_stepY.setText('speed Y')

                self.gui.label_speedsize_stepsizeX.setText(str(self.anc350_instrument.Speed[0]*ur('nm/s').to('um/s')))
                self.gui.label_speedsize_stepsizeY.setText(str(self.anc350_instrument.Speed[2] * ur('nm/s').to('um/s')))
                self.gui.groupBox_infoXY.setEnabled(True)
                self.gui.groupBox_infoZ.setEnabled(False)

            self.gui.groupBox_distance.setEnabled(False)

        elif self.current_move == 'step':
            # disable the user input possibility, show either the step size on current axes (depends on frequency)
            if 'Z' in self.current_axis:
                self.gui.label_speed_stepZ.setText('step size Z')
                self.gui.label_speedsize_stepsizeZ.setText(str(self.anc350_instrument.Stepwidth[1]*ur('nm')))
                self.gui.groupBox_infoXY.setEnabled(False)
                self.gui.groupBox_infoZ.setEnabled(True)
            else:
                self.gui.label_speed_stepX.setText('step size X')
                self.gui.label_speed_stepY.setText('step size Y')
                self.gui.label_speedsize_stepsizeX.setText(str(self.anc350_instrument.Stepwidth[0] * ur('nm')))
                self.gui.label_speedsize_stepsizeY.setText(str(self.anc350_instrument.Stepwidth[2] * ur('nm')))
                self.gui.groupBox_infoXY.setEnabled(True)
                self.gui.groupBox_infoZ.setEnabled(False)

            self.gui.groupBox_distance.setEnabled(False)


    def move(self, direction):
        """| Here the actual move takes place, after the user clicked on one of the four directional buttons
        | The clicked button determines the direction that is chosen
        | For the continuous and step move, that is than converted to 0 or 1
        | This is correct as it is written right now, I checked it
        | For the relative move, the direction is than converted in adding a minus sign or not
        | ** Continuous only works for 1s, since the stop button doesnt work yet**

        :param direction: direction of move, left, right, up, down
        :type direction: string
        """

        self.direction = direction
        self.logger.debug('current direction: ' + direction)

        #remember axis name that instrument thinks in
        if 'Z' in self.current_axis:
            axis_string = 'ZPiezoStepper'
        else:
            if self.direction == 'left' or self.direction == 'right':
                axis_string = 'XPiezoStepper'
            else:
                axis_string = 'YPiezoStepper'

        if self.current_move == 'move absolute':
            #combine the spinbox and unit combobox user input to a pint quantity
            self.logger.info('moving to an absolute position')
            distance = self.gui.doubleSpinBox_distance.value()
            unit = self.gui.comboBox_unit.currentText()

            self.logger.debug('axis: ' + axis_string)
            local_distance = ur(str(distance) + unit)
            self.logger.debug('to position: ' + str(local_distance))

            self.anc350_instrument.move_to(axis_string, local_distance)

        elif self.current_move == 'move relative':
            # combine the spinbox and unit combobox user input to a pint quantity
            # add minussign to communicate correct direction to instrument
            self.logger.info('moving relative')
            distance = self.gui.doubleSpinBox_distance.value()
            unit = self.gui.comboBox_unit.currentText()
            self.logger.debug('axis:' + axis_string)
            self.logger.debug('direction: '+ direction)

            if self.direction == 'right' or self.direction == 'up':
                local_distance = ur(str(distance) + unit)
                self.logger.debug(str(local_distance))
            elif self.direction == 'left' or self.direction == 'down':
                local_distance = ur(str(-1 * distance) + unit)
                self.logger.debug(str(local_distance))

            self.anc350_instrument.move_relative(axis_string, local_distance)

        elif self.current_move == 'continuous' or self.current_move == 'step':
            # convert direction buttons clicked to direction integers that instrument wants
            # than move for 1s continuously, since the stop button doesnt work yet
            if self.direction == 'left':
                if 'Z' in self.current_axis:
                    direction_int = 0       # correct direction, corresponds to labels closer and away
                else:
                    direction_int = 1
            elif self.direction == 'right':
                if 'Z' in self.current_axis:
                    direction_int = 1       # correct direction, corresponds to labels closer and away
                else:
                    direction_int = 0
            elif self.direction == 'up':
                direction_int = 0
            elif self.direction == 'down':
                direction_int = 1

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
        | **Does not work yet, since there are not threads**
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

