import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QWidget, QSlider, QLabel)
from PyQt5.QtGui import QIcon

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 simple window - pythonspot.com'
        self.left = 50
        self.top = 50
        self.width = 640
        self.height = 480
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
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
        self.make_x_coordinate_current_label()
        self.make_y_coordinate_current_label()
        self.make_z_coordinate_current_label()
        
        self.make_save_pos_1_button()
        self.make_save_pos_2_button()
        self.make_save_pos_3_button()
        self.make_recover_1_button()
        self.make_recover_2_button()
        self.make_recover_3_button()
        
        self.make_slider_z()
        self.make_slider_x()
        self.make_slider_y()
        
        self.show()
    #make labels:
    def make_save_pos_1_label(self):
        label = QLabel(self)
        label.setText("save pos. 1:")
        self.grid_layout.addWidget(label, 1, 2)
        
    def make_save_pos_2_label(self):
        label = QLabel(self)
        label.setText("save pos. 2:")
        self.grid_layout.addWidget(label, 2, 2)
        
    def make_save_pos_3_label(self):
        label = QLabel(self)
        label.setText("save pos. 3:")
        self.grid_layout.addWidget(label, 3, 2)
        
    def make_recover_1_label(self):
        label = QLabel(self)
        label.setText("recover 1:")
        self.grid_layout.addWidget(label, 1, 4)

    def make_recover_2_label(self):
        label = QLabel(self)
        label.setText("recover 2:")
        self.grid_layout.addWidget(label, 2, 4)

    def make_recover_3_label(self):
        label = QLabel(self)
        label.setText("recover 3:")
        self.grid_layout.addWidget(label, 3, 4)
        
        
    def make_x_coordinate_second_label(self):
        label = QLabel(self)
        label.setText("x: ")
        self.grid_layout.addWidget(label, 1, 0)
    def make_y_coordinate_second_label(self):
        label = QLabel(self)
        label.setText("y: ")
        self.grid_layout.addWidget(label, 2, 0)
    def make_z_coordinate_second_label(self):
        label = QLabel(self)
        label.setText("z: ")
        self.grid_layout.addWidget(label, 3, 0)
        
    def make_x_coordinate_label(self):
        label = QLabel(self)
        label.setText("x: ")
        self.grid_layout.addWidget(label, 0, 2)

    def make_y_coordinate_label(self):
        label = QLabel(self)
        label.setText("y: ")
        self.grid_layout.addWidget(label, 0, 4)
        
    def make_z_coordinate_label(self):
        label = QLabel(self)
        label.setText("z: ")
        self.grid_layout.addWidget(label, 0, 0)
    
    def make_x_coordinate_current_label(self):
        self.x_coordinate_label = QLabel(self)
        self.x_coordinate_label.setText("")
        self.grid_layout.addWidget(self.x_coordinate_label, 1, 1)
    
    def make_y_coordinate_current_label(self):
        self.y_coordinate_label = QLabel(self)
        self.y_coordinate_label.setText("")
        self.grid_layout.addWidget(self.y_coordinate_label, 2, 1)
    
    def make_z_coordinate_current_label(self):
        self.z_coordinate_label = QLabel(self)
        self.z_coordinate_label.setText("")
        self.grid_layout.addWidget(self.z_coordinate_label, 3, 1)
        
    #make buttons:
    def make_save_pos_1_button(self):
        button = QPushButton('save pos 1', self)
        button.setToolTip('save the first position')
        self.grid_layout.addWidget(button, 1, 3)
    
    def make_save_pos_2_button(self):
        button = QPushButton('save pos 2', self)
        button.setToolTip('save the second position')
        self.grid_layout.addWidget(button, 2, 3)
        
    def make_save_pos_3_button(self):
        button = QPushButton('save pos 3', self)
        button.setToolTip('save the third position')
        self.grid_layout.addWidget(button, 3, 3)
        
    def make_recover_1_button(self):
        button = QPushButton('recover 1', self)
        button.setToolTip('recover the first position')
        self.grid_layout.addWidget(button, 1, 5)
        
    def make_recover_2_button(self):
        button = QPushButton('recover 2', self)
        button.setToolTip('recover the second position')
        self.grid_layout.addWidget(button, 2, 5)
        
    def make_recover_3_button(self):
        button = QPushButton('recover 3', self)
        button.setToolTip('recover the third position')
        self.grid_layout.addWidget(button, 3, 5)
        
    #make sliders:
    def make_slider_z(self):
        self.slider_z = QSlider(Qt.Vertical, self)
        self.slider_z.setFocusPolicy(Qt.StrongFocus)
        self.slider_z.setTickPosition(QSlider.TicksBothSides)
        self.slider_z.setTickInterval(30)
        self.slider_z.setSingleStep(1)
        self.grid_layout.addWidget(self.slider_z, 0, 1)
        
    def make_slider_x(self):
        self.slider_x = QSlider(Qt.Vertical, self)
        self.slider_x.setFocusPolicy(Qt.StrongFocus)
        self.slider_x.setTickPosition(QSlider.TicksBothSides)
        self.slider_x.setTickInterval(30)
        self.slider_x.setSingleStep(1)
        self.grid_layout.addWidget(self.slider_x, 0, 3)
        
        
    def make_slider_y(self):
        self.slider_y = QSlider(Qt.Vertical, self)
        self.slider_y.setFocusPolicy(Qt.StrongFocus)
        self.slider_y.setTickPosition(QSlider.TicksBothSides)
        self.slider_y.setTickInterval(30)
        self.slider_y.setSingleStep(1)
        self.grid_layout.addWidget(self.slider_y, 0, 5)
        
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
