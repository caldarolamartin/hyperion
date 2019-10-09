"""
=======
OSA GUI
=======

This is the class to build a GUI for the OSA.


THere is a bug here that we do not understand:

    An idea is that something with the signal goes wrong which causes the pyvisa things to go invalid.
    This is true, I think I confirmed this, maybe it is just a concidence, I am not really sure.
    What goes wrong is that at some point after the gui is initialized the connection becomes invalid. But why would this be?
    An idea is to put this question on stackoverflow, maybe somebody does know the answer to this problem.
    Never shot is always mis

"""


from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLineEdit, QLabel, QMessageBox, QComboBox, \
    QSizePolicy, QGridLayout, QVBoxLayout

import logging
import sys

from hyperion.instrument.osa.osa_instrument import OsaInstrument
from hyperion import ur, Q_
from hyperion.view.general_worker import WorkThread
import matplotlib.pyplot as plt
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# todo figure out what goes wrong with the instr. in the view.

class OsaGui(QWidget):
    """ OSA Gui class.
    It builds the GUI for the OSA instrument.

    """

    def __init__(self, instr, draw):
        """ Init of the class.
            The class needs an instance of the osa instrument.
        """
        super().__init__()
        self.title = 'Osa gui'
        self.left = 50          #how many pixels are away from the left of the GUI
        self.top = 50           #how many pixels are away form the top of the GUI
        self.width = 700        #how many pixels in width the GUI is
        self.height = 350       #how many pixels in height the GUI is
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class App created')
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.instr = instr
        self.draw = draw
        self.initUI()

    def initUI(self):
        """
        This method initialises all the QWidgets needed.
        """
        self.set_gui_constructor()

        self.set_textboxs()

        #only works if the pyvisa bug is fixed
        #self.set_textboxs_to_osa_machine_values()

        self.set_labels()

        self.set_submit_button()

        self.set_recommended_sample_points_button()

        self.show()

    def set_gui_constructor(self):
        """ a constructor to set the properties of  the GUI in"""
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        #self.statusBar().showMessage("Just some text")

    def set_recommended_sample_points_button(self):
        """calculate the recommended sample_points"""
        button_calculate_recommended_sample_points = QPushButton('get recommended sample_points', self)
        button_calculate_recommended_sample_points.setToolTip(
            "click this button to \n get the recommended sample_points")
        self.layout.addWidget(button_calculate_recommended_sample_points, 11, 0)
        button_calculate_recommended_sample_points.clicked.connect(self.on_click_recommended)
    def set_submit_button(self):
        """code to make the submit button """
        self.button_submit = QPushButton('submit', self)
        self.button_submit.setToolTip('You are hovering over the button, \n what do you expect?')
        self.layout.addWidget(self.button_submit, 12, 0)
        self.button_submit.clicked.connect(self.on_click_submit)

    def set_labels(self):
        self.set_start_wav_label()
        self.set_end_wav_label()
        self.set_optical_resolution_label()
        self.set_sample_points_label()
        self.set_sensitivity_label()
    def set_sensitivity_label(self):
        # set the sensitivity label
        self.layout.addWidget(QLabel("the sensitivity"), 8, 0)
    def set_sample_points_label(self):
        # set the sample points label
        self.layout.addWidget(QLabel("the amount of sample points"), 6, 0)
    def set_optical_resolution_label(self):
        # set the optical resolution label
        self.layout.addWidget(QLabel("the optical resolution in stepvalue of nm"), 4, 0)
    def set_end_wav_label(self):
        # set the end_wav label
        self.layout.addWidget(QLabel("the end wavelength, from 600.00 nm to 1750.00 nm"), 2, 0)
    def set_start_wav_label(self):
        # set the start_wav label
        self.layout.addWidget(QLabel("the start wavelength, from 600.00 nm to 1750.00 nm"), 0, 0)

    def set_textboxs(self):
        self.set_start_wav_textbox()
        self.set_end_wav_text_box()
        self.set_optical_resolution_textbox()
        self.set_sample_points_textbox()
        self.set_sensitivity_dropdown()
    def set_sensitivity_dropdown(self):
        """"code to make the sensitivity_dropdown """
        self.dropdown_sensitivity = QComboBox(self)
        self.dropdown_sensitivity.addItems(
            ["sensitivity normal range", "sensitivity normal range automatic", "sensitivity medium range",
             "sensitivity high 1 range", "sensitivity high 2 range", "sensitivity high 3 range"])
        self.layout.addWidget(self.dropdown_sensitivity, 9, 0)
    def set_sample_points_textbox(self):
        # this is the sample_points_textbox
        self.textbox_sample_points = QLineEdit(self)
        self.layout.addWidget(self.textbox_sample_points, 7, 0)
    def set_optical_resolution_textbox(self):
        """"code to make the optical_resolution dropdown"""
        self.dropdown_optical_resolution = QComboBox(self)
        self.dropdown_optical_resolution.addItems(["0.01", "0.02", "0.05", "0.1", "0.2", "0.5", "1.0", "2.0", "5.0"])
        self.layout.addWidget(self.dropdown_optical_resolution, 5, 0)
    def set_end_wav_text_box(self):
        # this is the end_wav_textbox
        self.textbox_end_wav = QLineEdit(self)
        self.layout.addWidget(self.textbox_end_wav, 3, 0)
    def set_start_wav_textbox(self):
        # this is the start_wav_textbox
        self.textbox_start_wav = QLineEdit(self)
        self.layout.addWidget(self.textbox_start_wav, 1, 0)

    def get_chosen_optical_resolution(self):
        return self.dropdown_optical_resolution.currentText()
    def get_chosen_sensitivity(self):
        return self.dropdown_sensitivity.currentText()


    def on_click_recommended(self):
        """"when the recommend sample points button is clicked
        the textfield will be set empty and the recommend sample points will be calculated.
        using the formula: 1 + (2*(end_wav  - start_wav)/float(optical_resolution))
        """
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

    def on_click_submit(self):
        """"
        In this method there is a request to do a single sweep and plot the data.
        """
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
        print("starting")
        self.worker_thread.start()

    def plot_data(self):
        """
        Plot the data. On the x axis there is the wavelength and the y axis is the
        spectrometer data.
        """
        wav = self.instr.wav
        spec = self.instr.spec
        self.draw.random_plot.plot(wav, spec, clear=True)

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

class DrawSpectrum(QWidget):
    """
    In this class a widget is created to draw a graph on.
    """
    def __init__(self):
        super().__init__()
        self.title = 'Osa graph view'
        self.title = 'draw osa gui'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.random_plot = pg.PlotWidget()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        vbox.addWidget(self.random_plot)
        self.setLayout(vbox)
        self.show()

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = DrawSpectrum()
#     sys.exit(app.exec_())

if __name__ == '__main__':
    from hyperion import _logger_format, _logger_settings
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    

    with OsaInstrument(settings ={'dummy': True, 'controller':'hyperion.controller.osa.osa_controller/OsaController'}) as instr:
        draw = DrawSpectrum()
        instr.initialize()

        app = QApplication([])
        ex = OsaGui(instr, draw) # mandatory in order to call osainstrument in osa_view class
        ex.show()

        instr.finalize()
        sys.exit(app.exec_())
