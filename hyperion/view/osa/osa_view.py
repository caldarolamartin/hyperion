import sys

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLineEdit, QLabel, QMessageBox, QComboBox
from PyQt5.QtCore import pyqtSlot

from hyperion.instrument.osa import osa_instrument
from hyperion.controller.osa import osacontroller

#todo add the sensitivity parameter in osa_controller and osa_instrument
#todo add labels which tell the user the current value of the osa machine

class App(QMainWindow):

    def __init__(self, instr):
        super().__init__()
        self.title = 'PyQt5 just a window'
        self.left = 50 #how many pixels are away from the left of the GUI
        self.top = 50 #how many pixels are away form the top of the GUI
        self.width = 340 # how many pixels in width the GUI is
        self.height = 280 # how many pixels in height the GUI is
        self.instr = instr
        self.initUI()

    def initUI(self):
        self.set_gui_constructor()

        self.set_textboxs()

        self.set_labels()

        self.set_submit_button()

        self.set_recommended_sample_points_button()

        self.show()
    def set_gui_constructor(self):
        # a constructor to set the properties of  the GUI in
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.statusBar().showMessage("Just some text")

    def set_recommended_sample_points_button(self):
        # calculate the recommended sample_points
        button_calculate_recommended_sample_points = QPushButton('get recommended sample_points', self)
        button_calculate_recommended_sample_points.setToolTip(
            "click this button to \n get the recommended sample_points")
        # button.move() sets the button on the given position you specify.
        button_calculate_recommended_sample_points.move(100, 200)
        button_calculate_recommended_sample_points.clicked.connect(self.on_click_recommended)
    def set_submit_button(self):
        # submit button code
        button_submit = QPushButton('submit', self)
        button_submit.setToolTip('You are hovering over the button, \n what do you expect?')
        # button.move() sets the button on the given position you specify.
        button_submit.move(200, 200)
        button_submit.clicked.connect(self.on_click_submit)

    def set_labels(self):
        self.set_start_wav_label()
        self.set_end_wav_label()
        self.set_optical_resolution_label()
        self.set_sample_points_label()
        self.set_sensitivity_label()
    def set_sensitivity_label(self):
        #set the sensitivity label
        self.label_sensitivity = QLabel(self)
        self.label_sensitivity.move(20, 130)
        self.label_sensitivity.setText("the sensitivity")
        self.label_sensitivity.adjustSize()
    def set_sample_points_label(self):
        # the sample points label
        self.label_sample_points = QLabel(self)
        self.label_sample_points.move(20, 100)
        self.label_sample_points.setText("the amount of sample points")
        self.label_sample_points.adjustSize()
    def set_optical_resolution_label(self):
        # the optical resolution label
        self.label_optical_resolution = QLabel(self)
        self.label_optical_resolution.move(20, 70)
        self.label_optical_resolution.setText("the optical resolution in stepvalue of nm")
        self.label_optical_resolution.adjustSize()
    def set_end_wav_label(self):
        # the end_wav label
        self.label_end_wav = QLabel(self)
        self.label_end_wav.move(20, 40)
        self.label_end_wav.setText("the end wavelength, from 600.00 nm to 1750.00 nm")
        self.label_end_wav.adjustSize()
    def set_start_wav_label(self):
        # the start_wav label
        self.label_start_wav = QLabel(self)
        self.label_start_wav.move(20, 10)
        self.label_start_wav.setText("the start wavelength, from 600.00 nm to 1750.00 nm")
        self.label_start_wav.adjustSize()

    def set_textboxs(self):
        self.set_start_wav_textbox()
        self.set_end_wav_text_box()
        self.set_optical_resolution_textbox()
        self.set_sample_points_textbox()
        self.set_sensitivity_dropdown()
    def set_sensitivity_dropdown(self):
        #this is the sensitivity_dropdown
        self.dropdown_sensitivity = QComboBox(self)
        self.dropdown_sensitivity.addItems(["sensitivity normal range","sensitivity normal range automatic","sensitivity medium range","sensitivity high 1 range","sensitivity high 2 range","sensitivity high 3 range"])
        self.dropdown_sensitivity.move(20, 142)
        self.dropdown_sensitivity.resize(175, 20)
    def set_sample_points_textbox(self):
        # this is the sample_points_textbox
        self.textbox_sample_points = QLineEdit(self)
        self.textbox_sample_points.move(20, 112)
        self.textbox_sample_points.resize(50, 20)
    def set_optical_resolution_textbox(self):
        # this is the optical_resolution_dropdown
        self.dropdown_optical_resolution = QComboBox(self)
        self.dropdown_optical_resolution.addItems(["0.01","0.02","0.05","0.1","0.2","0.5","1.0","2.0","5.0"])
        self.dropdown_optical_resolution.move(20, 82)
        self.dropdown_optical_resolution.resize(75, 20)
    def set_end_wav_text_box(self):
        # this is the end_wav_textbox
        self.textbox_end_wav = QLineEdit(self)
        self.textbox_end_wav.move(20, 52)
        self.textbox_end_wav.resize(50, 20)
    def set_start_wav_textbox(self):
        # this is the start_wav_textbox
        self.textbox_start_wav = QLineEdit(self)
        self.textbox_start_wav.move(20, 22)
        self.textbox_start_wav.resize(50, 20)

    def get_chosen_optical_resolution(self):
        return self.dropdown_optical_resolution.currentText()
    def get_chosen_sensitivity(self):
        return self.dropdown_sensitivity.currentText()


    @pyqtSlot()
    def on_click_recommended(self):
        print("the recommended sample points will be calculated ")
        self.textbox_sample_points.setText("")

        #check if the textboxs are not empty
        if self.is_start_wav_not_empty() and self.is_end_wav_not_empty():
            #all fields are filled
            osa_instrument.get_recommended_sample_points(self)
        else:
            #some parameter is missing in one of the textboxs
            self.error_message_not_all_fields_are_filled()

    def is_sample_points_not_empty(self):
        if self.textbox_sample_points.text() != "":
            return True
        else:
            return False
    def is_end_wav_not_empty(self):
        if self.textbox_end_wav.text() != "":
            return True
        else:
            return False
    def is_start_wav_not_empty(self):
        if self.textbox_start_wav.text() != "":
            return True
        else:
            return False

    def error_message_not_all_fields_are_filled(self):
        message = "You did not type the\n"

        if not self.is_start_wav_not_empty():
            message += " start wavelength value\n"
        if not self.is_end_wav_not_empty():
            message += " end wavelength value\n"
        if not self.is_optical_resolution_not_empty():
            message += " optical resolution value\n"
        if not self.is_sample_points_not_empty():
            message += " sample points value\n"
        message += "you should set the specified value\n"

        QMessageBox.question(self, 'you did something wrong', message,
                             QMessageBox.Ok,
                             QMessageBox.Ok)

    @pyqtSlot()
    def on_click_submit(self):
        self.get_submit_button_status()
        if self.is_start_wav_not_empty() and self.is_end_wav_not_empty() and self.is_sample_points_not_empty():
            end_wav, optical_resolution, sample_points, start_wav = osa_instrument.get_values_from_textboxs(self)

            #check if conditions for a single sweep are met
            if osa_instrument.is_start_wav_value_correct(start_wav) and osa_instrument.is_end_wav_value_correct(end_wav) and osa_instrument.is_end_wav_bigger_than_start_wav(start_wav,end_wav):
                #all tests are succesfull. now the rest of the code may be executed.

                # set the settings of the osa machine
                self.set_parameters_for_osa_machine(end_wav, optical_resolution, sample_points, start_wav)

                #perform the sweep
                self.instr.perform_single_sweep()
                self.instr.wait_for_osa(5)
                self.instr.get_data()

            self.get_output_message(end_wav, optical_resolution, sample_points, start_wav)
            self.set_textboxs_to_empty_value()

        else:
            self.error_message_not_all_fields_are_filled()

    def set_parameters_for_osa_machine(self, end_wav, optical_resolution, sample_points, start_wav):
        #print(self.dev.start_wav)
        #print(self.dev.end_wav)
        #print(self.dev.optical_resolution)
        #print(self.dev.sample_points)
        self.instr.start_wav = float(start_wav)
        self.instr.end_wav = float(end_wav)
        self.instr.optical_resolution = float(optical_resolution)
        self.instr.sample_points = float(sample_points)


    def set_textboxs_to_empty_value(self):
        # set the textboxs to a specified value
        self.textbox_start_wav.setText("")
        self.textbox_end_wav.setText("")
        self.textbox_optical_resolution.setText("")
        self.textbox_sample_points.setText("")
    def get_output_message(self, end_wav, optical_resolution, sample_points, start_wav):
        # make a textbox to display given values.
        QMessageBox.question(self, 'What is this, a response?', "You typed: " + start_wav + "\n" + end_wav +
                             "\n" + optical_resolution + "\n" + sample_points, QMessageBox.Ok,
                             QMessageBox.Ok)
    def get_submit_button_status(self):
        # when the button is clicked this method will be executed
        print('button says something')
        self.statusBar().showMessage("you have clicked the button, nothing happens(yet)")


if __name__ == '__main__':
    # , 'controller':'hyperion.controller.osa/osacontroller', 'port':'AUTO'

    with osa_instrument.OsaInstrument(settings ={'dummy': False, 'controller':'hyperion.controller.osa.osacontroller/OsaController'}) as instr:
        instr.initialize()

        app = QApplication(sys.argv)
        ex = App(instr) #mandatory in order to call osacontroller in osa_view class

        instr.finalize()
        sys.exit(app.exec_())

