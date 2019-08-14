import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QGridLayout, QPushButton, QWidget, QSlider, QLabel,
                             QComboBox, QLineEdit)

from hyperion.instrument.motor.thorlabs_motor_instrument import Thorlabsmotor
#import keyboard 
#todo make save logic
#todo make recover logic


"""
code om te implementeren op een gegeven moment. FF vragen aan ben of hij
weet hoe je dit kan implementeren in de code hier onder. 
https://stackoverflow.com/questions/24072790/detect-key-press-in-python

import keyboard  # using module keyboard
while True:  # making a loop
    try:  # used try so that if user pressed other than the given key error will not be shown
        if keyboard.is_pressed('q'):  # if key 'q' is pressed 
            print('You Pressed A Key!')
            break  # finishing the loop
        else:
            pass
    except:
        break  # if user pressed a key other than the given key the loop will break
"""

class App(QWidget):

    def __init__(self, motor_hub):
        super().__init__()
        self.title = 'thorlabs motors GUI'
        self.left = 50
        self.top = 50
        self.width = 400
        self.height = 200
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.motor_hub = motor_hub
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.initialize_available_motors()
        
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
        self.make_motor_current_position_label()
    def make_buttons(self):
        self.make_save_pos_1_button()
        self.make_save_pos_2_button()
        self.make_save_pos_3_button()
        self.make_recover_1_button()
        self.make_recover_2_button()
        self.make_recover_3_button()
        self.make_go_home_button()
        self.make_go_to_button()
        
        
    def make_misc_gui_stuff(self):
        self.make_slider_z()
        self.make_slider_x()
        self.make_slider_y()
        
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
    
    def make_motor_current_position_label(self):
        self.current_motor_position_label = QLabel(self)
        try:
            self.current_motor_position_label.setText(self.motor_bag[self.motor_combobox.currentText()].controller.position())
        except Exception:
            self.current_motor_position_label.setText("currently\nunavailable")
        self.grid_layout.addWidget(self.current_motor_position_label, 1, 5)    
        
    #make buttons:
    def make_save_pos_1_button(self):
        button = QPushButton('save pos 1', self)
        button.setToolTip('save the first position')
        self.grid_layout.addWidget(button, 1, 1)    
    def make_save_pos_2_button(self):
        button = QPushButton('save pos 2', self)
        button.setToolTip('save the second position')
        self.grid_layout.addWidget(button, 2, 1)        
    def make_save_pos_3_button(self):
        button = QPushButton('save pos 3', self)
        button.setToolTip('save the third position')
        self.grid_layout.addWidget(button, 3, 1)
        
    def make_recover_1_button(self):
        button = QPushButton('recover 1', self)
        button.setToolTip('recover the first position')
        self.grid_layout.addWidget(button, 1, 3)        
    def make_recover_2_button(self):
        button = QPushButton('recover 2', self)
        button.setToolTip('recover the second position')
        self.grid_layout.addWidget(button, 2, 3)        
    def make_recover_3_button(self):
        button = QPushButton('recover 3', self)
        button.setToolTip('recover the third position')
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
        
    #make misc gui stuff:
    def make_slider_z(self):
        self.slider_z = QSlider(Qt.Vertical, self)
        self.slider_z.setFocusPolicy(Qt.StrongFocus)
        self.slider_z.setTickPosition(QSlider.TicksBothSides)
        self.slider_z.setMinimum(1)
        self.slider_z.setMaximum(9)
        self.slider_z.setValue(5)
        self.slider_z.setTickInterval(9)
        #self.slider_z.setSingleStep(1)
        
        
        self.slider_z.sliderReleased.connect(self.set_slider_z_to_the_middle)
        self.slider_z.sliderMoved.connect(self.make_slider_z_motor_move)
        self.grid_layout.addWidget(self.slider_z, 4, 5)     
    def make_slider_x(self):
        self.slider_x = QSlider(Qt.Vertical, self)
        self.slider_x.setFocusPolicy(Qt.StrongFocus)
        self.slider_x.setTickPosition(QSlider.TicksBothSides)
        self.slider_x.setMinimum(1)
        self.slider_x.setMaximum(9)
        self.slider_x.setValue(5)
        self.slider_x.setTickInterval(9)
        self.slider_x.setSingleStep(1)
        self.slider_x.sliderReleased.connect(self.set_slider_x_to_the_middle)
        self.slider_x.sliderMoved.connect(self.make_slider_x_motor_move)
        self.grid_layout.addWidget(self.slider_x, 4, 1)
    def make_slider_y(self):
        self.slider_y = QSlider(Qt.Vertical, self)
        self.slider_y.setFocusPolicy(Qt.NoFocus)
        self.slider_y.setTickPosition(QSlider.TicksBothSides)
        self.slider_y.setMinimum(1)
        self.slider_y.setMaximum(9)
        self.slider_y.setValue(5)
        self.slider_y.setTickInterval(9)
        self.slider_y.setSingleStep(1)
        self.slider_y.sliderReleased.connect(self.set_slider_y_to_the_middle)
        self.slider_y.sliderMoved.connect(self.make_slider_y_motor_move)
        self.grid_layout.addWidget(self.slider_y, 4, 3)
        
    def make_dropdown_motor(self):    
        list_with_motors = []
        self.motor_combobox = QComboBox(self) 
        for index in self.motor_hub.controller.list_available_devices():
            list_with_motors.append(str(index[1]))
        self.motor_combobox.addItems(list_with_motors)
        self.motor_combobox.currentIndexChanged.connect(self.set_current_motor_label)
        self.grid_layout.addWidget(self.motor_combobox, 1, 7)
    def make_go_to_input_textfield(self):
        self.input_textfield = QLineEdit(self)
        self.input_textfield.setText("0.01")
        self.grid_layout.addWidget(self.input_textfield, 2, 7)
        
    def initialize_available_motors(self):
        #todo, this setup is very hacky and not the hyperion way to do this.
        #this should be changed when I know how to do this the right way.
        self.motor_bag = {}
        opteller = 0
        for serial_number in self.motor_hub.controller.list_available_devices():
            serial_number = str(serial_number[1])
            self.motor_bag[serial_number] = Thorlabsmotor(settings = {'controller': 'hyperion.controller.thorlabs.TDC001/TDC001',
                                    'serial_number' : str(self.motor_hub.controller.list_available_devices()[opteller][1])})
            self.motor_bag[serial_number].initialize(int(serial_number))
            opteller += 1
    def set_slider_z_to_the_middle(self):
        self.slider_z.setValue(5)
        self.motor_bag[self.motor_combobox.currentText()].controller.stop_profiled()
    def set_slider_x_to_the_middle(self):
        self.slider_x.setValue(5)
        self.motor_bag[self.motor_combobox.currentText()].controller.stop_profiled()
    def set_slider_y_to_the_middle(self):
        self.slider_y.setValue(5)
        self.motor_bag[self.motor_combobox.currentText()].controller.stop_profiled()
    def make_slider_z_motor_move(self):
        if self.slider_z.value() > 5:
            #moving forward
            self.motor_bag[self.motor_combobox.currentText()].controller.move_velocity(2)
        elif self.slider_z.value() < 5:
            #moving reverse
            self.motor_bag[self.motor_combobox.currentText()].controller.move_velocity(1)
    def make_slider_x_motor_move(self):
        if self.slider_x.value() > 5:
            #moving forward
            self.motor_bag[self.motor_combobox.currentText()].controller.move_velocity(2)
        elif self.slider_x.value() < 5:
            #moving reverse
            self.motor_bag[self.motor_combobox.currentText()].controller.move_velocity(1)
    def make_slider_y_motor_move(self):
        if self.slider_y.value() > 5:
            #moving forward
            self.motor_bag[self.motor_combobox.currentText()].controller.move_velocity(2)
        elif self.slider_y.value() < 5:
            #moving reverse
            self.motor_bag[self.motor_combobox.currentText()].controller.move_velocity(1)
    
    def set_current_motor_label(self):
        #in this function the position value is retrieved and round + set in a label.
        self.current_motor_position_label.setText(str(round(self.motor_bag[self.motor_combobox.currentText()].controller.position, 2)))
        
    def go_home_motor(self):
        selected_motor = str(self.motor_combobox.currentText())
        self.motor_bag[selected_motor].controller.move_home(True)
        
    def go_to_input(self):
        selected_motor = str(self.motor_combobox.currentText())
        try:
            go_to_input = float(self.input_textfield.text())
            self.motor_bag[selected_motor].move_relative_um(go_to_input)
        except ValueError:
            print("The input is not a float, change this")
            return

        
if __name__ == '__main__':
    motor_hub = Thorlabsmotor()
    app = QApplication(sys.argv)
    ex = App(motor_hub)
    sys.exit(app.exec_())
