"""
=============
Base for GUIS
=============

This file contains different base classes to make several types of guis.

'hyperion.view.BaseGui' is for building Qwidget guis.

'hyperion.view.BaseGraph' is for building Qwidget that contains creating a plot.


"""
import traceback
from hyperion import logging
import sys
from hyperion import package_path
import pyqtgraph as pg
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QTimer
from os import path
import yaml
from hyperion.view.general_worker import WorkThread
from hyperion.tools.loading import get_class

class BaseGui(QWidget):
    """Base class to build a gui that can be loaded in the master gui.


    """
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.initialize_plot()
        vbox.addWidget(self.pg_plot_widget)
        self.setLayout(vbox)
        self.show()

class TimeAxisItem(pg.AxisItem):
    """This code I found on the internet to change things of the axes, for instance the color or the size of the numbers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def attachToPlotItem(self, plotItem):
        """Add this axis to the given PlotItem
        :param plotItem: (PlotItem)
        """
        self.setParentItem(plotItem)
        viewBox = plotItem.getViewBox()
        self.linkToView(viewBox)
        self._oldAxis = plotItem.axes[self.orientation]['item']
        self._oldAxis.hide()
        plotItem.axes[self.orientation]['item'] = self
        pos = plotItem.axes[self.orientation]['pos']
        plotItem.layout.addItem(self, *pos)
        self.setZValue(-1000)


class ModifyMeasurement(QDialog):
    def __init__(self, experiment, measurement, parent=None):
        self.logger = logging.getLogger(__name__)
        self.experiment = experiment
        self.measurement = measurement
        self.parent = parent
        self._original_list = self.experiment.properties['Measurements'][measurement]
        super().__init__(parent)
        self.setWindowTitle('Modify Measurement: {}'.format(measurement))
        self._indent = 2
        self.plural = lambda num: 's' if num > 1 else ''
        self._current_doc = 1 # 1 for original, -1 for modified, 0 for suggestion
        self._modified = False
        self._valid = False   # None for unknown, True, False
        self._have_suggestion = False  # True, False
        self._invalid_methods = True
        self.initUI()
        self.reset()    # initialize to original

        # self.show()

    def initUI(self):
        grid = QGridLayout()
        self.button_reset = QPushButton('Reset Original', clicked = self.reset)
        self.button_validate = QPushButton('Validate', clicked = self.validate)
        self.button_suggestion = QPushButton('Show suggestion', clicked = self.suggestion)
        self.button_use = QPushButton('Use', clicked = self.use)
        self.button_cancel = QPushButton('Cancel', clicked = self.close)
        self.button_save_to_original_file = QPushButton('Save to original file', enabled = False)

        self.label_valid_1 = QLabel()
        self.label_valid_2 = QLabel()
        # self.button = QPushButton('original')
        # self.button_suggestion = QPushButton('suggestion')


        self.txt = QTextEdit()
        self.txt.setLineWrapMode(QTextEdit.NoWrap)
        self.txt.setFont(QFont("Courier New", 11))
        self.txt.textChanged.connect(self.changed)
        # self.txt.setPlainText(self._doc)

        grid.addWidget(self.button_reset, 0, 0)
        grid.addWidget(self.button_validate, 0, 1)
        grid.addWidget(self.button_suggestion, 0, 2)
        grid.addWidget(self.txt, 1, 0, 1, 3)
        grid.addWidget(self.label_valid_1, 2, 0)
        grid.addWidget(self.label_valid_2, 3, 0)
        grid.addWidget(self.button_use, 4, 0)
        grid.addWidget(self.button_cancel, 4, 1)
        grid.addWidget(self.button_save_to_original_file, 4, 2)
        self.setLayout(grid)

        self.resize(500, 900)
        self.center()

    def update_buttons(self):
        self.button_reset.setEnabled(self._current_doc<1)
        self.button_validate.setEnabled(not self._valid and self._current_doc and self._modified)
        self.button_suggestion.setEnabled(self._have_suggestion and self._current_doc)
        self.button_use.setEnabled(self._valid == True)


    def use(self):
        if not self.convert_text_to_list():
            return
        self.experiment.properties['Measurements'][self.measurement] = self._list
        if hasattr(self.parent, '_valid'):
            self.parent._valid = True
        if hasattr(self.parent, 'update_buttons'):
            self.parent.update_buttons()
        self.close()

    def clear_labels(self):
        self.label_valid_1.setText('')
        self.label_valid_2.setText('')
        self.label_valid_1.setStyleSheet('color: black')

    def changed(self):
        self.clear_labels()
        self._current_doc = -1
        self._modified = True
        self._have_suggestion = False
        self._valid = False
        self.update_buttons()

    def reset(self):
        self._doc = yaml.dump(self._original_list, indent=self._indent)
        self.txt.setPlainText(self._doc)
        self.clear_labels()
        self.validate()
        self._current_doc = 1
        self.update_buttons()

    def convert_text_to_list(self):
        self._doc = self.txt.toPlainText()
        try:
            self._list = yaml.safe_load(self._doc)
            return True
        except yaml.YAMLError as exc:
            lines = [k.line for k in exc.args if type(k) is yaml.error.Mark]
            self.label_valid_1.setText('Invalid yaml. Issues in lines: '+str(lines)[1:-1])
            self.label_valid_1.setStyleSheet('color: red')
            self._valid = False
            self._modified = False
            return False

    def validate(self):
        if not self.convert_text_to_list():
            self.update_buttons()
            return
        self._suggested_list, self._invalid_methods, self._invalid_names = self.experiment._validate_actionlist(self._list)
        self._valid = self._invalid_methods==0 and self._invalid_names==0
        if self._valid:
            self.label_valid_1.setText('Valid !')
            self.label_valid_1.setStyleSheet('color: black')
        else:
            self.set_label_invalid()
            self.label_valid_2.setText('{} invalid Name{}'.format(self._invalid_names, self.plural(self._invalid_names)))
            if not self._invalid_methods:
                self._have_suggestion = True
        self._modified = False
        self.update_buttons()


    def set_label_invalid(self):
        self.label_valid_1.setText('{} invalid _method{}'.format(self._invalid_methods, self.plural(self._invalid_methods)))
        if self._invalid_methods:
            self.label_valid_1.setStyleSheet('color: red')

    def suggestion(self):
        self._doc = yaml.dump(self._suggested_list, indent=self._indent)
        self.txt.setPlainText(self._doc)
        self.set_label_invalid()
        self.label_valid_2.setText('{} Name{} modified'.format(self._invalid_names, self.plural(self._invalid_names)))
        self._current_doc = 0
        self._valid = True
        self.update_buttons()

    def center(self):
        frameGm = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

class BaseActionGui(BaseGui):
    def __init__(self, experiment, actiondict):
        self.logger = logging.getLogger(__name__)
        super().__init__()
        self.init()
        self.experiment = experiment
        self.actiondict = actiondict
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0,0,0,0)
        outer_layout.setSpacing(0)
        self.box = QGroupBox(actiondict['Name'])
        self.box.setContentsMargins(0, 9, 0, 0)
        self.initUI()
        outer_layout.addWidget(self.box)
        self.setLayout(outer_layout)

    def init(self):
        self.logger.debug('This method should be overridden by child class')

    def initUI(self):
        self.logger.debug('This method should be overridden by child class')

class EmptyActionGui(BaseActionGui):
    def init()

class BaseMeasurement(BaseGui):
    def __init__(self, experiment, measurement, parent=None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating BaseMeasurement object')
        super().__init__(parent)
        self.experiment = experiment
        self.measurement = measurement
        if measurement in self.experiment.properties['Measurements']:
            self.actionlist = self.experiment.properties['Measurements'][measurement]
        else:
            self.logger.error('Unknown measurement: {}'.format(measurement))
            self.actionlist = []

        self.measurement_thread = WorkThread(experiment.dummy_measurement_for_testing_gui_buttons)


        self._valid = self.validate()
        self.button_layout =  self.create_buttons()
        self.build_ui()

        # if 'Defaults' in actionlist:
        #     if 'folder' in self.actionlist['Defaults']:
        #         self.folder = self.actionlist['Defaults']['folder']
        #     else:
        #         self.folder = os.path.join(package_path, 'data')

        self.dialog_config = ModifyMeasurement(self.experiment, self.measurement, self)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_buttons)
        self.timer.start(50) # in ms

    def create_buttons(self):
        self.logger.debug('Creating start stop buttons')
        layout_buttons = QHBoxLayout()
        self.button_start_pause = QPushButton('Start', clicked = self.start_pause)
        self.button_break = QPushButton('Break', clicked = self.apply_break)
        self.button_stop = QPushButton('Stop', clicked = self.apply_stop)
        self.button_config = QPushButton('Config', clicked = self.config)
        layout_buttons.addWidget(self.button_start_pause)
        layout_buttons.addWidget(self.button_break)
        layout_buttons.addWidget(self.button_stop)
        layout_buttons.addWidget(self.button_config)
        return layout_buttons

    def build_ui(self, actionlist):
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(5, 5, 5, 5)
        outer_layout.setSpacing(5)
        outer_layout.addLayout(self.button_layout)
        self.logger.debug('Creating action list')
        action_layout = None
        if self._valid:
            for actiondict in self.actionlist:
                if '_view' in actiondict:
                    action_layout = get_class(actiondict['_view'])(self.experiment, actiondict)
                elif 'Type' in actiondict:
                    tp = actiondict['Type']
                    if tp in self.experiment.properties['ActionTypes']:
                        type_dict = self.experiment.properties['ActionTypes'][tp]
                        if '_view' in type_dict:
                            action_layout = get_class(type_dict['_view'])(self.experiment, actiondict)
                    else:
                        self.logger.debug('ActionType {} not found for {}'.format(tp, actiondict['Name']))
                else:
                    self.logger.debug('No gui found for action: {}'.format(actiondict['Name']))
                    action_layout = QVBoxLayout
                if '~nested' in actiondict:
                    nested_layout = self.build_ui(actiondict['~nested'])
                    if action_layout is None:
                        action_layout = QGroupBox(actiondict['Name'])
                        action_layout = setContentsMargins(0, 9, 0, 0)
                        outer_layout.


                        action_layout = QVBoxLayout()
                        action_layout.setContentsMargins(0, 0, 0, 0)
                        action_layout.setSpacing(0)

                    outer_layout.addWidget(action_widget)
        return outer_layout

    def _add_actionbox(self, actiondict):


    def start_pause(self):
        self.logger.debug('start/pause pressed')
        self.experiment.apply_pause = not self.experiment.apply_pause
        if self.experiment.running_status == self.experiment._not_running:
            self.measurement_thread.start()
        self.update_buttons()

    def apply_break(self):
        self.logger.debug('break pressed')
        self.experiment.apply_break = True
        self.update_buttons()

    def apply_stop(self):
        self.logger.debug('stop pressed')
        self.experiment.apply_stop = True
        self.update_buttons()

    def config(self):
        self.dialog_config.show()
        self.update_buttons()




    def update_buttons(self):

        # note that:
        # experiment._not_running = 0
        # experiment._running =     1
        # experiment._pausing =     2
        # experiment._breaking =    3
        # experiment._stopping =    4
        if not self._valid:
            self.button_start_pause.setEnabled(False)
            self.button_break.setEnabled(False)
            self.button_stop.setEnabled(False)
            self.button_config.setEnabled(True)
            return
        else:
            if self.experiment.running_status == self.experiment._not_running:
                self.button_start_pause.setText('Start')
            elif self.experiment.apply_pause:
                self.button_start_pause.setText('Continue')
            else:
                self.button_start_pause.setText('Pause')
            self.button_start_pause.setEnabled(self.experiment.running_status < self.experiment._breaking)
            self.button_break.setEnabled(self.experiment._not_running < self.experiment.running_status < self.experiment._breaking)
            self.button_stop.setEnabled(self.experiment._not_running < self.experiment.running_status < self.experiment._stopping)
            self.button_config.setEnabled(self.experiment.running_status == self.experiment._not_running)


    def validate(self):
        new_action_list, invalid_methods, invalid_names = self.experiment._validate_actionlist(self.experiment.properties['Measurements'][self.measurement])
        return (invalid_methods==0 and invalid_names==0)




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