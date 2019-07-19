from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLineEdit, QLabel, QMessageBox, QComboBox, \
    QSizePolicy, QDockWidget
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject



import logging
import sys
import time
import random

from hyperion.instrument.osa.osa_instrument import OsaInstrument
from hyperion import ur, Q_
from hyperion.view.general_worker import WorkThread
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
#todo figure out what goes wrong with the instr. in the view.
"""
An idea is that something with the signal goes wrong which causes the pyvisa things to go invalid. 
This is true, I think I confirmed this, maybe it is just a concidence, I am not really sure.  
What goes wrong is that at some point after the gui is initialized the connection becomes invalid. But why would this be?  
An idea is to put this question on stackoverflow, maybe somebody does know the answer to this problem. 
Never shot is always mis
"""
class App(QDockWidget):

    some_signal = pyqtSignal()

    def __init__(self, instr):
        super().__init__()
        self.title = 'PyQt5 just a window'
        self.left = 50          #how many pixels are away from the left of the GUI
        self.top = 50           #how many pixels are away form the top of the GUI
        self.width = 700        #how many pixels in width the GUI is
        self.height = 350       #how many pixels in height the GUI is
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class App created')
        self.initUI()
        self.instr = instr

    def initUI(self):
        self.set_gui_constructor()

        self.set_textboxs()
        #self.set_textboxs_to_osa_machine_values()

        self.set_labels()

        self.set_submit_button()

        self.set_recommended_sample_points_button()

        self.m = PlotCanvas(self, width=4, height=3)
        self.m.move(310, 15)

        #self.show()
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
        self.button_submit = QPushButton('submit', self)
        self.button_submit.setToolTip('You are hovering over the button, \n what do you expect?')
        # button.move() sets the button on the given position you specify.
        self.button_submit.move(200, 200)
        #self.some_signal.connect(self.on_click_submit)
        #self.some_signal.emit()
        self.button_submit.clicked.connect(self.on_click_submit)

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
        self.textbox_end_wav.resize(60, 20)
    def set_start_wav_textbox(self):
        # this is the start_wav_textbox
        self.textbox_start_wav = QLineEdit(self)
        self.textbox_start_wav.move(20, 22)
        self.textbox_start_wav.resize(60, 20)

    def get_chosen_optical_resolution(self):
        return self.dropdown_optical_resolution.currentText()
    def get_chosen_sensitivity(self):
        return self.dropdown_sensitivity.currentText()


    def on_click_recommended(self):
        print("the recommended sample points will be calculated ")
        if self.instr.controller._is_initialized:
            self.instr.controller.perform_single_sweep()
        else:
            print("pyvisa does not work like intended")
            print(id(self.instr.controller._osa))

        self.textbox_sample_points.setText("")

        #check if the textboxs are not empty
        if self.is_start_wav_not_empty() and self.is_end_wav_not_empty():
            #all fields are filled
            self.get_recommended_sample_points()
        else:
            #some parameter are missing in one of the textboxs
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

    def get_values_from_textboxs(self):
        # get all the values from the textfields
        start_wav = self.get_start_wav()
        end_wav = self.get_end_wav()
        optical_resolution = self.get_optical_resolution()
        sample_points = self.get_sample_points()
        return end_wav, optical_resolution, sample_points, start_wav
    def get_sample_points(self):
        sample_points = self.textbox_sample_points.text()
        return int(sample_points)
    def get_optical_resolution(self):
        optical_resolution = self.dropdown_optical_resolution.currentText()
        return float(optical_resolution)
    def get_end_wav(self):
        end_wav = self.textbox_end_wav.text()
        return Q_(end_wav)
    def get_start_wav(self):
        start_wav = self.textbox_start_wav.text()
        return Q_(start_wav)

    def get_recommended_sample_points(self):
        self.textbox_sample_points.setText(
            str(int(1 + (2 * (Q_(self.textbox_end_wav.text()) - Q_(self.textbox_start_wav.text())).m_as('nm') / float(
                self.dropdown_optical_resolution.currentText())))))

    ###########################################################################################
    def on_click_submit(self):
        if self.instr.controller._is_initialized:
            self.instr.controller.perform_single_sweep()
        else:
            print("pyvisa does not work like intended")
            print(id(self.instr.controller._osa))

        self.logger.info('submit button clicked')

        self.get_submit_button_status()
        if self.is_start_wav_not_empty() and self.is_end_wav_not_empty() and self.is_sample_points_not_empty():
            #self.logger.info('fields not empty, grabbing fields')
            end_wav, optical_resolution, sample_points, start_wav = self.get_values_from_textboxs()
            #check if conditions for a single sweep are met
            if self.instr.is_start_wav_value_correct(start_wav) and self.instr.is_end_wav_value_correct(end_wav) and self.instr.is_end_wav_bigger_than_start_wav(start_wav,end_wav):
                #all tests are succesfull. now the rest of the code may be executed.
                # set the settings of the osa machine

                print('setting parameters in instrument')
                print('set_parameters_for_osa_machine( ... )')
                self.set_parameters_for_osa_machine(end_wav, optical_resolution, sample_points, start_wav)

                #try:
                self.make_thread()
                #except:
                #    print("exception occured: "+str(sys.exc_info()[0]))
                self.plot_data()

            self.get_output_message(end_wav, optical_resolution, sample_points, start_wav)
            self.set_textboxs_to_osa_machine_values()

        else:
            self.error_message_not_all_fields_are_filled()

    def set_parameters_for_osa_machine(self, end_wav, optical_resolution, sample_points, start_wav):
        #print(self.instr.start_wav)
        #print(self.instr.end_wav)
        #print(self.instr.optical_resolution)
        #print(self.instr.sample_points)
        self.instr.start_wav = Q_(start_wav)
        self.instr.end_wav = Q_(end_wav)
        self.instr.optical_resolution = float(optical_resolution)
        self.instr.sample_points = int(sample_points)

    def make_thread(self):
        print('starting sweep')
        print(id(self.instr.controller._osa))

        self.worker_thread = WorkThread(self.instr.take_spectrum)
        #self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        print("starting")
        self.worker_thread.start()
        #self.worker_thread.quit()
        """
        while self.worker_thread.is_running:
            time.sleep(2)
            print('waiting after sweep')
        print("proces finished")
        """

    def plot_data(self):
        wav = self.instr.wav
        spec = self.instr.spec
        PlotCanvas.plot(self.m, spec, wav)

    def set_textboxs_to_osa_machine_values(self):
        # set the textboxs to the value from the osa machine
        self.textbox_start_wav.setText("{} nm".format(self.instr.start_wav.m_as('nm')))
        self.textbox_end_wav.setText("{} nm".format(self.instr.end_wav.m_as('nm')))
        self.textbox_sample_points.setText("{}".format(int(self.instr.sample_points)))
    def get_output_message(self, end_wav, optical_resolution, sample_points, start_wav):
        # make a textbox to display given values.
        QMessageBox.question(self, 'What is this, a response?', "You typed: " + str(start_wav) + "\n" + str(end_wav) +
                             "\n" + str(optical_resolution) + "\n" + str(sample_points), QMessageBox.Ok,
                             QMessageBox.Ok)
    def get_submit_button_status(self):
        # when the button is clicked this method will be executed
        print('button says something')
        self.statusBar().showMessage("you have clicked the button, nothing happens(yet)")


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
    def plot(self, spec, wav):
        data = wav
        ax = self.figure.add_subplot(111)
        ax.plot(data, spec)
        ax.set_title('spectrum of light')
        self.draw()
        #ax.cla() causes the axes to clear it self from the data given. THIS IS mandatory
        ax.cla()


if __name__ == '__main__':
    # , 'controller':'hyperion.controller.osa/osacontroller', 'port':'AUTO'
    from hyperion import _logger_format, _logger_settings
    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    

    with OsaInstrument(settings ={'dummy': False, 'controller':'hyperion.controller.osa.osa_controller/OsaController'}) as instr:
        instr.initialize()

        app = QApplication([])
        ex = App(instr) #mandatory in order to call osainstrument in osa_view class
        ex.show()

        instr.finalize()
        sys.exit(app.exec_())

""""
app = QApplication([])
    win = MainWindow(exp)
    win.show()
    app.exit(app.exec_())
"""