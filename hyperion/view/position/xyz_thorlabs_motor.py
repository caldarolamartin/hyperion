"""
====================================
XYZ thorlabsmotor Thorlabs Motor GUI
====================================

GUI that controls an xyz motorstage based on linear thorlabs motors. Also using a keyboard

"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from hyperion.instrument.position.thorlabs_metainstrument_xyz import Thorlabsmotor_xyz
from hyperion.view.general_worker import WorkThread
from hyperion.view.base_guis import BaseGui
from hyperion import ur
from pynput.keyboard import Key, Listener
import logging

class Thorlabs_motor_GUI(BaseGui):
    """
    | The initialization of the thorlabs xyz gui.
    | Settings of the meta instrument are used. Here
    | Serial number and name are in the settings given underneath, so thorlabs_instrument knows them.
    | Initialize of the instrument is already done by the init of the thorlabs_instrument, that runs with the with downstairs.
    """

    def __init__(self, thorlabs_meta_instrument):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.left = 50
        self.top = 50
        self.width = 400
        self.height = 300
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        self.enable_homebutton = False
        self.enable_zstage = False

        self.motorx = thorlabs_meta_instrument.motorx
        self.logger.debug('You are connected to a {}'.format(self.motorx.kind_of_device))

        self.motory = thorlabs_meta_instrument.motory
        self.logger.debug('You are connected to a {}'.format(self.motory.kind_of_device))

        if self.enable_zstage == True:
            print(test)
            self.motorz = thorlabs_meta_instrument.motorz
            self.logger.debug('You are connected to a {}'.format(self.motorz.kind_of_device))

        else:
            self.logger.info("Z-stage disabled")


        self.title = 'Thorlabs {} GUI xyz Motor'

        self.saved_positionx = None
        self.saved_positiony = None


        self.current_positionx = None
        self.curren_positiony = None
        self.current_positionz = None

        self.keyboard_use = False
        self.keyboard_use_move = False

        self.min_distance = -12.0 * ur('mm')
        self.max_distance = 12.0 * ur('mm')

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.set_current_motor_position_label)
        self.timer.start(100)       #time in ms


    def initUI(self):
        self.logger.debug('Setting up the Single Thorlabs Motor GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.make_buttons()
        self.make_labels()
        self.make_misc_gui_stuff()
        self.load_distances() #used to load the initial distances

        self.show()
    def make_buttons(self):
        self.make_go_home_button()
        self.make_save_pos_button()
        self.make_recover_pos_button()
        self.make_keyboard_button()
        self.make_stop_button()
        self.make_move_left_button()
        self.make_move_right_button()
        self.make_move_up_button()
        self.make_move_down_button()
        self.make_move_in_button()
        self.make_move_out_button()
        self.make_keyboard_move_button()

    def make_labels(self):
        self.make_current_posx_label()
        self.make_current_posy_label()
        self.make_current_posz_label()
        self.make_keyboard_label()
        self.make_keyboard_move_label()

    def make_misc_gui_stuff(self):
        self.make_toggle_distancex_spinbox()
        self.make_toggle_distancey_spinbox()
        self.make_toggle_distancez_spinbox()
        self.make_unit_combobox_x()
        self.make_unit_combobox_y()
        self.make_unit_combobox_z()
        self.set_current_motor_position_label()


    def load_distances(self):
        self.set_toggle_distancex()
        self.set_toggle_distancey()
        self.set_toggle_distancez()

    ############################Make buttons, boxes and labels#########################################

    def make_go_home_button(self):
        self.go_home_button = QPushButton("Go home", self)
        self.go_home_button.setToolTip('Go to home position')
        self.go_home_button.clicked.connect(self.go_home_motor)
        self.grid_layout.addWidget(self.go_home_button, 3, 2)

    def make_move_left_button(self):
        self.move_left_button = QPushButton("Left", self)
        self.move_left_button.setToolTip('Go Left')
        self.move_left_button.clicked.connect(self.move_rel_left)
        self.grid_layout.addWidget(self.move_left_button, 0, 1)

    def make_move_right_button(self):
        self.move_right_button = QPushButton("Right", self)
        self.move_right_button.setToolTip('Go Right')
        self.move_right_button.clicked.connect(self.move_rel_right)
        self.grid_layout.addWidget(self.move_right_button, 0, 2)

    def make_move_up_button(self):
        self.move_up_button = QPushButton("Up", self)
        self.move_up_button.setToolTip('Go Up')
        self.move_up_button.clicked.connect(self.move_rel_up)
        self.grid_layout.addWidget(self.move_up_button, 1, 1)

    def make_move_down_button(self):
        self.move_down_button = QPushButton("Down", self)
        self.move_down_button.setToolTip('Go Down')
        self.move_down_button.clicked.connect(self.move_rel_down)
        self.grid_layout.addWidget(self.move_down_button, 1, 2)

    def make_move_in_button(self):
        self.move_in_button = QPushButton("In", self)
        self.move_in_button.setToolTip('Go In')
        self.move_in_button.clicked.connect(self.move_rel_in)
        self.grid_layout.addWidget(self.move_in_button, 2, 1)

    def make_move_out_button(self):
        self.move_out_button = QPushButton("Out", self)
        self.move_out_button.setToolTip('Go Down')
        self.move_out_button.clicked.connect(self.move_rel_out)
        self.grid_layout.addWidget(self.move_out_button, 2, 2)

    def make_save_pos_button(self):
        self.save_pos_button = QPushButton("save pos", self)
        self.save_pos_button.setToolTip('save the current position of the thorlabs_motor')
        self.save_pos_button.clicked.connect(self.save_position)
        self.grid_layout.addWidget(self.save_pos_button, 4, 2)
    def make_recover_pos_button(self):
        self.recover_pos_button = QPushButton("recover pos", self)
        self.recover_pos_button.setToolTip("recover the set position of the thorlabs_motor")
        self.recover_pos_button.clicked.connect(self.recover_position)
        self.grid_layout.addWidget(self.recover_pos_button, 4, 3)

    def make_keyboard_button(self):
        self.keyboard_button = QPushButton("keyboard\ntoggle", self)
        self.keyboard_button.setToolTip("use the keyboard to move the thorlabs_motor,\nit works great")
        self.keyboard_button.clicked.connect(self.use_keyboard)
        self.grid_layout.addWidget(self.keyboard_button, 3, 1)

    def make_keyboard_move_button(self):
        self.keyboard_button_move = QPushButton("keyboard\nmove", self)
        self.keyboard_button_move.setToolTip("use the keyboard to move the thorlabs_motor,\nit works great")
        self.keyboard_button_move.clicked.connect(self.use_keyboard_move)
        self.grid_layout.addWidget(self.keyboard_button_move, 4, 1)

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
        try:
            if self.enable_zstage == True:
                self.current_motorz_position_label.setText(self.motorz.position())
        except Exception:
            self.current_motorz_position_label.setText("currently/unavailable")
        self.grid_layout.addWidget(self.current_motorz_position_label, 2, 0)

    def make_keyboard_label(self):
        self.keyboard_label = QLabel(self)
        self.keyboard_label.setText("a/d to move x\nw/s to move y\nq/e to move z\nt to quit)")
        self.grid_layout.addWidget(self.keyboard_label, 3, 0)

    def make_keyboard_move_label(self):
        self.keyboard_move_label = QLabel(self)
        self.keyboard_move_label.setText("up/down to move x\nright/left to move y\nz/x to move z\nt to quit)")
        self.grid_layout.addWidget(self.keyboard_move_label, 4, 0)

    def make_toggle_distancex_spinbox(self):
        self.toggle_distancex_spinbox = QDoubleSpinBox(self)
        self.grid_layout.addWidget(self.toggle_distancex_spinbox, 0, 3)
        self.toggle_distancex_spinbox.setValue(100)
        self.toggle_distancex_spinbox.setMinimum(-999999999)        #otherwise you cannot reach higher than 99
        self.toggle_distancex_spinbox.setMaximum(999999999)
        self.toggle_distancex_spinbox.valueChanged.connect(self.set_toggle_distancex)

    def make_toggle_distancey_spinbox(self):
        self.toggle_distancey_spinbox = QDoubleSpinBox(self)
        self.grid_layout.addWidget(self.toggle_distancey_spinbox, 1, 3)
        self.toggle_distancey_spinbox.setValue(100)
        self.toggle_distancey_spinbox.setMinimum(-999999999)        #otherwise you cannot reach higher than 99
        self.toggle_distancey_spinbox.setMaximum(999999999)
        self.toggle_distancey_spinbox.valueChanged.connect(self.set_toggle_distancey)

    def make_toggle_distancez_spinbox(self):
        self.toggle_distancez_spinbox = QDoubleSpinBox(self)
        self.grid_layout.addWidget(self.toggle_distancez_spinbox, 2, 3)
        self.toggle_distancez_spinbox.setValue(100)
        self.toggle_distancez_spinbox.setMinimum(-999999999)        #otherwise you cannot reach higher than 99
        self.toggle_distancez_spinbox.setMaximum(999999999)
        self.toggle_distancez_spinbox.valueChanged.connect(self.set_toggle_distancez)


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

    def make_unit_combobox_x(self):
        self.unit_combobox_x = QComboBox(self)
        self.unit_combobox_x.addItems(["nm", "um", "mm"])
        self.unit_combobox_x.setCurrentText('um')
        self.unit_combobox_x.currentTextChanged.connect(self.set_toggle_distancex)
        self.grid_layout.addWidget(self.unit_combobox_x, 0, 4)

    def make_unit_combobox_y(self):
        self.unit_combobox_y = QComboBox(self)
        self.unit_combobox_y.addItems(["nm", "um", "mm"])
        self.unit_combobox_y.setCurrentText("um")
        self.unit_combobox_y.currentTextChanged.connect(self.set_toggle_distancey)
        self.grid_layout.addWidget(self.unit_combobox_y, 1, 4)

    def make_unit_combobox_z(self):
        self.unit_combobox_z = QComboBox(self)
        self.unit_combobox_z.addItems(["nm", "um", "mm"])
        self.unit_combobox_z.setCurrentText("um")
        self.unit_combobox_z.currentTextChanged.connect(self.set_toggle_distancez)
        self.grid_layout.addWidget(self.unit_combobox_z, 2, 4)


    def set_current_motor_position_label(self):
        """ In the instrument level, the current position is remembered and updated through self.position,
        which is called in the moving_loop during the moves.
        This method read this out (continuously, through the timer in the init) and displays the value.
        """

        self.current_positionx = self.motorx.current_position
        self.current_motorx_position_label.setText("pos x:"+ str(round(self.current_positionx, 2)))

        self.current_positiony = self.motory.current_position
        self.current_motory_position_label.setText("pos y:" + str(round(self.current_positiony, 2)))
        if self.enable_zstage == True:
            self.current_positionz = self.motorz.current_position
            self.current_motorz_position_label.setText("pos z:"+ str(round(self.current_positionz, 2)))


    def set_toggle_distancex(self):
        value = self.toggle_distancex_spinbox.value()
        unit = self.unit_combobox_x.currentText()
        toggle_distance = ur(str(value) + unit)
        self.logger.debug('toggle x distance value {}'.format(value))
        self.toggledistance_x = toggle_distance

    def set_toggle_distancey(self):
        value = self.toggle_distancey_spinbox.value()
        unit = self.unit_combobox_y.currentText()
        toggle_distance = ur(str(value) + unit)
        self.logger.debug('toggle y distance value {}'.format(value))
        self.toggledistance_y = toggle_distance

    def set_toggle_distancez(self):
        value = self.toggle_distancez_spinbox.value()
        unit = self.unit_combobox_z.currentText()
        toggle_distance = ur(str(value) + unit)
        self.logger.debug('toggle z distance value {}'.format(value))
        self.toggledistance_z = toggle_distance



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
        if self.enable_homebutton == True:
            self.movingx_thread = WorkThread(self.motorx.move_home, True)
            self.movingx_thread.start()

            self.movingy_thread = WorkThread(self.motory.move_home, True)
            self.movingy_thread.start()
            if self.enable_zstage == True:
                self.movingz_thread = WorkThread(self.motorz.move_home, True)
                self.movingz_thread.start()

        else:
            self.logger.log("Homing disabled")

    def move_rel_left(self):
        self.movingx_thread = WorkThread(self.motorx.move_relative, self.toggledistance_x, True)
        self.movingx_thread.start()

    def move_rel_right(self):
        self.movingx_thread = WorkThread(self.motorx.move_relative, -1*self.toggledistance_x, True)
        self.movingx_thread.start()

    def move_rel_up(self):
        self.movingy_thread = WorkThread(self.motory.move_relative, self.toggledistance_y, True)
        self.movingy_thread.start()

    def move_rel_down(self):
        self.movingy_thread = WorkThread(self.motory.move_relative, -1 * self.toggledistance_y, True)
        self.movingy_thread.start()

    def move_rel_in(self):
        if self.enable_zstage == True:
            self.movingz_thread = WorkThread(self.motorz.move_relative, self.toggledistance_z, True)
            self.movingz_thread.start()

    def move_rel_out(self):
        if self.enable_zstage == True:
            self.movingz_thread = WorkThread(self.motorz.move_relative, -1 * self.toggledistance_z, True)
            self.movingz_thread.start()

    def go_to_input(self):
        """Starts a thread to make an absolute move with the distance that is read out in self.set_distance from the spinbox.
        Value error has become a little bit irrelevant, now that I changed to pint quantities for distance.
        """
        try:
            self.movingx_thread = WorkThread(self.motorx.move_absolute, self.distance, True)
            self.movingx_thread.start()

            self.movingy_thread = WorkThread(self.motory.move_absolute, self.distance, True)
            self.movingy_thread.start()

            if self.enable_zstage == True:
                self.movingz_thread = WorkThread(self.motorz.move_absolute, self.distance, True)
                self.movingz_thread.start()
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
        if self.keyboard_use == False:
            self.worker_thread = WorkThread(self.create_keyboard_listener)
            self.worker_thread.start()
            self.keyboard_button.setStyleSheet("background-color: green")
            self.keyboard_use = True

        else:
            self.keyboard_button.setStyleSheet("")
            self.keyboard_use = False
            if self.worker_thread.isRunning():
                self.listener.stop()

    def use_keyboard_move(self):
        """Set text of keyboard_label to using keyboard.
        Collect events until released.
        """
        if self.keyboard_use_move == False:
            self.worker_move_thread = WorkThread(self.create_keyboard_listener_move)
            self.worker_move_thread.start()
            self.keyboard_button_move.setStyleSheet("background-color: green")
            self.keyboard_use_move = True

        else:
            self.keyboard_button_move.setStyleSheet("")
            self.keyboard_use_move = False
            if self.worker_move_thread.isRunning():
                self.listener_move.stop()


    def create_keyboard_listener(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as self.listener:
            self.listener.join()

    def create_keyboard_listener_move(self):
        with Listener(on_press=self.on_press_move, on_release=self.on_release_move) as self.listener_move:
            self.listener_move.join()

    def on_press(self, key):
        """ 
        In this method if the w is pressed the thorlabs_motor
        selected in the combobox will move forward or if 
        s is pressed the thorlabs_motor will move backward.
        The w and s are written as: "'w'"/"'s'" because of syntacs.
        """

        if str(key) == "'a'":
            self.move_rel_left()

        elif str(key) == "'d'":
            self.move_rel_right()

        elif str(key) == "'w'":
            self.move_rel_up()

        elif str(key) == "'s'":
            self.move_rel_down()

        elif str(key) == "'e'":
            self.move_rel_in()

        elif str(key) == "'q'":
            self.move_rel_out()

    def on_release(self, key):
        """
        In this method if the w or s is released the thorlabs_motor will stop moving.
        If q is released the keyboard mode stops. 
        """
        if str(key) == "'w'" or str(key) == "'s'":
            #stop the thorlabs_motor from going
            self.movingy_thread.quit()
            # self.motorx.stop_moving()


        elif str(key) == "'a'" or str(key) == "'d'":
            #stop the thorlabs_motor from going
            self.movingx_thread.quit()
            # self.motorx.stop_moving()

        elif str(key) == "'q'" or str(key) == "'e'":
            #stop the thorlabs_motor from going
            self.movingz_thread.quit()

        elif str(key) == "'t'":
            # Stop listener
            self.keyboard_button.setStyleSheet("")
            self.keyboard_use = False
            if self.worker_thread.isRunning():
                return False

    def on_press_move(self, key):
        """
        In this method if the w is pressed the thorlabs_motor
        selected in the combobox will move forward or if
        s is pressed the thorlabs_motor will move backward.
        The w and s are written as: "'w'"/"'s'" because of syntacs.
        """

        if key == Key.left:
            self.movingx_thread = WorkThread(self.motorx.move_velocity, 2, True)
            self.movingx_thread.start()
            self.set_current_motor_position_label

        elif key == Key.right:
            self.movingx_thread = WorkThread(self.motorx.move_velocity, 1, True)
            self.movingx_thread.start()

        elif key == Key.up:
            self.movingy_thread = WorkThread(self.motory.move_velocity, 1, True)
            self.movingy_thread.start()

        elif key == Key.down:
            self.movingy_thread = WorkThread(self.motory.move_velocity, 2, True)
            self.movingy_thread.start()

        elif str(key) == "'z'":
            if self.enable_zstage == True:
                self.movingz_thread = WorkThread(self.motorz.move_velocity, 2, True)
                self.movingz_thread.start()

        elif str(key) == "'x'":
            if self.enable_zstage == True:
                self.movingz_thread = WorkThread(self.motorz.move_velocity, 1, True)
                self.movingz_thread.start()

    def on_release_move(self, key):
        """
        In this method if the w or s is released the thorlabs_motor will stop moving.
        If q is released the keyboard mode stops.
        """
        if key == Key.up or key == Key.down:
            #stop the thorlabs_motor from going
            self.movingy_thread.quit()
            self.motory.stop_moving()


        elif key == Key.right or key == Key.left:
            #stop the thorlabs_motor from going
            self.movingx_thread.quit()
            self.motorx.stop_moving()

        elif str(key) == "'z'" or str(key) == "'x'":
            #stop the thorlabs_motor from going
            if self.enable_zstage == True:
                self.movingz_thread.quit()
                self.motorz.stop_moving()

        elif str(key) == "'t'":
            # Stop listener
            self.keyboard_button_move.setStyleSheet("")
            self.keyboard_use_move = False
            if self.worker_move_thread.isRunning():
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
        if self.enable_zstage == True:
            self.motorz.stop = True

        self.motorx.stop_moving()
        self.motory.stop_moving()
        if self.enable_zstage == True:
            self.motorz.stop_moving()


        if self.movingx_thread.isRunning:
            self.logger.debug('Moving thread motorx was running.')
            self.movingx_thread.quit()

        if self.movingy_thread.isRunning:
            self.logger.debug('Moving thread motory was running.')
            self.movingy_thread.quit()

        if self.movingz_thread.isRunning:
            self.logger.debug('Moving thread motorz was running.')
            self.movingz_thread.quit()

        self.motorx.stop = False
        self.motory.stop = False
        if self.enable_zstage == True:
            self.motorz.stop = False


if __name__ == '__main__':
    import hyperion

    xyz_motorsettings = {'x':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83817748, 'name': 'xMotor'},
              'y':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83817747, 'name': 'yMotor'},
              'z':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83817716, 'name': 'zMotor'}
              }

    with Thorlabsmotor_xyz(settings = xyz_motorsettings) as thorlabs_meta_instrument:

        app = QApplication(sys.argv)
        ex = Thorlabs_motor_GUI(thorlabs_meta_instrument)
        sys.exit(app.exec_())

