"""
====================================
XYZ thorlabsmotor Thorlabs Motor GUI
====================================

GUI that controls an xyz motorstage based on linear thorlabs motors. Also using a keyboard

"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from hyperion.instrument.position.thorlabs_metainstrument_twowaveplates import Thorlabsmotor_twowp
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
        self.height = 200
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        self.wp_one = thorlabs_meta_instrument.wp_one
        self.logger.debug('You are connected to a {}'.format(self.wp_one.kind_of_device))

        self.wp_two = thorlabs_meta_instrument.wp_two
        self.logger.debug('You are connected to a {}'.format(self.wp_one.kind_of_device))


        self.title = 'Thorlabs {} GUI two waveplates'

        self.current_position_one = None
        self.current_position_two = None

        self.wp_one_target = 0
        self.wp_two_target = 0

        self.offset_one = 0
        self.offset_two = 0

        self.keyboard_use_move = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.set_current_motor_position_label)
        self.timer.start(100)

        self.initUI()


    def initUI(self):
        self.logger.debug('Setting up the two waveplates Motor GUI')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.make_buttons()
        self.make_labels()
        self.make_misc_gui_stuff()


        self.show()
    def make_buttons(self):
        self.make_goto_one_button()
        self.make_goto_two_button()
        self.make_moveby_both_button()
        self.make_reset_one_button()
        self.make_reset_two_button()
        self.make_keyboard_move_button()


    def make_labels(self):
        self.make_current_pos_one_label()
        self.make_current_pos_two_label()
        self.make_both_text_label()
        self.make_keyboard_text_label()


    def make_misc_gui_stuff(self):
        self.make_wp_one_spinbox()
        self.make_wp_two_spinbox()
        self.make_wp_both_spinbox()



    ############################Make buttons, boxes and labels#########################################


    def make_goto_one_button(self):
        self.goto_one_button = QPushButton("Go to", self)
        self.goto_one_button.setToolTip('Go to')
        self.goto_one_button.clicked.connect(self.goto_one)
        self.grid_layout.addWidget(self.goto_one_button, 0, 2)

    def make_goto_two_button(self):
        self.goto_two_button = QPushButton("Go to", self)
        self.goto_two_button.setToolTip('Go to')
        self.goto_two_button.clicked.connect(self.goto_two)
        self.grid_layout.addWidget(self.goto_two_button, 1, 2)

    def make_reset_one_button(self):
        self.reset_one_button = QPushButton("Reset", self)
        self.reset_one_button.setToolTip('Reset')
        self.reset_one_button.clicked.connect(self.reset_one)
        self.grid_layout.addWidget(self.reset_one_button, 0, 3)

    def make_reset_two_button(self):
        self.reset_two_button = QPushButton("Reset", self)
        self.reset_two_button.setToolTip('Reset')
        self.reset_two_button.clicked.connect(self.reset_two)
        self.grid_layout.addWidget(self.reset_two_button, 1, 3)

    def make_moveby_both_button(self):
        self.moveby_both_button = QPushButton("Move by", self)
        self.moveby_both_button.setToolTip('Reset')
        self.moveby_both_button.clicked.connect(self.moveby_both)
        self.grid_layout.addWidget(self.moveby_both_button, 2, 2)

    def make_keyboard_move_button(self):
        self.keyboard_button_move = QPushButton("keyboard\nmove", self)
        self.keyboard_button_move.setToolTip("use the keyboard to move the thorlabs_motor,\nit works great")
        self.keyboard_button_move.clicked.connect(self.use_keyboard_move)
        self.grid_layout.addWidget(self.keyboard_button_move, 3, 3)

    def make_current_pos_one_label(self):
        self.current_pos_one_label = QLabel(self)
        try:
            self.current_pos_one_label.setText(self.wp_one.position())
        except Exception:
            self.current_pos_one_label.setText("currently/unavailable")
        self.grid_layout.addWidget(self.current_pos_one_label, 0, 0)

    def make_current_pos_two_label(self):
        self.current_pos_two_label = QLabel(self)
        try:
            self.current_pos_two_label.setText(self.wp_two.position())
        except Exception:
            self.current_pos_two_label.setText("currently/unavailable")
        self.grid_layout.addWidget(self.current_pos_two_label, 1, 0)

    def make_both_text_label(self):
        self.both_text_label = QLabel(self)
        self.both_text_label.setText("Both waveplates")
        self.grid_layout.addWidget(self.both_text_label, 2, 0)

    def make_keyboard_text_label(self):
        self.keyboard_text_label = QLabel(self)
        self.keyboard_text_label.setText("y/u to move wp one - h/j to move wp two - n/m to move both\nt to quit)")
        self.grid_layout.addWidget(self.keyboard_text_label, 3, 0, 1, 2)


    def make_wp_one_spinbox(self):
        self.wp_one_spinbox = QDoubleSpinBox(self)
        self.grid_layout.addWidget(self.wp_one_spinbox, 0, 1)
        self.wp_one_spinbox.setValue(0)
        self.wp_one_spinbox.setMinimum(-999999999)        #otherwise you cannot reach higher than 99
        self.wp_one_spinbox.setMaximum(999999999)
        self.wp_one_spinbox.valueChanged.connect(self.set_wp_one_target)

    def make_wp_two_spinbox(self):
        self.wp_two_spinbox = QDoubleSpinBox(self)
        self.grid_layout.addWidget(self.wp_two_spinbox, 1, 1)
        self.wp_two_spinbox.setValue(0)
        self.wp_two_spinbox.setMinimum(-999999999)        #otherwise you cannot reach higher than 99
        self.wp_two_spinbox.setMaximum(999999999)
        self.wp_two_spinbox.valueChanged.connect(self.set_wp_two_target)

    def make_wp_both_spinbox(self):
        self.wp_both_spinbox = QDoubleSpinBox(self)
        self.grid_layout.addWidget(self.wp_both_spinbox, 2, 1)
        self.wp_both_spinbox.setValue(0)
        self.wp_both_spinbox.setMinimum(-999999999)        #otherwise you cannot reach higher than 99
        self.wp_both_spinbox.setMaximum(999999999)
        self.wp_both_spinbox.valueChanged.connect(self.set_wp_both_degrees)

    def set_current_motor_position_label(self):
        """ In the instrument level, the current position is remembered and updated through self.position,
        which is called in the moving_loop during the moves.
        This method read this out (continuously, through the timer in the init) and displays the value.
        """
        self.current_position_one = self.wp_one.position()
        self.current_pos_one_label.setText("waveplate one:"+ str(round(self.current_position_one-self.offset_one, 2)))

        self.current_position_two = self.wp_two.position()
        self.current_pos_two_label.setText("waveplate two:"+ str(round(self.current_position_two-self.offset_two, 2)))

    def set_wp_both_degrees(self):
        value = self.wp_both_spinbox.value()
        unit = "degrees"
        toggle_distance = ur(str(value) + unit)
        self.logger.debug('toggle waveplate 1 distance value {}'.format(value))
        self.wp_both_target_relative = toggle_distance

    def set_wp_one_target(self):
        value = self.wp_one_spinbox.value()
        unit = "degrees"
        toggle_distance = ur(str(value) + unit)
        self.logger.debug('toggle waveplate 1 distance value {}'.format(value))
        self.wp_one_target = toggle_distance

    def reset_one(self):
        self.offset_one = self.wp_one.position()

    def reset_two(self):
        self.offset_two = self.wp_two.position()

    def set_wp_two_target(self):
        value = self.wp_two_spinbox.value()
        unit = "degrees"
        toggle_distance = ur(str(value) + unit)
        self.logger.debug('toggle waveplate 2 distance value {}'.format(value))
        self.wp_two_target = toggle_distance

    def goto_one(self):
        self.moving_one_thread = WorkThread(self.wp_one.move_absolute, self.wp_one_target+self.offset_one, True)
        self.moving_one_thread.start()

    def goto_two(self):
        self.moving_two_thread = WorkThread(self.wp_two.move_absolute, self.wp_two_target+self.offset_one, True)
        self.moving_two_thread.start()

    def moveby_both(self):
        self.moving_one_thread = WorkThread(self.wp_one.move_relative, self.wp_both_target_relative, True)
        self.moving_one_thread.start()

        self.moving_two_thread = WorkThread(self.wp_two.move_relative, self.wp_both_target_relative, True)
        self.moving_two_thread.start()


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

    def create_keyboard_listener_move(self):
        with Listener(on_press=self.on_press_move, on_release=self.on_release_move) as self.listener_move:
            self.listener_move.join()


    def on_press_move(self, key):
        """
        In this method if the w is pressed the thorlabs_motor
        selected in the combobox will move forward or if
        s is pressed the thorlabs_motor will move backward.
        The w and s are written as: "'w'"/"'s'" because of syntacs.
        """

        if str(key) == "'y'":
            self.moving_one_thread = WorkThread(self.wp_one.move_velocity, 2, True)
            self.moving_one_thread.start()

        elif str(key) == "'u'":
            self.moving_one_thread = WorkThread(self.wp_one.move_velocity, 1, True)
            self.moving_one_thread.start()

        elif str(key) == "'h'":
            self.moving_two_thread = WorkThread(self.wp_two.move_velocity, 2, True)
            self.moving_two_thread.start()

        elif str(key) == "'j'":
            self.moving_two_thread = WorkThread(self.wp_two.move_velocity, 1, True)
            self.moving_two_thread.start()

        elif str(key) == "'n'":
            self.moving_two_thread = WorkThread(self.wp_two.move_velocity, 2, True)
            self.moving_one_thread = WorkThread(self.wp_one.move_velocity, 2, True)
            self.moving_one_thread.start()
            self.moving_two_thread.start()

        elif str(key) == "'m'":
            self.moving_two_thread = WorkThread(self.wp_two.move_velocity, 1, True)
            self.moving_one_thread = WorkThread(self.wp_one.move_velocity, 1, True)
            self.moving_one_thread.start()
            self.moving_two_thread.start()

    def on_release_move(self, key):
        """
        In this method if the w or s is released the thorlabs_motor will stop moving.
        If q is released the keyboard mode stops.
        """
        if str(key) == "'y'" or str(key) == "'u'":
            #stop the thorlabs_motor from going
            self.moving_one_thread.quit()
            self.wp_one.stop_moving()

        elif str(key) == "'h'" or str(key) == "'j'":
            #stop the thorlabs_motor from going
            self.moving_two_thread.quit()
            self.wp_two.stop_moving()

        elif str(key) == "'n'" or str(key) == "'m'":
            # stop the thorlabs_motor from going
            self.moving_one_thread.quit()
            self.wp_one.stop_moving()
            self.moving_two_thread.quit()
            self.wp_two.stop_moving()


if __name__ == '__main__':
    import hyperion

    wp_motorsettings = {'wp_one':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83817715, 'name': 'waveplate 1200 nm'},
              'wp_two':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83817710, 'name': 'waveplate 1200 nm'}}

    with Thorlabsmotor_twowp(settings = wp_motorsettings) as thorlabs_meta_instrument:

        app = QApplication(sys.argv)
        ex = Thorlabs_motor_GUI(thorlabs_meta_instrument)
        sys.exit(app.exec_())

