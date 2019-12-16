"""
=============
Base for GUIS
=============

This file contains different base classes to make several types of guis.

'hyperion.view.BaseGui' is for building Qwidget guis.

'hyperion.view.BaseGraph' is for building Qwidget that contains creating a plot.


"""
import traceback
import logging
import sys
from hyperion import package_path
import pyqtgraph as pg
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from os import path
import yaml

class BaseGui(QWidget):
    """Base class to build a gui that can be loaded in the master gui.


    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # To avoid the crash when there is an error
        sys.excepthook = self.excepthook  # This is very handy in case there are exceptions that force the program to quit.

    def excepthook(self, etype, value, tb):
        """This is what it gets executed when there is an error. Here we build an
        error dialog box

        """
        self.logger.error('An error occurred. NameError: {} '.format(value))
        self.error_dialog(etype, value, tb)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.logger.debug('Exiting the with for the gui class')

    def error_dialog(self, etype, value, tb):
        """ Builds an error dialog box that pops up when there is an error. It shows the error in the details.
        It has two buttons: Ignore and Abort. Ignore continues and Abort closes

        """
        traceback.print_exception(etype, value, tb) # this prints the error in the terminal.
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)

        msg.setText("There was an error. \n Press Ignore or (x) to continue and Abort to exit the GUI.")
        msg.setWindowTitle("Error Box")
        text = ''
        for a in traceback.format_exception(etype, value, tb):
            text += '{}'.format(a)

        msg.setDetailedText("{}".format(text))
        msg.setStandardButtons(QMessageBox.Ignore | QMessageBox.Abort)
        msg.setDefaultButton(QMessageBox.Abort)
        msg.setEscapeButton(QMessageBox.Ignore)
        msg.buttonClicked.connect(self.error_dialog_btn)
        msg.exec_()

    def error_dialog_btn(self, i):
        """ Function that decides what to do when you press the buttons in the error dialog box.

        :param i: event when the QMessageBox buttons are pressed

        """
        self.logger.debug("Button pressed is: {}".format(i.text()))
        if i.text() == 'Abort':
            self.close() # to close the Qwidget


class BaseGraph(BaseGui):
    """
    In this class a widget is created to draw a graph on.
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating the BaseGraph ')
        self.title = 'BaseGraph Plot'
        self.left = 50
        self.top = 50
        self.width = 640
        self.height = 480
        self.plot_title = None

    def initialize_plot(self):
        """ This actually plots in the window. """
        if self.plot_title is None:
            self.plot_title = 'Title plot'
        # make the plot
        self.pg_plot_widget = pg.PlotWidget(title=self.plot_title)
        self.pg_plot = self.pg_plot_widget.plot([0],[0])

        # self.initUI()     # Removed this. It should be called by the child

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(path.join(package_path,'view','base_plot_windows_icon.png')))
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        vbox.addWidget(self.pg_plot_widget)
        self.setLayout(vbox)
        self.show()


class ModifyMeasurement(BaseGui):
    def __init__(self, experiment, measurement):
        self.experiment = experiment
        self.measurement = measurement
        self.original_list = self.experiment.properties['Measurements'][measurement]
        self.suggested_list, self.invalid_methods, self.invalid_names = self.experiment._validate_actionlist(self.original_list)
        super().__init__()

        self.initUI()
        self.show()

    def initUI(self):
        grid = QGridLayout()
        self.button_validate = QPushButton('validate')
        self.button_current = QPushButton('original')


        self.label_valid_1 = QLabel()
        self.label_valid_2 = QLabel()
        # self.button = QPushButton('original')
        # self.button_suggestion = QPushButton('suggestion')

        self.txt = QTextEdit()
        self.txt.setLineWrapMode(QTextEdit.NoWrap)
        # self.setLineWrapMode(QPlainTextEdit.NoWrap)
        font = QFont("Courier New")
        self.txt.setFont(font)
        doc = yaml.dump(self.original_list, indent=2)
        self.txt.setPlainText(doc)#.replace(r"\n", r"<br>") )
        self.resize(400, 700)

        grid.addWidget(self.button_validate, 0,0)
        grid.addWidget(self.button_current, 0,1)
        grid.addWidget(self.txt, 1, 0, 1, 2)
        grid.addWidget(self.label_valid_1, 2, 0)
        grid.addWidget(self.label_valid_1, 3, 0)
        self.setLayout(grid)


    # def toggle_txt(self, orig):
    #     if orig:
    #         self.txt.setText(self.original)
    #     else:





# class BaseMeasurement(BaseGui):
#     def __init__(self, experiment, measurement):
#         super().__init__():
#         if measurement in experiment.properties['Measurements']:
#             self.actionlist = experiment.properties['Measurements'][measurement]
#         if 'Defaults' in actionlist:
#             if 'folder' in self.actionlist['Defaults']:
#                 self.folder = self.actionlist['Defaults']['folder']
#             else:
#                 self.folder = os.path.join(package_path, 'data')
#
#     def validate(self):
#         new_action_list, self.invalid_methods, self.invalid_names = self.experiment._validate_actionlist(self.properties['Measurements'][measurement])
#
#
#     def initUI(self):
#         # default buttons:
#         # start, pause, stop, modify
#
#         button3 = modify
#         button1 = QPushButton('Start')
#         button2 = QPushButton('Break')
#
#
#         # before: start
#         # while running: pause, stop
#         # while paused: resume, stop
#         # while breaking: pause, [], stop




class SaverWidget(BaseGui):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        form_layout = QFormLayout()
        folder = QLineEdit()
        filename = QLineEdit()
        form_layout.addRow(QLabel('folder:'),folder)
        form_layout.addRow(QLabel('filename:'), filename)
        input_fields = QWidget()
        input_fields.setLayout(form_layout)

        grid_layout = QGridLayout()
        combo_version = QComboBox()
        # combo_version.addItems()
        but_open = QPushButton('Browse')
        but_open.clicked.connect(self.save_file_dialog)
        grid_layout.addWidget(input_fields, 0, 0)
        grid_layout.addWidget(but_open, 0, 1)

        self.setLayout(grid_layout)
        self.show()

    def save_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "HDF5 Files (*.h5);;All Files (*)", options=options)
        if fileName:
            print(fileName)



    # increment
    # fail
    # overwrite
    # append, increment
    # append, overwrite
    # append, fail

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sw = SaverWidget()
    app.exec_()
    # sys.exit(app.exec_())