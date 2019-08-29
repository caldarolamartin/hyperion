import sys
from PyQt5.QtWidgets import (QApplication, QGridLayout, QPushButton, QWidget, QLabel, QLineEdit)

from hyperion.instrument.motor.thorlabs_motor_instrument import Thorlabsmotor
from hyperion.view.general_worker import WorkThread
from hyperion import ur
from pynput.keyboard import Listener


class App(QWidget):

    def __init__(self, serial_number):
        """
        A serial_number of a motor must be given to this class in order to work. 
        """
        super().__init__()
        self.title = 'thorlabs motors GUI'
        self.left = 50
        self.top = 50
        self.width = 400
        self.height = 200
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.serial_number = serial_number
        self.position = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.motor = Thorlabsmotor(settings = {'controller': 'hyperion.controller.thorlabs.TDC001/TDC001','serial_number' : self.serial_number})
        self.motor.initialize(self.serial_number)
        
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
    def make_labels(self):
        self.make_keyboard_label()
        self.make_current_pos_label()
        self.make_save_label()
        self.make_recover_label()
    def make_misc_gui_stuff(self):
        self.make_input_textfield()
        self.set_current_motor_position_label()
        
    def make_go_home_button(self):
        self.go_home_button = QPushButton("go home", self)
        self.go_home_button.setToolTip('go to home position')
        self.go_home_button.clicked.connect(self.go_home_motor)
        self.grid_layout.addWidget(self.go_home_button, 0, 0)
    def make_go_to_button(self):
        self.move_button = QPushButton('move to in um', self)
        self.move_button.setToolTip('move to given input')
        self.move_button.clicked.connect(self.go_to_input)
        self.grid_layout.addWidget(self.move_button, 1, 0)
    def make_save_pos_button(self):
        self.save_pos_button = QPushButton("save pos", self)
        self.save_pos_button.setToolTip('save the current position of the motor')
        self.save_pos_button.clicked.connect(self.save_position)
        self.grid_layout.addWidget(self.save_pos_button, 0, 3)
    def make_recover_pos_button(self):
        self.recover_pos_button = QPushButton("recover pos", self)
        self.recover_pos_button.setToolTip("recover the set position of the motor")
        self.recover_pos_button.clicked.connect(self.recover_position)
        self.grid_layout.addWidget(self.recover_pos_button, 1, 3)
    def make_keyboard_button(self):
        self.keyboard_button = QPushButton("keyboard", self)
        self.keyboard_button.setToolTip("use the keyboard to move the motor,\nit works great")
        self.keyboard_button.clicked.connect(self.use_keyboard)
        self.grid_layout.addWidget(self.keyboard_button, 2, 1)
        
    def make_input_textfield(self):
        self.input_textfield = QLineEdit(self)
        self.input_textfield.setText("0.01")
        self.grid_layout.addWidget(self.input_textfield, 1, 1)

    def set_current_motor_position_label(self):
        self.current_motor_position_label.setText(str(round(self.motor.controller.position, 2)))
        
    def make_current_pos_label(self):
        self.current_motor_position_label = QLabel(self)
        try:
            self.current_motor_position_label.setText(self.motor.controller.position)
        except Exception:
            self.current_motor_position_label.setText("currently/nunavailable")
        self.grid_layout.addWidget(self.current_motor_position_label, 0, 1)    
        
    def make_keyboard_label(self):
        self.keyboard_label = QLabel(self)
        self.keyboard_label.setText("use keyboard\n(w/s, q to quit)")
        self.grid_layout.addWidget(self.keyboard_label, 2, 0)
    def make_save_label(self):
        self.save_label = QLabel(self)
        self.save_label.setText("save pos:")
        self.grid_layout.addWidget(self.save_label, 0, 2)
    def make_recover_label(self):
        self.recover_label = QLabel(self)
        self.recover_label.setText("recover pos:")
        self.grid_layout.addWidget(self.recover_label, 1, 2)
        
    def go_home_motor(self):
        self.motor.controller.move_home(True)
        self.set_current_motor_position_label()
        
    def go_to_input(self):
        try:
            go_to_input = float(self.input_textfield.text())
            self.motor.move_absolute(go_to_input * ur("micrometer"))
            self.set_current_motor_position_label()
        except ValueError:
            print("The input is not a float, change this")
            return
    
    def save_position(self):
        #make sure the user knows the button is pressed by setting it to a different color
        self.save_pos_button.setStyleSheet("background-color: green")
        #get positions
        try:
            self.position = self.motor.controller.position
        except Exception:
            #the motor position has not been found, could be because it is a 
            #piezo motor or because the software is not running as expected. 
            print("the position has not been set yet")
            self.position = None

    def recover_position(self):
        #set position of motors
        #(this only works if the position of the motors is from the home position):
        #so, that should be changed.
        print(self.position)
        if self.position == None:
            print("the positions have not been set!")
            return
        else:
            retrieved_position = self.motor.controller.position
            self.motor.controller.set_position = float(retrieved_position)
        
        
    def use_keyboard(self):
        #set text of keyboard_label to using keyboard
        self.keyboard_label.setText("using keyboard/npress q to exit")
        # Collect events until released
        self.worker_thread = WorkThread(self.create_keyboard_listener)
        self.worker_thread.start()
        
        #set the text back to you can use the keyboard.
        self.keyboard_label.setText("use keyboard\nto control selected\n combobox motor:")
    def create_keyboard_listener(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()
    def on_press(self, key):
        """ 
        In this method if the w is pressed the motor 
        selected in the combobox will move forward or if 
        s is pressed the motor will move backward.
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
        In this method if the w or s is released the motor will stop moving.
        If q is released the keyboard mode stops. 
        """
        if str(key) == "'w'" or str(key) == "'s'":
            #stop the motor from going
            self.motor.controller.stop_profiled()
            self.set_current_motor_position_label()
        elif str(key) == "'q'":
            # Stop listener
            if self.worker_thread.isRunning():
                self.set_current_motor_position_label()
                self.worker_thread.quit()
                self.worker_thread.wait()
                return False
    

if __name__ == '__main__':
    serial_number = 83815760
    app = QApplication(sys.argv)
    ex = App(serial_number)
    sys.exit(app.exec_())
