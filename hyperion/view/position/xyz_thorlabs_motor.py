"""
====================================
XYZ thorlabsmotor Thorlabs Motor GUI
====================================

Work in progress currentyly build as an xy motorstage

"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from hyperion.instrument.position.thorlabs_metainstrument_xyz import Thorlabsmotor_xyz
from hyperion.view.general_worker import WorkThread
from hyperion.view.base_guis import BaseGui
from hyperion import ur
from pynput.keyboard import Listener
import logging

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
        self.height = 300
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        self.motorx = thorlabs_instrument.motorx
        self.motory = thorlabs_instrument.motory
        self.logger.debug('You are connected to a {}'.format(self.motorx.kind_of_device))
        self.logger.debug('You are connected to a {}'.format(self.motorx.kind_of_device))

        self.title = 'Thorlabs {} GUI xyz Motor'

        self.saved_positionx = None
        self.saved_positiony= None
        self.current_positionx = None

        self.distance = 1.0*ur('mm')

        self.min_distance = -12.0 * ur('mm')
        self.max_distance = 12.0 * ur('mm')

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.set_current_motor_position_label)
        self.timer.start(100)       #time in ms

        self.movingx_thread = WorkThread(self.motorx.move_absolute, self.current_positionx, True)
        self.movingy_thread = WorkThread(self.motory.move_absolute, self.current_positionx, True)

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
        self.make_save_pos_button()
        self.make_recover_pos_button()
        self.make_keyboard_button()
        self.make_stop_button()
    def make_labels(self):
        self.make_current_posx_label()
        self.make_current_posy_label()
        self.make_current_posz_label()
    def make_misc_gui_stuff(self):
        # self.make_distance_spinbox()
        self.set_current_motor_position_label()

    def make_go_home_button(self):
        self.go_home_button = QPushButton("Go home", self)
        self.go_home_button.setToolTip('Go to home position')
        self.go_home_button.clicked.connect(self.go_home_motor)
        self.grid_layout.addWidget(self.go_home_button, 3, 2)

    def make_save_pos_button(self):
        self.save_pos_button = QPushButton("save pos", self)
        self.save_pos_button.setToolTip('save the current position of the thorlabs_motor')
        self.save_pos_button.clicked.connect(self.save_position)
        self.grid_layout.addWidget(self.save_pos_button, 4, 0)
    def make_recover_pos_button(self):
        self.recover_pos_button = QPushButton("recover pos", self)
        self.recover_pos_button.setToolTip("recover the set position of the thorlabs_motor")
        self.recover_pos_button.clicked.connect(self.recover_position)
        self.grid_layout.addWidget(self.recover_pos_button, 4, 1)
    def make_keyboard_button(self):
        self.keyboard_button = QPushButton("keyboard", self)
        self.keyboard_button.setToolTip("use the keyboard to move the thorlabs_motor,\nit works great")
        self.keyboard_button.clicked.connect(self.use_keyboard)
        self.grid_layout.addWidget(self.keyboard_button, 3, 1)

    def make_stop_button(self):
        self.stop_button = QPushButton("stop moving", self)
        self.stop_button.setToolTip("stop any moving")
        self.stop_button.clicked.connect(self.stop_moving)
        self.grid_layout.addWidget(self.stop_button, 3, 3)
        self.stop_button.setStyleSheet("background-color: red")

    def make_current_posx_label(self):
        self.current_motorx_position_label = QLabel(self)
        try:
            self.current_motorx_position_label.setText(self.motorx.position())
        except Exception:
            self.current_motorx_position_label.setText("currently/unavailable")
        self.grid_layout.addWidget(self.current_motorx_position_label, 0, 0)

    def make_current_posy_label(self):
        self.current_motory_position_label = QLabel(self)
        try:
            self.current_motory_position_label.setText(self.motory.position())
        except Exception:
            self.current_motory_position_label.setText("currently/unavailable")
        self.grid_layout.addWidget(self.current_motory_position_label, 1, 0)

    def make_current_posz_label(self):
        self.current_motorz_position_label = QLabel(self)
        self.grid_layout.addWidget(self.current_motorz_position_label, 2, 0)


    # def make_save_label(self):
    #     self.save_label = QLabel(self)
    #     self.save_label.setText("saved:")
    #     self.grid_layout.addWidget(self.save_label, 0, 3)
    # def make_recover_label(self):
    #     self.recover_label = QLabel(self)
    #     self.recover_label.setText("recover pos:")
    #     self.grid_layout.addWidget(self.recover_label, 1, 3)

    def make_distance_spinbox(self):
        self.distance_spinbox = QDoubleSpinBox(self)
        if self.motorx.kind_of_device == 'waveplate':
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

    # def make_unit_combobox(self):
    #     self.unit_combobox = QComboBox(self)
    #     if self.motorx.kind_of_device == 'waveplate':
    #         self.unit_combobox.addItems(["degrees"])
    #         self.unit_combobox.setCurrentText('degrees')
    #         self.unit_combobox.setEnabled(False)
    #     else:
    #         self.unit_combobox.addItems(["nm", "um", "mm"])
    #         self.unit_combobox.setCurrentText('mm')
    #
    #     self.unit_combobox.currentTextChanged.connect(self.set_distance)
    #     self.grid_layout.addWidget(self.unit_combobox, 1, 3)


    def set_current_motor_position_label(self):
        """ In the instrument level, the current position is remembered and updated through self.position,
        which is called in the moving_loop during the moves.
        This method read this out (continuously, through the timer in the init) and displays the value.
        """

        self.current_positionx = self.motorx.current_position
        self.current_motorx_position_label.setText("pos x:"+ str(round(self.current_positionx, 2)))
        print(str(round(self.current_positionx, 2)))

        self.current_positiony = self.motory.current_position
        self.current_motory_position_label.setText("pos y:" + str(round(self.current_positiony, 2)))

        self.current_positionz = 0
        self.current_motorz_position_label.setText("not yet available")



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
        self.movingx_thread = WorkThread(self.motorx.move_home, True)
        self.movingx_thread.start()

        self.movingy_thread = WorkThread(self.motory.move_home, True)
        self.movingy_thread.start()



        #self.motorx.move_home(True)
        #self.set_current_motor_position_label()

    def go_to_input(self):
        """Starts a thread to make an absolute move with the distance that is read out in self.set_distance from the spinbox.
        Value error has become a little bit irrelevant, now that I changed to pint quantities for distance.
        """
        try:
            self.movingx_thread = WorkThread(self.motorx.move_absolute, self.distance, True)
            self.movingx_thread.start()

            self.movingy_thread = WorkThread(self.motory.move_absolute, self.distance, True)
            self.movingy_thread.start()
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
            self.saved_positionx = self.motorx.position()
            self.logger.debug(str(round(self.saved_positionx,2)))
            self.save_label.setText("saved: " + str(round(self.saved_positionx,2)))

            self.saved_positiony = self.motory.position()
            self.logger.debug(str(round(self.saved_positiony,2)))
            self.save_label.setText("saved: " + str(round(self.saved_positiony,2)))

        except Exception:
            self.logger.warning("the position has not been set yet")
            self.saved_position = None

    def recover_position(self):
        """Sets position of motors to the saved position with a thread.
        When done, changes the save button to default.
        """
        self.logger.info("current position: {}".format(self.current_positionx))
        if self.saved_positionx == None:
            self.logger.warning("the positions have not been set!")
            return
        else:
            self.movingx_thread = WorkThread(self.motorx.move_absolute, self.saved_positionx, True)
            self.movingx_thread.start()
            self.movingy_thread = WorkThread(self.motory.move_absolute, self.saved_positiony, True)
            self.movingy_thread.start()


            self.save_pos_button.setStyleSheet("default")

    def use_keyboard(self):
        """Set text of keyboard_label to using keyboard.
        Collect events until released.
        """

        self.worker_thread = WorkThread(self.create_keyboard_listener)
        self.worker_thread.start()

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
        if str(key) == "'a'":
            #forward
            self.set_current_motor_position_label()
            self.motorx.controller.move_velocity(2)
            self.set_current_motor_position_label()
        elif str(key) == "'d'":
            #backwards
            self.set_current_motor_position_label()
            self.motorx.controller.move_velocity(1)
            self.set_current_motor_position_label()
        elif str(key) == "'w'":
            #backwards
            self.set_current_motor_position_label()
            self.motory.controller.move_velocity(2)
            self.set_current_motor_position_label()
        elif str(key) == "'s'":
            #backwards
            self.set_current_motor_position_label()
            self.motory.controller.move_velocity(1)
            self.set_current_motor_position_label()

    def on_release(self, key):
        """
        In this method if the w or s is released the thorlabs_motor will stop moving.
        If q is released the keyboard mode stops. 
        """
        if str(key) == "'w'" or str(key) == "'s'":
            #stop the thorlabs_motor from going
            self.motory.stop_moving()
            self.set_current_motor_position_label()

        elif str(key) == "'a'" or str(key) == "'d'":
            #stop the thorlabs_motor from going
            self.motorx.stop_moving()
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
        self.motorx.stop = True
        self.motory.stop = True

        self.motorx.stop_moving()
        self.motory.stop_moving()

        if self.movingx_thread.isRunning:
            self.logger.debug('Moving thread motorx was running.')
            self.movingx_thread.quit()

        if self.movingy_thread.isRunning:
            self.logger.debug('Moving thread motory was running.')
            self.movingy_thread.quit()

        self.motorx.stop = False
        self.motory.stop = False


if __name__ == '__main__':
    import hyperion

    xyz_motorsettings = {'x':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83817748, 'name': 'xMotor'},
              'y':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83817747, 'name': 'yMotor'},
              'z':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 1, 'name': 'zMotor'}
              }

    with Thorlabsmotor_xyz(settings = xyz_motorsettings) as thorlabs_instrument:

        app = QApplication(sys.argv)
        ex = Thorlabs_motor_GUI(thorlabs_instrument)
        sys.exit(app.exec_())

