"""
=========================
Single Thorlabs Motor GUI
=========================

Works with the new Thorlabs Motor instrument. Keyboard stuff has not been tested or updated yet.

"""
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from hyperion.instrument.position.thorlabs_motor_instr import Thorlabsmotor
from hyperion.view.general_worker import WorkThread
from hyperion.view.base_guis import BaseGui
from hyperion import ur
from pynput.keyboard import Listener
from hyperion import logging

class Thorlabs_motor_GUI(BaseGui):
    """
    | The initialization of the single_thorlabs gui.
    | Serial number and name are in the settings given underneath, so thorlabs_instrument knows them.
    | Initialize of the instrument is already done by the init of the thorlabs_instrument, that runs with the with downstairs.
    """

    def __init__(self, thorlabs_instrument):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.left = 50
        self.top = 50
        self.width = 400
        self.height = 200
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        self.motor = thorlabs_instrument
        self.logger.debug('You are connected to a {}'.format(self.motor.kind_of_device))
        self.title = 'Thorlabs {} GUI'.format(self.motor._name)

        self.saved_position = None
        self.current_position = None

        self.distance = 1.0*ur('mm')

        self.min_distance = -12.0 * ur('mm')
        self.max_distance = 12.0 * ur('mm')

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.set_current_motor_position_label)
        self.timer.start(100)       #time in ms

        self.moving_thread = WorkThread(self.motor.move_absolute, self.current_position, True)

    def initUI(self):
        self.logger.debug('Setting up the Single Thorlabs Motor GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.make_buttons()
        self.make_labels()
        self.make_misc_gui_stuff()

        self.show()
    def make_buttons(self):
        self.make_go_home_button()
        self.make_go_to_button()
        self.make_save_pos_button()
        self.make_recover_pos_button()
        self.make_keyboard_button()
        self.make_stop_button()
    def make_labels(self):
        self.make_keyboard_label()
        self.make_current_pos_label()
        self.make_save_label()
        self.make_recover_label()
        self.make_unit_combobox()
    def make_misc_gui_stuff(self):
        self.make_distance_spinbox()
        self.set_current_motor_position_label()

    def make_go_home_button(self):
        self.go_home_button = QPushButton("go home", self)
        self.go_home_button.setToolTip('go to home position')
        self.go_home_button.clicked.connect(self.go_home_motor)
        self.grid_layout.addWidget(self.go_home_button, 0, 0)
    def make_go_to_button(self):
        self.move_button = QPushButton('move to', self)
        self.move_button.setToolTip('move to given input')
        self.move_button.clicked.connect(self.go_to_input)
        self.grid_layout.addWidget(self.move_button, 1, 0)
    def make_save_pos_button(self):
        self.save_pos_button = QPushButton("save pos", self)
        self.save_pos_button.setToolTip('save the current position of the thorlabs_motor')
        self.save_pos_button.clicked.connect(self.save_position)
        self.grid_layout.addWidget(self.save_pos_button, 0, 4)
    def make_recover_pos_button(self):
        self.recover_pos_button = QPushButton("recover pos", self)
        self.recover_pos_button.setToolTip("recover the set position of the thorlabs_motor")
        self.recover_pos_button.clicked.connect(self.recover_position)
        self.grid_layout.addWidget(self.recover_pos_button, 1, 4)
    def make_keyboard_button(self):
        self.keyboard_button = QPushButton("keyboard", self)
        self.keyboard_button.setToolTip("use the keyboard to move the thorlabs_motor,\nit works great")
        self.keyboard_button.clicked.connect(self.use_keyboard)
        self.grid_layout.addWidget(self.keyboard_button, 2, 1)
    def make_stop_button(self):
        self.stop_button = QPushButton("stop moving", self)
        self.stop_button.setToolTip("stop any moving")
        self.stop_button.clicked.connect(self.stop_moving)
        self.grid_layout.addWidget(self.stop_button, 2, 4)
        self.stop_button.setStyleSheet("background-color: red")

    def make_current_pos_label(self):
        self.current_motor_position_label = QLabel(self)
        try:
            self.current_motor_position_label.setText(self.motor.position())
        except Exception:
            self.current_motor_position_label.setText("currently/nunavailable")
        self.grid_layout.addWidget(self.current_motor_position_label, 0, 1)

    def make_keyboard_label(self):
        self.keyboard_label = QLabel(self)
        self.keyboard_label.setText("use keyboard\n(w/s, q to quit)")
        self.grid_layout.addWidget(self.keyboard_label, 2, 0)
    def make_save_label(self):
        self.save_label = QLabel(self)
        self.save_label.setText("saved:")
        self.grid_layout.addWidget(self.save_label, 0, 3)
    def make_recover_label(self):
        self.recover_label = QLabel(self)
        self.recover_label.setText("recover pos:")
        self.grid_layout.addWidget(self.recover_label, 1, 3)

    def make_distance_spinbox(self):
        self.distance_spinbox = QDoubleSpinBox(self)
        if self.motor.kind_of_device == 'waveplate':
            self.distance_spinbox.setValue(self.distance.m_as('mm'))
            self.distance = self.distance.m_as('mm')*ur('degrees')
            self.min_distance = 0 * ur('degrees')
            self.max_distance = 360 * ur('degrees')
        else:
            self.distance_spinbox.setValue(self.distance.m_as('mm'))
        self.grid_layout.addWidget(self.distance_spinbox, 1, 1)
        self.distance_spinbox.setMinimum(-999999999)        #otherwise you cannot reach higher than 99
        self.distance_spinbox.setMaximum(999999999)
        self.distance_spinbox.valueChanged.connect(self.set_distance)

    def make_unit_combobox(self):
        self.unit_combobox = QComboBox(self)
        if self.motor.kind_of_device == 'waveplate':
            self.unit_combobox.addItems(["degrees"])
            self.unit_combobox.setCurrentText('degrees')
            self.unit_combobox.setEnabled(False)
        else:
            self.unit_combobox.addItems(["nm", "um", "mm"])
            self.unit_combobox.setCurrentText('mm')

        self.unit_combobox.currentTextChanged.connect(self.set_distance)
        self.grid_layout.addWidget(self.unit_combobox, 1, 3)


    def set_current_motor_position_label(self):
        """ In the instrument level, the current position is remembered and updated through self.position,
        which is called in the moving_loop during the moves.
        This method read this out (continuously, through the timer in the init) and displays the value.
        """
        self.current_position = self.motor.current_position
        self.current_motor_position_label.setText(str(round(self.current_position, 2)))


#----------------------------------------------------------------------------------------------------------------------

    def set_distance(self):
        """| Reads the value that the user filled in the spinbox and combines it with the unit to make a pint quantity.
        | The pint quantity is saved in self.distance.
        | Also compares the wanted distance with the maximum and minimum values,
        | which are set in the init or changed to degrees in make_distance_spinbox.
        | If the user input is too high or low, the spinbox is changed to the maximum or minimum value.
        """
        value = self.distance_spinbox.value()
        unit = self.unit_combobox.currentText()

        local_distance = ur(str(value)+unit)
        self.logger.debug('local distance value {}'.format(self.distance))
        self.logger.debug("{}".format(value > self.max_distance.m_as(unit)))

        if value > self.max_distance.m_as(unit):
            self.logger.debug('value too high')
            local_max = self.max_distance.to(unit)
            self.logger.debug(str(local_max))
            self.distance_spinbox.setValue(local_max.m_as(unit))
        elif value < self.min_distance.m_as(unit):
            self.logger.debug('value too low')
            local_min = self.min_distance.to(unit)
            self.distance_spinbox.setValue(local_min.m_as(unit))

        self.distance = local_distance
        self.logger.debug('dictionary distance changed to: ' + str(self.distance))

    def go_home_motor(self):
        """Starts a thread and communicates to the instrument to move home.
        The instrument loop will take care of updating the current position and checking whether self.stop is True or False.
        """
        self.moving_thread = WorkThread(self.motor.move_home, True)
        self.moving_thread.start()
        #self.motor.move_home(True)
        #self.set_current_motor_position_label()

    def go_to_input(self):
        """Starts a thread to make an absolute move with the distance that is read out in self.set_distance from the spinbox.
        Value error has become a little bit irrelevant, now that I changed to pint quantities for distance.
        """
        try:
            self.moving_thread = WorkThread(self.motor.move_absolute, self.distance, True)
            self.moving_thread.start()
            #self.set_current_motor_position_label()
        except ValueError:
            self.logger.warning("The input is not a float, change this")
            return

    def save_position(self):
        """Saves the current position for the user.
        Makes sure the user knows the button is pressed by setting it to a different color.
        Gives an error if the thorlabs_motor position has not been found, could be because it is a
        piezo thorlabs_motor or because the software is not running as expected.
        """
        self.save_pos_button.setStyleSheet("background-color: green")
        try:
            self.saved_position = self.motor.position()
            self.logger.debug(str(round(self.saved_position,2)))
            self.save_label.setText("saved: " + str(round(self.saved_position,2)))
        except Exception:
            self.logger.warning("the position has not been set yet")
            self.saved_position = None

    def recover_position(self):
        """Sets position of motors to the saved position with a thread.
        When done, changes the save button to default.
        """
        self.logger.info("current position: {}".format(self.current_position))
        if self.saved_position == None:
            self.logger.warning("the positions have not been set!")
            return
        else:
            self.moving_thread = WorkThread(self.motor.move_absolute, self.saved_position, True)
            self.moving_thread.start()
            self.save_pos_button.setStyleSheet("default")

    def use_keyboard(self):
        """Set text of keyboard_label to using keyboard.
        Collect events until released.
        """
        self.keyboard_label.setText("using keyboard/npress q to exit")

        self.worker_thread = WorkThread(self.create_keyboard_listener)
        self.worker_thread.start()

        #set the text back to you can use the keyboard.
        self.keyboard_label.setText("use keyboard\nto control selected\n combobox thorlabs_motor:")

    def create_keyboard_listener(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def on_press(self, key):
        """ 
        In this method if the w is pressed the thorlabs_motor
        selected in the combobox will move forward or if 
        s is pressed the thorlabs_motor will move backward.
        The w and s are written as: "'w'"/"'s'" because of syntacs.
        """
        if str(key) == "'w'":
            #forward
            self.set_current_motor_position_label()
            self.motor.controller.move_velocity(2)
            self.set_current_motor_position_label()
        elif str(key) == "'s'":
            #backwards
            self.set_current_motor_position_label()
            self.motor.controller.move_velocity(1)
            self.set_current_motor_position_label()
    def on_release(self, key):
        """
        In this method if the w or s is released the thorlabs_motor will stop moving.
        If q is released the keyboard mode stops. 
        """
        if str(key) == "'w'" or str(key) == "'s'":
            #stop the thorlabs_motor from going
            self.motor.stop_moving()
            self.set_current_motor_position_label()
        elif str(key) == "'q'":
            # Stop listener
            if self.worker_thread.isRunning():
                self.set_current_motor_position_label()
                self.worker_thread.quit()
                self.worker_thread.wait()
                return False

    def stop_moving(self):
        """| Stops movement of the current cube.
        | The moving_loop method in the instrument level checks whether the stop is True, and if so, breaks the loop.
        | The stop_moving method in the instrument actually stops the device.
        | Because of the moving_thread that is started in the method move in this class,
        | the loops in the methods in instrument actually keep checking for this stop value.
        """
        self.logger.info('stop moving')
        self.motor.stop = True
        self.motor.stop_moving()

        if self.moving_thread.isRunning:
            self.logger.debug('Moving thread was running.')
            self.moving_thread.quit()

        self.motor.stop = False


if __name__ == '__main__':

    xMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850129, 'name': 'xMotor'}

    yMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube', 'serial': 83850123, 'name': 'yMotor'}

    WaveplateMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850090, 'name': 'Waveplate'}

    with Thorlabsmotor(settings = WaveplateMotor) as thorlabs_instrument:

        app = QApplication(sys.argv)
        ex = Thorlabs_motor_GUI(thorlabs_instrument)
        sys.exit(app.exec_())

