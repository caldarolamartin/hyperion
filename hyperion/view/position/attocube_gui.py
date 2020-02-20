"""
===================
Attocube GUI
===================

This is to build a gui for the instrument piezo motor attocube.


"""
import sys, os
from hyperion import logging
from hyperion import ur
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
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
    def __init__(self, anc350_instrument, also_close_output=False):
        """Attocube
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.title = 'Attocube GUI'
        self.anc350_instrument = anc350_instrument

        name = 'attocube.ui'
        gui_folder = os.path.dirname(os.path.abspath(__file__))
        gui_file = os.path.join(gui_folder, name)
        self.logger.debug('Loading the GUI file: {}'.format(gui_file))
        self.gui = uic.loadUi(gui_file, self)

        self.max_amplitude_V = 60
        self.max_frequency = 2000
        self.max_dclevel_V = 60 * ur('V')          #Pay attention: this max only goes for 4K,
        self.max_dcLevel_mV_300K = 60 * ur('V')       #at room temperature use 60V as max
        self.max_distance = 5*ur('mm')

        self.current_positions = {}

        self.current_axis = 'X,Y Piezo Stepper'
        self.current_move = 'step'
        self.direction = 'left'
        self.distance = 0*ur('um')

        self.settings = {'amplitudeX': 30, 'amplitudeY': 40, 'amplitudeZ': 30,
                                       'frequencyX': 1000, 'frequencyY': 1000, 'frequencyZ': 1000}

        self.temperature = 300

        self.scanner_unitX = 'V'
        self.scanner_unitY = 'V'
        self.scanner_unitZ = 'V'

        self.dcX = 1*ur(self.scanner_unitX)
        self.dcY = 1*ur(self.scanner_unitY)
        self.dcZ = 0*ur(self.scanner_unitZ)

        self.stop = self.stop_moving

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
        self.gui.groupBox_basic.setStyleSheet("QGroupBox#Colored_basic {border: 1px solid blue; border-radius: 9px;}")

        self.gui.groupBox_configurate.setObjectName("Colored_configure")
        self.gui.groupBox_configurate.setStyleSheet("QGroupBox#Colored_configure {border: 1px solid blue; border-radius: 9px;}")

        #combobox basic
        self.gui.comboBox_axis.setCurrentText(self.current_axis)
        self.gui.comboBox_axis.currentTextChanged.connect(self.get_axis)

        self.gui.pushButton_stop.clicked.connect(self.stop_moving)
        self.pushButton_stop.setStyleSheet("background-color: red")

        self.gui.doubleSpinBox_temperature.setValue(self.temperature)
        self.set_temperature()
        self.gui.doubleSpinBox_temperature.valueChanged.connect(self.set_temperature)

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

        # self.gui.pushButton_left.setCheckable(True)
        # self.gui.pushButton_left.toggle()
        self.gui.pushButton_left.clicked.connect(lambda: self.move('left'))
        self.gui.pushButton_right.clicked.connect(lambda: self.move('right'))
        self.gui.pushButton_up.clicked.connect(lambda: self.move('up'))
        self.gui.pushButton_down.clicked.connect(lambda: self.move('down'))

    def make_combobox_scanner(self):
        """| *Layout of scanner combobox*
        | Connects the spinboxes to set_value, that in case of the scanner will immediately put the voltage to move the scanner.
        """
        self.gui.comboBox_unitX.setCurrentText(self.scanner_unitX)
        self.gui.comboBox_unitX.currentTextChanged.connect(lambda: self.set_scanner_position('X'))

        self.gui.comboBox_unitY.setCurrentText(self.scanner_unitY)
        self.gui.comboBox_unitY.currentTextChanged.connect(lambda: self.set_scanner_position('Y'))

        self.gui.comboBox_unitZ.setCurrentText(self.scanner_unitZ)
        self.gui.comboBox_unitZ.currentTextChanged.connect(lambda: self.set_scanner_position('Z'))

        self.gui.doubleSpinBox_scannerX.setValue(int(self.dcX.m_as('V')))
        self.gui.doubleSpinBox_scannerY.setValue(int(self.dcY.m_as('V')))
        self.gui.doubleSpinBox_scannerZ.setValue(int(self.dcZ.m_as('V')))

        self.move_scanner('dCX')
        self.move_scanner('dCY')
        self.move_scanner('dCZ')

        self.gui.doubleSpinBox_scannerX.valueChanged.connect(lambda: self.set_scanner_position('X'))
        self.gui.doubleSpinBox_scannerY.valueChanged.connect(lambda: self.set_scanner_position('Y'))
        self.gui.doubleSpinBox_scannerZ.valueChanged.connect(lambda: self.set_scanner_position('Z'))

        self.gui.pushButton_zero_scanners.clicked.connect(self.zero_scanners)

    def show_position(self):
        """In the instrument level, the current positions of both Stepper and Scanner are remembered in a dictionary and updated through get_position.
        This method read them out (continuously, through the timer in the init) and displays their values.
        """
        self.anc350_instrument.update_all_positions()

        self.current_positions = self.anc350_instrument.current_positions

        self.gui.label_actualPositionX.setText(str(self.current_positions['XPiezoStepper']))
        self.gui.label_actualPositionY.setText(str(self.current_positions['YPiezoStepper']))
        self.gui.label_actualPositionZ.setText(str(self.current_positions['ZPiezoStepper']))

        self.gui.scan_positionX.setText(str(self.current_positions['XPiezoScanner']))
        self.gui.scan_positionY.setText(str(self.current_positions['YPiezoScanner']))
        self.gui.scan_positionZ.setText(str(self.current_positions['ZPiezoScanner']))

    def get_axis(self):
        """| *Layout stacked widgets plus blue borders*
        | Depending on the selected axis, the gui looks differently.
        | - The basic box is always enabled.
        | - If one of the Steppers is selected, only the configuration box is shown.
        | - After configuration, also the box with all the moves will be enabled.
        | - If one of the Scanners is selected, only the scanner box is shown.
        | - When the Z Piezo Stepper is selected, all of the X values change to Z.
        | - When the Z Piezo Scanner is selected, similar but now only for the two boxes in the scanner part.
        | - **Important** self.current_axis is saved here and used in the whole program.
        """
        self.current_axis = self.gui.comboBox_axis.currentText()
        self.logger.debug('current axis:' + str(self.current_axis))

        if 'Stepper' in self.current_axis:
            #self.gui.groupBox_configurate.setEnabled(True)
            self.gui.groupBox_configurate.setStyleSheet("QGroupBox#Colored_configure {border: 1px solid blue; border-radius: 9px;}")

            self.gui.groupBox_actions.setStyleSheet("QGroupBox default")

            self.gui.stackedWidget_actions.setCurrentWidget(self.gui.page_configure_stepper)
            self.gui.stackedWidget_stepper.setCurrentWidget(self.gui.stackedWidgetMoving)
            self.gui.stackedWidgetMoving.setEnabled(False)

            if 'Z' in self.current_axis:
                #Disable the xy groupboxes, enable the z groupboxes,
                # choose the page_amplZ of the stackedWidget_configure
                self.gui.groupBox_XY.setEnabled(False)
                self.gui.groupBox_Z.setEnabled(True)

                self.gui.stackedWidget_configure.setCurrentWidget(self.gui.page_amplZ)

                self.gui.pushButton_up.setEnabled(False)
                self.gui.pushButton_down.setEnabled(False)
                self.gui.pushButton_left.setText('closer')
                self.gui.pushButton_right.setText('away')
            else:
                #Enable the xy groupboxes, disable the z groupboxes,
                # choose the page_amplXY of the stackedWidget_configure.

                self.gui.groupBox_XY.setEnabled(True)
                self.gui.groupBox_Z.setEnabled(False)

                self.gui.stackedWidget_configure.setCurrentWidget(self.gui.page_amplXY)

                self.gui.pushButton_up.setEnabled(True)
                self.gui.pushButton_down.setEnabled(True)
                self.gui.pushButton_left.setText('left')
                self.gui.pushButton_right.setText('right')

        elif 'Scanner' in self.current_axis:
            #Choose the page_move_scanner of the stackedWidget_actions and the stackedWidgetEmpty of the stackedWidget_stepper
            self.gui.stackedWidget_actions.setCurrentWidget(self.gui.page_move_scanner)
            self.gui.stackedWidget_stepper.setCurrentWidget(self.gui.stackedWidgetempty)

            #Give the configurate box a border and the action box none
            self.gui.groupBox_configurate.setStyleSheet("QGroupBox#Colored_configure {border: 1px solid blue; border-radius: 9px;}")
            self.gui.groupBox_actions.setStyleSheet("QGroupBox default")

            #Choose either the page_scannerZ or page_scannerXY of the stackedWidget_voltScanner
            if 'Z' in self.current_axis:
                self.gui.stackedWidget_voltScanner.setCurrentWidget(self.gui.page_scannerZ)
            else:
                self.gui.stackedWidget_voltScanner.setCurrentWidget(self.gui.page_scannerXY)

    def get_move(self):
        """| *Layout of all moving options*
        | Similar to the get_axis, the box with all the moves has lots of options that get chosen from the stacked widgets.
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
            self.gui.stackedWidget_moveDependent.setCurrentWidget(self.gui.page_distance)

        elif self.current_move == 'move absolute':
            # disable the info box (with speed or step size), enable user input posibility
            self.gui.label_sortMove.setText('to absolute position')
            self.gui.stackedWidget_moveDependent.setCurrentWidget(self.gui.page_distance)

        elif self.current_move == 'continuous':
            #disable the user input possibility, show either the speed of current axes (depends on amplitude)
            if 'Z' in self.current_axis:
                self.gui.label_speed_stepZ.setText('speed Z')
                self.gui.label_speedsize_stepsizeZ.setText(str(self.anc350_instrument.Speed[1] * ur('nm/s').to('um/s')))
                self.gui.stackedWidget_moveDependent.setCurrentWidget(self.gui.page_stepZ)
            else:
                self.gui.label_speed_stepX.setText('speed X')
                self.gui.label_speed_stepY.setText('speed Y')

                self.gui.label_speedsize_stepsizeX.setText(str(self.anc350_instrument.Speed[0]*ur('nm/s').to('um/s')))
                self.gui.label_speedsize_stepsizeY.setText(str(self.anc350_instrument.Speed[2] * ur('nm/s').to('um/s')))
                self.gui.stackedWidget_moveDependent.setCurrentWidget(self.gui.page_stepXY)

        elif self.current_move == 'step':
            # disable the user input possibility, show either the step size on current axes (depends on frequency)
            if 'Z' in self.current_axis:
                self.gui.label_speed_stepZ.setText('step size Z')
                self.gui.label_speedsize_stepsizeZ.setText(str(self.anc350_instrument.Stepwidth[1]*ur('nm')))
                self.gui.stackedWidget_moveDependent.setCurrentWidget(self.gui.page_stepZ)
            else:
                self.gui.label_speed_stepX.setText('step size X')
                self.gui.label_speed_stepY.setText('step size Y')
                self.gui.label_speedsize_stepsizeX.setText(str(self.anc350_instrument.Stepwidth[0] * ur('nm')))
                self.gui.label_speedsize_stepsizeY.setText(str(self.anc350_instrument.Stepwidth[2] * ur('nm')))
                self.gui.stackedWidget_moveDependent.setCurrentWidget(self.gui.page_stepXY)

    def set_temperature(self):
        """Set the temperature and change the scanner piezo voltage limits accordingly.
        """
        self.temperature = self.gui.doubleSpinBox_temperature.value()
        self.logger.debug('Changing the temperature to {}K'.format(self.temperature))

        self.anc350_instrument.temperature = self.temperature
        self.anc350_instrument.set_temperature_limits()

        self.max_dclevel_V = self.anc350_instrument.max_dC_level

        self.logger.debug('Changed the scanner piezo limits to {}'.format(self.max_dclevel_V))

    def set_value(self, axis, value_type):
        """| Reads the values that the user filled in: amplitude, frequency or dc level on scanner.
        | Sets either the user input or the default amplitudes/frequencies as in the dictionary. The value is saved in self.settings.
        | If X and Y Scanner are selected, values are set separately; with Z, there is only one spinbox to fill in.
        | Values from dictionary are used in configure_stepper, but only if the user clicks configure.
        | axis and value_type are locally changed into the name as known in the dictionaries, like amplitudeX or dcZ.

        :param axis: axis X, Y, Z
        :type axis: string

        :param value_type: amplitude, frequency or dc
        :type value_type: string
        """
        self.logger.debug('changing a user input value')
        local_axis_name = value_type + axis

        if value_type == 'amplitude':
            self.logger.debug('changing the amplitude')
            max_value = self.max_amplitude_V
        elif value_type == 'frequency':
            self.logger.debug('changing the frequency')
            max_value = self.max_frequency

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

    def set_scanner_position(self, axis):
        """To make it possible to use both V and mV for the scanner.
        The value of the spinbox and the unit in the combobox are combined.
        Then they are tested against the maximum and minimum values.
        If they are labeled too high or too low, the user input is changed to the maximum or minimum value.

        :param axis: axis X, Y, Z
        :type axis: string
        """
        change = 'not'

        if axis == 'X':
            scanner_pos = self.gui.doubleSpinBox_scannerX.value()
            self.scanner_unitX = self.gui.comboBox_unitX.currentText()
            scanner_unit = self.scanner_unitX
        elif axis == 'Y':
            scanner_pos = self.gui.doubleSpinBox_scannerY.value()
            self.scanner_unitY = self.gui.comboBox_unitY.currentText()
            scanner_unit = self.scanner_unitY
        elif axis == 'Z':
            scanner_pos = self.gui.doubleSpinBox_scannerZ.value()
            self.scanner_unitZ = self.gui.comboBox_unitZ.currentText()
            scanner_unit = self.scanner_unitZ

        local_position = ur(str(scanner_pos)+scanner_unit)
        self.logger.debug('{} local scanner position value: {}'.format(axis, local_position))

        if local_position > self.max_dclevel_V:
            self.logger.debug('value too high')
            local_max = self.max_dclevel_V.to(scanner_unit)
            self.logger.debug(str(local_max))
            change = 'high'
        elif local_position > self.max_dcLevel_mV_300K:
            self.logger.warning('You are exceeding the 60V maximum for the piezo at room temperature')
        elif local_position < 0:
            self.logger.debug('value too low')
            change = 'low'

        if axis == 'X':
            if change == 'high':
                self.gui.doubleSpinBox_scannerX.setValue(local_max.m_as(scanner_unit))
            elif change == 'low':
                self.gui.doubleSpinBox_scannerX.setValue(0)
            scanner_pos = self.gui.doubleSpinBox_scannerX.value()
            local_position = ur(str(scanner_pos) + scanner_unit)
            self.dcX = local_position
            self.logger.debug('dictionary position {} changed to: {}'.format(axis, self.dcX))

        elif axis == 'Y':
            if change == 'high':
                self.gui.doubleSpinBox_scannerY.setValue(local_max.m_as(scanner_unit))
            elif change == 'low':
                self.gui.doubleSpinBox_scannerY.setValue(0)
            scanner_pos = self.gui.doubleSpinBox_scannerY.value()
            local_position = ur(str(scanner_pos) + scanner_unit)
            self.dcY = local_position
            self.logger.debug('dictionary position {} changed to: {}'.format(axis, self.dcY))

        elif axis == 'Z':
            if change == 'high':
                self.gui.doubleSpinBox_scannerZ.setValue(local_max.m_as(scanner_unit))
            elif change == 'low':
                self.gui.doubleSpinBox_scannerZ.setValue(0)
            scanner_pos = self.gui.doubleSpinBox_scannerZ.value()
            local_position = ur(str(scanner_pos) + scanner_unit)
            self.dcZ = local_position
            self.logger.debug('dictionary position {} changed to: {}'.format(axis, self.dcZ))

        self.move_scanner('dc'+axis)

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
            distance = self.gui.doubleSpinBox_distance.value()
        elif local_distance < 0:
            self.logger.debug('value too low')
            self.gui.doubleSpinBox_distance.setValue(0)
            distance = self.gui.doubleSpinBox_distance.value()

        local_distance = ur(str(distance) + unit)           #in case something changed
        self.distance = local_distance
        self.logger.debug('dictionary distance changed to: ' + str(self.distance))

    def configure_stepper(self):
        """Configures the stepper, using the amplitude and frequency that had been set in set_frequency and set_amplitude.
        After configuration, the box with all the different moves is chosen
        and the get_move is run to set the layout fit for the current move.
        """
        self.logger.info('configurating stepper')
        if 'Z' in self.current_axis:
            self.anc350_instrument.configure_stepper('ZPiezoStepper', self.settings['amplitudeZ'] * ur('V'), self.settings['frequencyZ'] * ur('Hz'))
        else:
            self.anc350_instrument.configure_stepper('XPiezoStepper', self.settings['amplitudeX'] * ur('V'), self.settings['frequencyX'] * ur('Hz'))
            self.anc350_instrument.configure_stepper('YPiezoStepper', self.settings['amplitudeY'] * ur('V'), self.settings['frequencyY'] * ur('Hz'))

        self.gui.groupBox_actions.setObjectName("Colored_actions")
        self.gui.groupBox_actions.setStyleSheet("QGroupBox#Colored_actions {border: 1px solid blue; border-radius: 9px;}")

        self.gui.stackedWidgetMoving.setEnabled(True)

        self.get_move()

    def move_scanner(self, axis):
        """| Moves the scanner.
        | Is called by set_value, moves as soon as the user clicked Enter.

        :param axis: axis as they are called in the dictionary self.stepper_settings: dcX, dcY, dcZ
        :type axis: string
        """
        self.logger.info('moving the scanner ' + axis)

        if 'X' in axis:
            self.logger.debug('move by {}'.format(self.dcX))
            self.anc350_instrument.move_scanner('XPiezoScanner', self.dcX)
        elif 'Y' in axis:
            self.logger.debug('move by {}'.format(self.dcY))
            self.anc350_instrument.move_scanner('YPiezoScanner', self.dcY)
        elif 'Z' in axis:
            self.logger.debug('move by {}'.format(self.dcZ))
            self.anc350_instrument.move_scanner('ZPiezoScanner',self.dcZ)

    def zero_scanners(self):
        """Put 0V on all scanners.
        """
        self.logger.info('Zero all Scanners.')
        self.anc350_instrument.zero_scanners()

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
            self.moving_thread.quit()

        self.anc350_instrument.stop = False


if __name__ == '__main__':

    with Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350','temperature': 300}) as anc350_instrument:
        app = QApplication(sys.argv)
        ex = Attocube_GUI(anc350_instrument)
        sys.exit(app.exec_())

