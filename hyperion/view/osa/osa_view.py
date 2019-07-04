import sys
from typing import List

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLineEdit, QLabel, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 just a window'
        self.left = 50 #how many pixels are away from the left of the GUI
        self.top = 50 #how many pixels are away form the top of the GUI
        self.width = 340 # how many pixels in width the GUI is
        self.height = 280 # how many pixels in height the GUI is
        self.initUI()

    def initUI(self):
        self.set_gui_constructor()

        self.set_textboxs()

        self.set_labels()

        self.set_submit_button()

        self.set_recommended_sample_points_button()
        #show the GUI
        self.show()

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

    def set_sample_points_label(self):
        # the sample points label
        self.label_sample_points = QLabel(self)
        self.label_sample_points.move(20, 100)
        self.label_sample_points.setText("the sample points")
        self.label_sample_points.adjustSize()

    def set_optical_resolution_label(self):
        # the optical resolution label
        self.label_optical_resolution = QLabel(self)
        self.label_optical_resolution.move(20, 70)
        self.label_optical_resolution.setText("the optical resolution")
        self.label_optical_resolution.adjustSize()

    def set_end_wav_label(self):
        # the end_wav label
        self.label_end_wav = QLabel(self)
        self.label_end_wav.move(20, 40)
        self.label_end_wav.setText("the end wavelength, from 600.00 to 1750.00")
        self.label_end_wav.adjustSize()

    def set_start_wav_label(self):
        # the start_wav label
        self.label_start_wav = QLabel(self)
        self.label_start_wav.move(20, 10)
        self.label_start_wav.setText("the start wavelength, from 600.00 to 1750.00")
        self.label_start_wav.adjustSize()

    def set_gui_constructor(self):
        # a constructor to set the properties of  the GUI in
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.statusBar().showMessage("Just some text")

    def set_textboxs(self):
        self.set_start_wav_textbox()
        self.set_end_wav_text_box()
        self.set_optical_resolution_textbox()
        self.set_sample_points_textbox()

    def set_sample_points_textbox(self):
        # this is the sample_points_textbox
        self.textbox_sample_points = QLineEdit(self)
        self.textbox_sample_points.move(20, 112)
        self.textbox_sample_points.resize(50, 20)

    def set_optical_resolution_textbox(self):
        # this is the optical_resolution_textbox
        self.textbox_optical_resolution = QLineEdit(self)
        self.textbox_optical_resolution.move(20, 82)
        self.textbox_optical_resolution.resize(50, 20)

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

    @pyqtSlot()
    def on_click_recommended(self):
        #when the recommended_sample_points button is clicked something happens
        print("the recommended sample points will be calculated ")
        self.textbox_sample_points.setText("")

        #check if the textboxs are not empty
        if self.is_start_wav_not_empty() and self.is_end_wav_not_empty() and self.is_optical_resolution_not_empty():
            #alle velden zijn ingevuld
            self.get_recommended_sample_points()
        else:
            #er is iets nog niet ingevuld
            self.error_message_not_all_fields_are_filled()

    def is_sample_points_not_empty(self):
        if self.textbox_sample_points.text() != "":
            return True
        else:
            return False

    def is_optical_resolution_not_empty(self):
        if self.textbox_optical_resolution.text() != "":
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

    def get_recommended_sample_points(self):
        self.textbox_sample_points.setText(
            str(1 + (2 * (float(self.textbox_end_wav.text()) - float(self.textbox_start_wav.text())) / float(
                self.textbox_optical_resolution.text()))))

    @pyqtSlot()
    def on_click_submit(self):
        self.get_submit_button_status()
        if self.is_start_wav_not_empty() and self.is_end_wav_not_empty() and self.is_optical_resolution_not_empty() and self.is_sample_points_not_empty():
            end_wav, optical_resolution, sample_points, start_wav = self.get_values_from_textboxs()

            self.is_start_wav_value_correct(start_wav)
            self.is_end_wav_value_correct(end_wav)
            self.is_optical_resolution_correct(optical_resolution)
            self.is_end_wav_bigger_than_start_wav(end_wav, start_wav)

            self.get_output_message(end_wav, optical_resolution, sample_points, start_wav)
            self.set_textboxs_to_empty_value()

        else:
            #er is een veld nog niet ingevuld, ik weet niet welke
            self.error_message_not_all_fields_are_filled()

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

    def get_values_from_textboxs(self):
        # get all the values from the textfields
        start_wav = self.textbox_start_wav.text()
        end_wav = self.textbox_end_wav.text()
        optical_resolution = self.textbox_optical_resolution.text()
        sample_points = self.textbox_sample_points.text()
        return end_wav, optical_resolution, sample_points, start_wav

    def get_submit_button_status(self):
        # when the button is clicked this method will be executed
        print('button says something')
        self.statusBar().showMessage("you have clicked the button, nothing happens(yet)")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())