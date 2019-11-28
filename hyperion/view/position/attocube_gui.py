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
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from hyperion.instrument.position.anc_instrument import Anc350Instrument
from hyperion.view.base_guis import BaseGui
from hyperion.view.general_worker import WorkThread

class Attocube_GUI(BaseGui):
    """
    | **Attocube piezo GUI for the instrument.**
    | Uses the attocube.ui file that was made with qt Designer. The maximum values for amplitude, frequency dcLevel on Scanner and distance are set here to be used in the rest of the class.
    | The start parameters for current_axis, current_move, direction and distance are set here, to be used and changed in the rest of the class.
    | A timer is started here to update the position real time.
    | A moving_thread is already made here, so the program doesnt break if somebody clicks stop before he has moved anywhere.

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

        self.current_positions = {}

        self.current_axis = 'X,Y Piezo Stepper'
        self.current_move = 'continuous'
        self.direction = 'left'
        self.distance = 0*ur('um')

        self.settings = {'amplitudeX': 30, 'amplitudeY': 40, 'amplitudeZ': 30,
                                       'frequencyX': 100, 'frequencyY': 100, 'frequencyZ': 100, 'dcX': 1, 'dcY': 1, 'dcZ': 1}

        self.initUI()

        #This one is to continuously (= every 100ms) show the position of the axes
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_position)
        self.timer.start(100)       #time in ms

        self.moving_thread = WorkThread(self.anc350_instrument.move_to, self.current_axis, self.distance)

    def initUI(self):
        """Connect all buttons, comboBoxes and doubleSpinBoxes to methods
        """
        self.logger.debug('Setting up the Measurement GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.show()

        self.make_combobox_scanner()
        self.make_combobox_movements()
        self.make_combobox_configurate()
        self.make_combobox_basic()

    def make_combobox_basic(self):
        """| *Layout of basic combobox*
        | Sets the blue border, the colour of the stop button and disables all other comboboxes.
        | Connects buttons and show_position, which works with a timer that is started in the init of this class.
        """
        self.gui.groupBox_basic.setObjectName("Colored_basic")
        self.gui.groupBox_basic.setStyleSheet("QGroupBox#Colored_basic {border: 2px solid blue;}")

        self.gui.groupBox_configurate.setObjectName("Colored_configure")
        self.gui.groupBox_configurate.setStyleSheet("QGroupBox#Colored_configure {border: 2px solid blue;}")

        #combobox basic
        self.gui.comboBox_axis.setCurrentText(self.current_axis)
        self.gui.comboBox_axis.currentTextChanged.connect(self.get_axis)
        self.gui.pushButton_stop.clicked.connect(self.stop_moving)

        self.gui.groupBox_moving.setEnabled(False)
        self.gui.groupBox_scanner.setEnabled(False)

        self.show_position()

        self.pushButton_stop.setStyleSheet("background-color: red")
        self.gui.groupBox_XY.setEnabled(True)
        self.gui.groupBox_Z.setEnabled(False)

    def make_combobox_configurate(self):
        """| *Layout of configurate combobox*
        | Sets the blue border. Connects the spinboxes to methode set_value.
        | Values are read and remembered in the whole class. Connects the configurate button.
        """
        self.gui.doubleSpinBox_amplitudeX.setValue(self.settings['amplitudeX'])
        self.gui.doubleSpinBox_frequencyX.setValue(self.settings['frequencyX'])

        self.gui.doubleSpinBox_amplitudeY.setValue(self.settings['amplitudeY'])
        self.gui.doubleSpinBox_frequencyY.setValue(self.settings['frequencyY'])

        self.gui.doubleSpinBox_amplitudeZ.setValue(self.settings['amplitudeZ'])
        self.gui.doubleSpinBox_frequencyZ.setValue(self.settings['frequencyZ'])

        self.gui.doubleSpinBox_frequencyX.valueChanged.connect(lambda: self.set_value('X','frequency'))
        self.gui.doubleSpinBox_amplitudeX.valueChanged.connect(lambda: self.set_value('X','amplitude'))

        self.gui.doubleSpinBox_amplitudeY.valueChanged.connect(lambda: self.set_value('Y','amplitude'))
        self.gui.doubleSpinBox_frequencyY.valueChanged.connect(lambda: self.set_value('Y','frequency'))

        self.gui.doubleSpinBox_amplitudeY.valueChanged.connect(lambda: self.set_value('Z','amplitude'))
        self.gui.doubleSpinBox_frequencyY.valueChanged.connect(lambda: self.set_value('Z','frequency'))

        self.gui.pushButton_configurateStepper.clicked.connect(self.configure_stepper)

        self.get_axis()

    def make_combobox_movements(self):
        """| *Layout of combobox of all movements*
        | Sets the blue border. Runs the self.get_move method to find out what kind of movement is selected (step, continuous, ...).
        | Connects the spinbox and unit combobox to method set_value. Values are read and remembered in the whole class.
        | Connects all buttons to the methode self.move, that figures out in which way and direction to move.
        """
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

    def make_combobox_scanner(self):
        """| *Layout of scanner combobox*
        | Connects the spinboxes to set_value, that in case of the scanner will immediately put the voltage to move the scanner.
        """
        self.gui.doubleSpinBox_scannerX.setValue(self.settings['dcX'])
        self.gui.doubleSpinBox_scannerY.setValue(self.settings['dcY'])
        self.gui.doubleSpinBox_scannerZ.setValue(self.settings['dcZ'])

        self.gui.doubleSpinBox_scannerX.valueChanged.connect(lambda: self.set_value('X','dc'))
        self.gui.doubleSpinBox_scannerY.valueChanged.connect(lambda: self.set_value('Y','dc'))
        self.gui.doubleSpinBox_scannerZ.valueChanged.connect(lambda: self.set_value('Z','dc'))

    def show_position(self):
        """In the instrument level, the current positions are remembered in a dictionary and updated through get_position.
        This method read them out (continuously, through the timer in the init) and displays their values.
        """
        self.current_positions = self.anc350_instrument.current_positions

        self.gui.label_actualPositionX.setText(str(self.current_positions['XPiezoStepper']))
        self.gui.label_actualPositionY.setText(str(self.current_positions['YPiezoStepper']))
        self.gui.label_actualPositionZ.setText(str(self.current_positions['ZPiezoStepper']))

    def get_axis(self):
        """| *Layout enabling and disabling plus blue borders*
        | Depending on the selected axis, the gui looks differently.
        | - The basic box is always enabled.
        | - If one of the Steppers is selected, only the configuration box is enabled.
        | - After configuration, also the box with all the moves will be enabled.
        | - If one of the Scanners is selected, only the scanner box is enabled.
        | - When the Z Piezo Stepper is selected, all of the X values change to Z, and the Y values are disabled.
        | - When the Z Piezo Scanner is selected, similar but now only for the two boxes in the scanner part.
        | - **Important** self.current_axis is saved here and used in the whole program.
        """
        self.current_axis = self.gui.comboBox_axis.currentText()
        self.logger.debug('current axis:' + str(self.current_axis))

        if 'Stepper' in self.current_axis:
            #Disable the scanner box, enable the configure box + show blue border
            self.gui.groupBox_scanner.setEnabled(False)
            self.gui.groupBox_scanner.setStyleSheet("QGroupBox default")

            self.gui.groupBox_configurate.setEnabled(True)
            self.gui.groupBox_configurate.setStyleSheet("QGroupBox#Colored_configure {border: 2px solid blue;}")

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
            self.gui.groupBox_scanner.setStyleSheet("QGroupBox#Colored_scanner {border: 2px solid blue;}")

            if 'Z' in self.current_axis:
                self.gui.groupBox_scanXY.setEnabled(False)
                self.gui.groupBox_scanZ.setEnabled(True)
            else:
                self.gui.groupBox_scanXY.setEnabled(True)
                self.gui.groupBox_scanZ.setEnabled(False)

    def get_move(self):
        """| *Layout of all moving options*
        | Similar to the get_axis, the box with all the moves has lots of options that get disabled or enabled.
        | - When continuous is selected, it gives you the speed in the selected axes.
        | - When step is selected, it gives you the stepsize of the selected axes.
        | - When move absolute or move relative are selected, the user can enter the desired position/distance.
        """

        self.current_move = self.gui.comboBox_kindOfMove.currentText()
        self.logger.debug('current way of moving: ' + str(self.current_move))

        if 'absolute' in self.current_move:
            #disable all buttons, except for one or two, to move
            if 'Z' in self.current_axis:
                self.gui.pushButton_left.setEnabled(False)
                self.gui.pushButton_up.setEnabled(False)
                self.gui.pushButton_down.setEnabled(False)
                self.gui.pushButton_right.setText('move Z')
            else:
                self.gui.pushButton_left.setEnabled(False)
                self.gui.pushButton_up.setText('move Y')
                self.gui.pushButton_down.setEnabled(False)
                self.gui.pushButton_right.setText('move X')
        else:
            #enable the buttons that were disabled in move absolute
            if 'Z' in self.current_axis:
                self.gui.pushButton_left.setEnabled(True)
                self.gui.pushButton_up.setEnabled(False)
                self.gui.pushButton_down.setEnabled(False)
                self.gui.pushButton_right.setText('away')
            else:
                self.gui.pushButton_left.setEnabled(True)
                self.gui.pushButton_up.setText('up')
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

    def set_value(self, axis, value_type):
        """| Reads the values that the user filled in: amplitude, frequency or dc level on scanner.
        | Sets either the user input or the default amplitudes/frequencies as in the dictionary. The value is saved in self.settings.
        | If X and Y Scanner are selected, values are set separately; with Z, there is only one spinbox to fill in.
        | Values from dictionary are used in configure_stepper, but only if the user clicks configure.
        | axis and value_type are locally changed into the name as known in the dictionaries, like amplitudeX or dcZ.
        | If scanner values were changed, this method calls to moving of the the scanner as soon as the user clicks Enter.

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
        """Works similar to set_value method, but now only for the distance spinBox and unit.
        Combines value of spinbox with unit to make pint quantity and checks against maximum value defined up.
        Either applies the dictionary value of the distance, or changes that dictionary value and than applies it.
        """
        distance = self.gui.doubleSpinBox_distance.value()
        unit = self.gui.comboBox_unit.currentText()

        local_distance = ur(str(distance)+unit)
        self.logger.debug('local distance value: ' + str(local_distance))

        if local_distance > self.max_distance:
            self.logger.debug('value too high')
            local_max = self.max_distance.to(unit)
            self.logger.debug(str(local_max))
            self.gui.doubleSpinBox_distance.setValue(local_max.m_as(unit))
        elif local_distance < 0:
            self.logger.debug('value too low')
            self.gui.doubleSpinBox_distance.setValue(0)

        self.distance = local_distance
        self.logger.debug('dictionary distance changed to: ' + str(self.distance))

    def configure_stepper(self):
        """Configures the stepper, using the amplitude and frequency that had been set in set_frequency and set_amplitude.
        After configuration, the box with all the different moves is enabled
        and the get_move is run to set the layout fit for the current move.
        """
        self.logger.info('configurating stepper')
        if 'Z' in self.current_axis:
            self.anc350_instrument.configure_stepper('ZPiezoStepper', self.settings['amplitudeZ'] * ur('V'), self.settings['frequencyZ'] * ur('Hz'))
        else:
            self.anc350_instrument.configure_stepper('XPiezoStepper', self.settings['amplitudeX'] * ur('V'), self.settings['frequencyX'] * ur('Hz'))
            self.anc350_instrument.configure_stepper('YPiezoStepper', self.settings['amplitudeY'] * ur('V'), self.settings['frequencyY'] * ur('Hz'))

        self.gui.groupBox_moving.setEnabled(True)
        self.gui.groupBox_moving.setObjectName("ColoredGroupBox")
        self.gui.groupBox_moving.setStyleSheet("QGroupBox#ColoredGroupBox {border: 2px solid blue;}")

        self.gui.groupBox_configurate.setStyleSheet("QGroupBox default")

        self.get_move()

    def move_scanner(self, axis):
        """| Moves the scanner.
        | Is called by set_value, moves as soon as the user clicked Enter.

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

    def move(self, direction):
        """| Here the actual move takes place, after the user clicked on one of the four directional buttons.
        | The clicked button determines the direction that is chosen.
        | - For the continuous and step move, that is than converted to 0 or 1.
        | This is correct as it is written right now, I checked it.
        | - For the relative move, the direction is than converted in adding a minus sign or not.
        | - For every kind of move, the self.moving_thread is started, so the stop button can be used and the position label can be updated.
        | I gave this thread the same name every time, don't know whether that is bad practice. The thread is quit in the stop method.

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

            self.moving_thread = WorkThread(self.anc350_instrument.move_to,axis_string, local_distance)
            self.moving_thread.start()

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

            self.moving_thread = WorkThread(self.anc350_instrument.move_relative,axis_string, local_distance)
            self.moving_thread.start()

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
                self.logger.info('moving continuously')
                self.moving_thread = WorkThread(self.anc350_instrument.move_continuous, axis_string, direction_int)
                self.moving_thread.start()

            elif self.current_move == 'step':
                self.logger.info('making a step')
                self.anc350_instrument.given_step(axis_string, direction_int, 1)
                self.show_position()

    def stop_moving(self):
        """| Stops movement of all steppers.
        | The check_if_moving loop in the instrument level checks whether the stop is True, and if so, breaks the loop.
        | Similar for a loop in the move_continuous in the instrument level, that checks for the stop.
        | The stop_moving in the instrument level actually stops the device.
        | Because of the moving_thread that is started in the method move in this class, the loops in the methods in instrument actually keep checking for this stop value.
        """
        self.logger.info('stop moving')
        self.anc350_instrument.stop = True
        self.anc350_instrument.stop_moving('XPiezoStepper')
        self.anc350_instrument.stop_moving('YPiezoStepper')
        self.anc350_instrument.stop_moving('ZPiezoStepper')

        if self.moving_thread.isRunning:
            print('is running')
            self.moving_thread.quit()

        self.anc350_instrument.stop = False


if __name__ == '__main__':
    import hyperion

    with Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350'}) as anc350_instrument:
        app = QApplication(sys.argv)
        ex = Attocube_GUI(anc350_instrument)
        sys.exit(app.exec_())

