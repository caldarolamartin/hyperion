import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QGridLayout, QPushButton, QWidget, QSlider, QLabel,
                             QComboBox, QLineEdit)

from hyperion.instrument.thorlabs_motor.thorlabs_motor_instrument import Thorlabsmotor
from hyperion.view.general_worker import WorkThread
from pynput.keyboard import Listener
from hyperion import ur

class App(QWidget):

    def __init__(self, motor_hub):
        """
        This init of this class,
        make sure that the .yml file is correctly configurated, else it will not work, trust me, I am an expert.
        """
        super().__init__()
        self.title = 'thorlabs motors GUI'
        self.left = 50
        self.top = 50
        self.width = 400
        self.height = 200
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.motor_hub = motor_hub
        self.motor_bag = {}
        self.slider_dict = {}
        self.position_1_all_motors_dict = {}
        self.position_2_all_motors_dict = {}
        self.position_3_all_motors_dict = {}
        self.velocity_motors_dict = {}
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.motor_bag = self.motor_hub.initialize_available_motors(self.motor_bag)
        
        self.make_misc_gui_stuff()
        self.make_labels()
        self.make_buttons()
        
        self.show()
        
    def make_labels(self):    
        #make labels:
        self.make_save_pos_1_label()
        self.make_save_pos_2_label()
        self.make_save_pos_3_label()
        self.make_recover_1_label()
        self.make_recover_2_label()
        self.make_recover_3_label()
        self.make_x_coordinate_label()
        self.make_y_coordinate_label()
        self.make_z_coordinate_label()
        self.make_x_coordinate_second_label()
        self.make_y_coordinate_second_label()
        self.make_z_coordinate_second_label()
        self.make_motor_x_current_position_label()
        self.make_motor_y_current_position_label()
        self.make_motor_z_current_position_label()
        self.make_use_keyboard_label()
        self.make_go_faster_label()
    def make_buttons(self):
        #make buttons
        self.make_save_pos_3_button()
        self.make_save_pos_1_button()
        self.make_save_pos_2_button()
        self.make_recover_1_button()
        self.make_recover_2_button()
        self.make_recover_3_button()
        self.make_go_home_button()
        self.make_go_to_button()
        self.make_use_keyboard_button()
        
    def make_misc_gui_stuff(self):
        #make all the miscellaneous gui stuff. 
        """
        In this method th slider and other miscellaneous gui stuff will be made.
        The slider get made by adding a tuple with the name of the slider and the name of the
        thorlabs_motor that the slider will use.
        """
        slider_list = self.motor_hub.make_slider_list()
        opteller = 1
        for slider in slider_list:    
            self.make_slider(lambda: slider[0], slider[1], opteller)
            opteller += 2
        self.make_go_faster_slider()
        self.make_dropdown_motor()
        self.make_go_to_input_textfield()
    def make_save_pos_1_label(self):
        label = QLabel(self)
        label.setText("save pos. 1:")
        self.grid_layout.addWidget(label, 1, 0)        
    def make_save_pos_2_label(self):
        label = QLabel(self)
        label.setText("save pos. 2:")
        self.grid_layout.addWidget(label, 2, 0)        
    def make_save_pos_3_label(self):
        label = QLabel(self)
        label.setText("save pos. 3:")
        self.grid_layout.addWidget(label, 3, 0)
        
    def make_recover_1_label(self):
        label = QLabel(self)
        label.setText("recover 1:")
        self.grid_layout.addWidget(label, 1, 2)
    def make_recover_2_label(self):
        label = QLabel(self)
        label.setText("recover 2:")
        self.grid_layout.addWidget(label, 2, 2)
    def make_recover_3_label(self):
        label = QLabel(self)
        label.setText("recover 3:")
        self.grid_layout.addWidget(label, 3, 2)
        
    def make_x_coordinate_second_label(self):
        label = QLabel(self)
        label.setText("x: ")
        self.grid_layout.addWidget(label, 1, 4)
    def make_y_coordinate_second_label(self):
        label = QLabel(self)
        label.setText("y: ")
        self.grid_layout.addWidget(label, 2, 4)
    def make_z_coordinate_second_label(self):
        label = QLabel(self)
        label.setText("z: ")
        self.grid_layout.addWidget(label, 3, 4)
        
    def make_x_coordinate_label(self):
        label = QLabel(self)
        label.setText("speed\nx: ")
        self.grid_layout.addWidget(label, 4, 0)
    def make_y_coordinate_label(self):
        label = QLabel(self)
        label.setText("speed\ny: ")
        self.grid_layout.addWidget(label, 4, 2)        
    def make_z_coordinate_label(self):
        label = QLabel(self)
        label.setText("speed\nz: ")
        self.grid_layout.addWidget(label, 4, 4)
    
    def make_motor_x_current_position_label(self):
        """
        update the x position label.
        The same is done for the y and z in make_motor_y/z_current_position_label
        """
        self.current_motor_x_position_label = QLabel(self)
        try:
            self.current_motor_x_position_label.setText(self.motor_bag[self.motor_combobox.currentText()].controller.position())
        except Exception:
            self.current_motor_x_position_label.setText("currently\nunavailable")
        self.grid_layout.addWidget(self.current_motor_x_position_label, 1, 5)
    def make_motor_y_current_position_label(self):
        self.current_motor_y_position_label = QLabel(self)
        try:
            self.current_motor_y_position_label.setText(self.motor_bag[self.motor_combobox.currentText()].controller.position())    
        except Exception:
            self.current_motor_y_position_label.setText("currently\nunavailable")
        self.grid_layout.addWidget(self.current_motor_y_position_label, 2, 5)
    def make_motor_z_current_position_label(self):
        self.current_motor_z_position_label = QLabel(self)
        try:
            self.current_motor_z_position_label.setText(self.motor_bag[self.motor_combobox.currentText()].controller.position())    
        except Exception:
            self.current_motor_z_position_label.setText("currently\nunavailable")
        self.grid_layout.addWidget(self.current_motor_z_position_label, 3, 5)
        
    def make_use_keyboard_label(self):
        self.keyboard_label = QLabel(self)
        self.keyboard_label.setText("use keyboard\nto control selected\n combobox thorlabs_motor:")
        self.grid_layout.addWidget(self.keyboard_label, 3, 6)
    def make_go_faster_label(self):
        self.go_faster_label = QLabel(self)
        self.go_faster_label.setText("change\nthorlabs_motor speed:")
        self.grid_layout.addWidget(self.go_faster_label, 4, 6)
        
    #make buttons:
    def make_save_pos_1_button(self):
        self.save_1_button = QPushButton('save pos 1', self)
        self.save_1_button.setToolTip('save the first position')
        #self, button, color, position_all_motors_dict
        self.save_1_button.clicked.connect(lambda: self.save_position_for_all_motors(self.save_1_button, "green", self.position_1_all_motors_dict))
        self.grid_layout.addWidget(self.save_1_button, 1, 1)    
    def make_save_pos_2_button(self):
        self.save_2_button = QPushButton('save pos 2', self)
        self.save_2_button.setToolTip('save the second position')
        self.save_2_button.clicked.connect(lambda: self.save_position_for_all_motors(self.save_2_button, "yellow", self.position_2_all_motors_dict))
        self.grid_layout.addWidget(self.save_2_button, 2, 1)        
    def make_save_pos_3_button(self):
        self.save_3_button = QPushButton('save pos 3', self)
        self.save_3_button.setToolTip('save the third position')
        self.save_3_button.clicked.connect(lambda: self.save_position_for_all_motors(self.save_3_button, "red", self.position_3_all_motors_dict))
        self.grid_layout.addWidget(self.save_3_button, 3, 1)
        
    def make_recover_1_button(self):
        button = QPushButton('recover 1', self)
        button.setToolTip('recover the first position')
        button.clicked.connect(lambda: self.recover_position_all_motors(self.position_1_all_motors_dict))
        self.grid_layout.addWidget(button, 1, 3)        
    def make_recover_2_button(self):
        button = QPushButton('recover 2', self)
        button.setToolTip('recover the second position')
        button.clicked.connect(lambda: self.recover_position_all_motors(self.position_2_all_motors_dict))
        self.grid_layout.addWidget(button, 2, 3)        
    def make_recover_3_button(self):
        button = QPushButton('recover 3', self)
        button.setToolTip('recover the third position')
        button.clicked.connect(lambda: self.recover_position_all_motors(self.position_3_all_motors_dict))
        self.grid_layout.addWidget(button, 3, 3)
        
    def make_go_home_button(self):
        self.go_home_button = QPushButton('go home', self)
        self.go_home_button.setToolTip('go to home position')
        self.go_home_button.clicked.connect(self.go_home_motor)
        self.grid_layout.addWidget(self.go_home_button, 1, 6)
    def make_go_to_button(self):
        self.move_button = QPushButton('move to in um', self)
        self.move_button.setToolTip('move to given input')
        self.move_button.clicked.connect(self.go_to_input)
        self.grid_layout.addWidget(self.move_button, 2, 6)
    def make_use_keyboard_button(self):
        self.use_keyboard_button = QPushButton('use keyboard', self)
        self.use_keyboard_button.setToolTip('use keyboard to control motors')
        self.use_keyboard_button.clicked.connect(self.control_motor_with_keyboard)
        self.grid_layout.addWidget(self.use_keyboard_button, 3, 7)
    
    #make misc gui stuff:
    def make_slider(self, slider, motor_name, opteller):
        """
        In this method sliders get made automatically. 
        This done by getting the name of the slider an setting it in a slider_dict.
        The rest of the parameters get set in this method.
        
        :param slider: a slider name
        :type string
        :param motor_name: the name of the thorlabs_motor which connects with the slider
        :type string
        :param opteller: indication on which grid the slider must be set
        :type int
        """
        self.slider_ding = QSlider(Qt.Vertical, self)
        self.slider_ding.setFocusPolicy(Qt.StrongFocus)
        self.slider_ding.setTickPosition(QSlider.TicksBothSides)
        self.slider_ding.setMinimum(1)
        self.slider_ding.setMaximum(9)
        self.slider_ding.setValue(5)
        self.slider_ding.setTickInterval(1)
        self.slider_ding.setSingleStep(1)
        self.slider_ding.sliderReleased.connect(lambda: self.set_slider_to_middle(slider, motor_name))
        self.slider_ding.sliderMoved.connect(lambda: self.make_slider_motor_move(slider, motor_name))
        
        self.slider_dict[slider] = self.slider_ding
        self.grid_layout.addWidget(self.slider_dict[slider], 4, opteller)
    
    def set_slider_to_middle(self, slider, motor_name):
        """
        In this method an slider is set to the middle. This is done 
        through connecting a signal and slot.
        
        :param slider_object: an slider that must be set to it's middle
        :type QSlider
        :param motor_name: the name of the thorlabs_motor to stop
        :type string
        """
        self.slider_dict[slider].setValue(5)
        self.motor_bag[motor_name].controller.stop_profiled()
        
    def make_slider_motor_move(self, slider, motor_name):
        """
        In this method the thorlabs_motor moves if the slider is moved.
        
        :param slider_object: the slider that is being moved
        :type QSlider
        :param motor_name: the name of the thorlabs_motor to move
        :type string
        """
        if self.slider_dict[slider].value() > 5:
            #moving forward
            self.motor_bag[motor_name].controller.move_velocity(2)
        elif self.slider_dict[slider].value() < 5:
            #moving reverse
            self.motor_bag[motor_name].controller.move_velocity(1)    
    def make_go_faster_slider(self):
        """

        """
        self.go_faster_slider = QSlider(Qt.Horizontal, self)
        self.go_faster_slider.setFocusPolicy(Qt.StrongFocus)
        self.go_faster_slider.setTickPosition(QSlider.TicksBelow)
        self.go_faster_slider.setMinimum(0)
        self.go_faster_slider.setMaximum(10)
        self.go_faster_slider.setValue(0)
        self.go_faster_slider.setTickInterval(1)
        self.go_faster_slider.setSingleStep(1)
        self.go_faster_slider.sliderReleased.connect(self.change_motor_speed)
        self.grid_layout.addWidget(self.go_faster_slider, 4, 7)
    def change_motor_speed(self):
        #print("for thorlabs_motor: "+str(self.motor_combobox.currentText())+" the limits are: "+str(self.motor_bag[self.motor_combobox.currentText()].controller.get_velocity_parameter_limits()))
        output = self.motor_bag[self.motor_combobox.currentText()].controller.get_velocity_parameters()
        # minimum velocity = output[0]
        # acceleration = ouput[1]
        # maximum velocity = output[2]
        if not self.motor_combobox.currentText() in self.velocity_motors_dict:
            #setting the original highest value of the thorlabs_motor to prevent degrading in speed.
            self.velocity_motors_dict[self.motor_combobox.currentText()] = output[2]
        if (output[0] - output[2]) == 0:
            #the numbers are equal meaning that the speed cannot change
            print("you cannot change the speed of this thorlabs_motor")
        else:
            #the speed can change
            total_speed = self.velocity_motors_dict[self.motor_combobox.currentText()] - output[0]
            tenth_of_total_speed = total_speed / 10
            print(tenth_of_total_speed)
            slider_value = self.go_faster_slider.value()
            print(slider_value)
            new_speed = slider_value * tenth_of_total_speed
            print("the max speed: "+str(self.velocity_motors_dict[self.motor_combobox.currentText()])+"the new speed "+str(new_speed))
            print("-"*40)
            if new_speed < output[2] and new_speed > output[0]:
                self.motor_bag[self.motor_combobox.currentText()].controller.set_velocity_parameters(output[0], output[1], new_speed)
            
    def make_dropdown_motor(self):    
        list_with_motors = []
        self.motor_combobox = QComboBox(self)
        #these are all the available motors:
        for index in self.motor_bag.keys():
            list_with_motors.append(str(index))
        self.motor_combobox.addItems(list_with_motors)
        self.motor_combobox.currentIndexChanged.connect(self.set_current_motor_label)
        self.grid_layout.addWidget(self.motor_combobox, 1, 7)
    def make_go_to_input_textfield(self):
        self.input_textfield = QLineEdit(self)
        self.input_textfield.setText("0.01")
        self.grid_layout.addWidget(self.input_textfield, 2, 7)
    
    def set_current_motor_label(self):
        """
        The position for the x, y, z motor will be set in this method.
        If another motor is found the x label will change. Why x...because, IDK. What else to do.
        """
        if self.motor_combobox.currentText() == "zMotor":
            self.current_motor_x_position_label.setText(str(round(self.motor_bag[self.motor_combobox.currentText()].controller.position, 2)))
        elif self.motor_combobox.currentText() == "yMotor": 
            self.current_motor_y_position_label.setText(str(round(self.motor_bag[self.motor_combobox.currentText()].controller.position, 2)))
        elif self.motor_combobox.currentText() == "testMotor":
            self.current_motor_z_position_label.setText(str(round(self.motor_bag[self.motor_combobox.currentText()].controller.position, 2)))
        else:
            #this is a thorlabs_motor that is not the zMotor, yMotor or the testMotor, so
            #let's set the x position to something else
            self.current_motor_x_position_label.setText(str(round(self.motor_bag[self.motor_combobox.currentText()].controller.position, 2)))
            
            
        
    def go_home_motor(self):
        selected_motor = str(self.motor_combobox.currentText())
        self.motor_bag[selected_motor].controller.move_home(True)
        self.set_current_motor_label()
        
    def go_to_input(self):
        selected_motor = str(self.motor_combobox.currentText())
        try:
            go_to_input = self.input_textfield.text() * ur('micrometer')
            self.motor_bag[selected_motor].move_absolute(float(go_to_input.magnitude))
            self.set_current_motor_label()
        except ValueError:
            print("The input is not a float, change this")
            return
        
    def on_press(self, key):
        """ 
        In this method if the w is pressed the thorlabs_motor
        selected in the combobox will move forward or if 
        s is pressed the thorlabs_motor will move backward.
        The w and s are written as: "'w'"/"'s'" because of syntacs.
        """
        if str(key) == "'w'":
            #forward
            self.set_current_motor_label()
            self.motor_bag[self.motor_combobox.currentText()].controller.move_velocity(2)
            self.set_current_motor_label()
        elif str(key) == "'s'":
            #backwards
            self.set_current_motor_label()
            self.motor_bag[self.motor_combobox.currentText()].controller.move_velocity(1)
            self.set_current_motor_label()
    def on_release(self, key):
        """
        In this method if the w or s is released the thorlabs_motor will stop moving.
        If q is released the keyboard mode stops. 
        """
        if str(key) == "'w'" or str(key) == "'s'":
            #stop the thorlabs_motor from going
            self.motor_bag[self.motor_combobox.currentText()].controller.stop_profiled()
            self.set_current_motor_label()
        elif str(key) == "'q'":
            # Stop listener
            if self.worker_thread.isRunning():
                self.set_current_motor_label()
                self.worker_thread.quit()
                self.worker_thread.wait()
                return False
    def control_motor_with_keyboard(self):
        """ 
        In this method with the Listener object you can 
        press a button on the keyboard and with that input a thorlabs_motor will move.
        
        """
        #set text of keyboard_label to using keyboard
        self.keyboard_label.setText("using keyboard/npress esc to exit")
        # Collect events until released
        self.worker_thread = WorkThread(self.create_keyboard_listener)
        self.worker_thread.start()
        
        #set the text back to you can use the keyboard.
        self.keyboard_label.setText("use keyboard\nto control selected\n combobox thorlabs_motor:")
    def create_keyboard_listener(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()
        
    def save_position_for_all_motors(self, button, color, position_all_motors_dict):
        #make sure the user knows the button is pressed by setting it to a different color
        button.setStyleSheet("background-color: "+color)
        #get positions
        for motor in self.motor_bag.items():
            #thorlabs_motor[0] == serial nummer
            #thorlabs_motor[1] == Thorlabs thorlabs_motor instance
            try:
                position = motor[1].controller.position
            except Exception:
                #the thorlabs_motor position has not been found, could be because it is a
                #piezo thorlabs_motor or because the software is not running as expected.
                print("for thorlabs_motor: "+ str(motor[0]) +" the position has not been set")
                position = None
            position_all_motors_dict[motor[0]] = position
    def recover_position_all_motors(self, position_all_motors_dict):
        #set position of motors
        #(this only works if the position of the motors is from the home position):
        #so, that should be changed. 
        if bool(position_all_motors_dict) == False:
            print("the positions have not been set!")
            return
        for motor in self.motor_bag.items():
            #thorlabs_motor[0] == serial nummer
            #thorlabs_motor[1] == Thorlabs thorlabs_motor instance
            retrieved_position = position_all_motors_dict[motor[0]]
            if retrieved_position != None and retrieved_position != motor[1].controller.position:
                motor[1].controller.set_position = float(retrieved_position)

if __name__ == '__main__':
    motor_hub = Thorlabsmotor()
    app = QApplication(sys.argv)
    ex = App(motor_hub)
    sys.exit(app.exec_())
