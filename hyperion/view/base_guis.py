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
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import QTimer
from os import path
import yaml
from hyperion.view.general_worker import WorkThread
from hyperion.tools.loading import get_class
from hyperion.experiment.base_experiment import ActionDict
from PyQt5 import uic


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

    def deleteItemsOfLayout(self, layout):
        """
        Removes items of a layout recursively .
        :param layout: a QLayout
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.deleteItemsOfLayout(item.layout())

    def close_children_guis(self):
        pass


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
    """
    Pop-up dialog window to modify (correct) the action-list of a measurement.
    Using the _validate_actionlist method of BaseExperiment it checks for missing Names and for
    missing/incorrect _methods and indicates if the actionlist is valid or not.
    Missing or incorrect _methods have to be fixed by the user.
    (Note that Actions may refer to a Type that holds default values, possibly including _method).
    In case of Missing Names, a suggestion is generated.
    The Use button allows the user to store the modified/corrected actionlist in the properties dictionary of the
    experiment and apply it to the GUI.

    Notes:

    - QDialog steals focus and must be closed before main program can continue.
    - The methods of this class are not intended to be called from outside this class

    :param experiment: hyperion experiment object
    :param measurement: (str) name of a measurement (specified in the config of the experiment)
    :param parent: parent QWidget
    """
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
        self._current_doc = 1           # 1 for original, -1 for modified, 0 for suggestion
        self._modified = False
        self._valid = False             # None for unknown, True, False
        self._have_suggestion = False   # True, False
        self._invalid_methods = True
        self.font = QFont("Courier New", 11)

        self.initUI()
        self.reset()        # initialize to original
        self.set_size()     # Make window fix text when openning (if possible)


    def initUI(self):
        # Allow window to be shrunk and expanded:
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid = QGridLayout()
        # create buttons, lables and the textedit:
        self.button_reset = QPushButton('Reset Original', clicked = self.reset)
        self.button_validate = QPushButton('Validate', clicked = self.validate)
        self.button_suggestion = QPushButton('Show suggestion', clicked = self.suggestion)
        self.button_use = QPushButton('Use', clicked = self.use)
        self.button_cancel = QPushButton('Cancel', clicked = self.close)
        self.button_save_to_original_file = QPushButton('Save to original file', enabled = False)
        self.label_valid_1 = QLabel()  # empty
        self.label_valid_2 = QLabel()  # empty
        self.txt = QTextEdit()
        self.txt.setLineWrapMode(QTextEdit.NoWrap)
        self.txt.setFont(self.font)
        self.txt.textChanged.connect(self.changed)
        # add all widgets to the layout:
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

    def reset(self):
        # Update text, validate, and update buttons accordingly
        self._doc = yaml.dump(self._original_list, indent=self._indent)
        self.txt.setPlainText(self._doc)
        self.clear_labels()
        self.validate()
        self._current_doc = 1
        self.update_buttons()

    def set_size(self):
        # Adjust window size to text (if possible)
        # These values were chosen in Windows 7
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        font_metrics = QFontMetrics(self.font)
        max_width = min(QDesktopWidget().availableGeometry(self).width(), QDesktopWidget().screenGeometry(self).width())
        max_height = min(QDesktopWidget().availableGeometry(self).height(), QDesktopWidget().screenGeometry(self).height())
        width = max(400, min(max_width-16, self.txt.document().idealWidth() + 42+10))
        height = max(400, min(max_height-38, font_metrics.size(0, self._doc).height() + 145))
        self.resize(width, height)

    def update_buttons(self):
        # Update status of buttons
        self.button_reset.setEnabled(self._current_doc<1)
        self.button_validate.setEnabled(not self._valid and self._current_doc and self._modified)
        self.button_suggestion.setEnabled(self._have_suggestion and self._current_doc)
        self.button_use.setEnabled(self._valid == True)

    def use(self):
        # Store the corrected actionlist in experiment and updates _valid=True in parent (ifa available)
        self.logger.debug('"Use" pressed')
        if not self.convert_text_to_list():
            self.logger.warning('Failed to convert yaml-text to list')
            return
        self.experiment.properties['Measurements'][self.measurement] = self._list
        if hasattr(self.parent, '_valid'):
            self.parent._valid = True
        if hasattr(self.parent, 'update_buttons'):
            self.parent.update_buttons()
        self.close()

    def clear_labels(self):
        # Clear the two labels under the textedit field
        self.label_valid_1.setText('')
        self.label_valid_2.setText('')
        self.label_valid_1.setStyleSheet('color: black')

    def changed(self):
        # Called when the text in the textedt is modified. Will call update buttons.
        self.clear_labels()
        self._current_doc = -1
        self._modified = True
        self._have_suggestion = False
        self._valid = False
        self.update_buttons()

    def convert_text_to_list(self):
        # Converts the text in the textedit to a list
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
        # Uses experiment._validate_actionlist() to validate the current text. Sets _valid flag and updates buttons.
        # Updates the labels under the textedit field.
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
        # Set the method label
        self.label_valid_1.setText('{} invalid _method{}'.format(self._invalid_methods, self.plural(self._invalid_methods)))
        if self._invalid_methods:
            self.label_valid_1.setStyleSheet('color: red')

    def suggestion(self):
        # Show the suggestion that was generated by experiment._validate_actionlist()
        self._doc = yaml.dump(self._suggested_list, indent=self._indent)
        self.txt.setPlainText(self._doc)
        self.set_label_invalid()
        self.label_valid_2.setText('{} Name{} modified'.format(self._invalid_names, self.plural(self._invalid_names)))
        self._current_doc = 0
        self._valid = True
        self.update_buttons()


class BaseMeasurementGui(BaseGui):
    """
    Builds a Meaasurement GUI based on the Measurement actionlist in experiment.properties (which is read from the
    config file). The GUI will follow the nested structure in the actionlist.
    Note that the Actions in the actionlist need to refer to an appropriate GUI file and Widget and to an appropriate
    method in the experiment (which should contain nested() if nesting is to be possible).
    I also builds the Start/Pause, Break and Stop buttons that

    :param experiment: hyperion experiment object
    :param measurement: (str) name of a measurement (specified in the config of the experiment)
    :param parent: parent QWidget
    """
    def __init__(self, experiment, measurement, parent=None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating BaseMeasurement object')
        super().__init__(parent)
        self.experiment = experiment
        self.measurement = measurement
        if not hasattr(self.experiment, 'properties'):
            self.logger.error('Experiment object needs to have properties dictionary. Make sure you load config.')
        if measurement not in self.experiment.properties['Measurements']:
            self.logger.error('Unknown measurement: {}'.format(measurement))

        if 'ActionTypes' in self.experiment.properties:
            self.types = self.experiment.properties['ActionTypes']
        else:
            self.types = {}

        # self.measurement_thread = WorkThread(experiment.dummy_measurement_for_testing_gui_buttons)
        self.measurement_thread = WorkThread(lambda: experiment.perform_measurement(self.measurement))

        self._valid = self.validate()
        self.outer_layout = QGridLayout()
        self.outer_layout.setSpacing(20)
        self.button_layout = self.create_buttons()
        self.outer_layout.addLayout(self.button_layout, 0, 0)
        self.actions_layout = QVBoxLayout()
        label_incorrect = QLabel('incorrect config file')
        label_incorrect.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.actions_layout.addWidget(label_incorrect)
        self.create_actionlist_guis()
        # This line controls the size of the whole layout.
        # .SetDefaultConstraint causes it to adjust to the content size, but keeps it adjustable
        # .SetFixedSize adjust to the content and prevents manual resizing
        self.outer_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(self.outer_layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.show()
        # Prepare window to modify config:
        self.dialog_config = ModifyMeasurement(self.experiment, self.measurement, self)
        # Set up QTimer to periodically update button states (based on
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_buttons)
        self.timer.start(50) # in ms

    def create_buttons(self):
        """
        Create Start/Pause, Break, Stop and Config Button. And link to appropriate methods.
        :return: layout containing buttons
        """
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

    def create_actionlist_guis(self):
        """
        Creates and updates the the (nested) measurement GUI.
        """
        self.deleteItemsOfLayout(self.actions_layout)
        if self._valid:
            self.actions_layout = self.add_actions_recursively(self.experiment.properties['Measurements'][self.measurement])
        else:
            self.actions_layout = QVBoxLayout()
            self.actions_layout.addWidget(QLabel('incorrect config file'))
        self.outer_layout.addLayout(self.actions_layout, 1, 0)
        self.update()

    def add_actions_recursively(self, actionlist, nesting_level=0):
        """
        Recursive function to build nested layout of action GUIs.

        :param actionlist: (list)
        :param nesting_level: (int) Used for recursion (use default when calling method)
        :return: layout containing the nested GUIs
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5+self.__shift(nesting_level)[0])
        for act in actionlist:
            actiondict = ActionDict(act, self.types)
            box = QGroupBox(actiondict['Name'])
            box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            box.setCheckable(True)   # This adds the checkbox in the top-left corner
            box_layout = QVBoxLayout()
            box_layout.setContentsMargins(0,5,0,0)
            box_layout.setSpacing(0)                    # distance between action widget and its nested items
            if '_view' in actiondict:
                action_gui_class = get_class(actiondict['_view'])
                action_gui_widget = action_gui_class(actiondict, self.experiment)
                action_gui_widget.layout.setContentsMargins(7,0,20-self.__shift(nesting_level)[1],10)
                action_gui_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                box_layout.addWidget(action_gui_widget)
            if '~nested' in actiondict:
                nested_layout = self.add_actions_recursively(actiondict['~nested'], nesting_level+1)
                nested_layout.setContentsMargins(max(3,12-nesting_level), 0, self.__shift(nesting_level)[0],5+max(0,5-nesting_level))
                box_layout.addLayout(nested_layout)
            if box_layout.count():
                box.setLayout(box_layout)
                layout.addWidget(box)
        return layout

    def __shift(self, level, maxlev=5):
        # Helper function to calculating border widths for aligning nested layout in add_actions_recursively().
        # Returns tuple
        inverted = max(0, maxlev - level)
        shift = 0
        for s in range(inverted, maxlev):
            shift += s+2
        return inverted, shift

    def start_pause(self):
        """
        Called when Start/Pause/Continue button is pressed.
        Starts a measurement thread or communicates to experiment through the Measurement status flags that a
        measurement should be paused or continued.
        """
        self.logger.debug('start/pause pressed')
        self.experiment.apply_pause = not self.experiment.apply_pause
        if self.experiment.running_status == self.experiment._not_running:
            self.measurement_thread.start()
        self.update_buttons()

    def apply_break(self):
        """
        Called when Break button is pressed.
        Communicates to experiment through the Measurement status flags that a measurement break ("soft stop") should be
        applied.
        """
        self.logger.debug('break pressed')
        self.experiment.apply_break = True
        self.update_buttons()

    def apply_stop(self):
        """
        Called when Stop button is pressed.
        Communicates to experiment through the Measurement status flags that a measurement should be stopped (immediately).
        """
        self.logger.debug('stop pressed')
        self.experiment.apply_stop = True
        self.update_buttons()

    def config(self):
        """
        Called when Config button is pressed.
        Opens the ModifyMeasurement Dialog to modify/correct the config text directly.
        """
        self.dialog_config.exec_()
        self.update_buttons()
        self.create_actionlist_guis()
        self.update()

    def update_buttons(self):
        """
        Updates the status of the start/pause/continue, break, stop buttons.
        """
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
            if self.experiment.apply_break:
                self.button_break.setText('Breaking')
            else:
                self.button_break.setText('Break')
            self.button_start_pause.setEnabled(self.experiment.running_status < self.experiment._breaking)
            self.button_break.setEnabled(self.experiment._not_running < self.experiment.running_status < self.experiment._breaking)
            self.button_stop.setEnabled(self.experiment._not_running < self.experiment.running_status < self.experiment._stopping)
            self.button_config.setEnabled(self.experiment.running_status == self.experiment._not_running)

    def validate(self):
        """
        Uses self.experiment._validate_actionlist() to determine if the current actionlist in experiment.properties is
        valid.
        :return: (boolean) True if valid
        """
        new_action_list, invalid_methods, invalid_names = self.experiment._validate_actionlist(self.experiment.properties['Measurements'][self.measurement])
        return (invalid_methods==0 and invalid_names==0)


# This saver widget is a rudimentary start and is not used at the moment:
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