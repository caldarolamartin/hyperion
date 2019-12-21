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

# class TestActionWidget(QGroupBox):
#     def __init__(self, experiment, actiondict):
#         self.logger = logging.getLogger(__name__)
#         super().__init__()
#         action_widget = QWidget()
#         self.layout = QVBoxLayout()
#         self.setLayout()
#
#
#     def init(self):
#
#         return

# class BaseActionGui(QGroupBox):
#     def __init__(self, experiment, actiondict, parent=None):
#         self.logger = logging.getLogger(__name__)
#         self.experiment = experiment
#         self.actiondict = actiondict
#         title = actiondict['Name']
#         super().__init__(title, parent)
#         self.layout = QVBoxLayout()
#         self.setContentsMargins(0, 9, 0, 0)
#         # self.layout.setContentsMargins(0,0,0,0)
#         # self.layout.setSpacing(5)
#         action_layout_or_widget = self.action_layout()
#
#         if '_ui' in actiondict
#
#         if action_layout is not None:
#             self.layout.addLayout(action_layout)
#         self.setLayout(self.layout)
#
#     def loadUI(self):
#
#
#     def action_layout_or_widget(self):
#         layout = QHBoxLayout()
#         layout.addWidget(QPushButton('button'))
#         layout.addWidget(QDoubleSpinBox())
#         placeholder = QWidget()
#         placeholder.setLayout(layout)
#         return placeholder

    # def init(self):
    #     self.logger.debug('This method should be overridden by child class')
    #
    # def initUI(self):
    #     self.logger.debug('This method should be overridden by child class')

# class EmptyActionGui(BaseActionGui):
#     def init()

# class ExampleActionGui(BaseActionGui):
#     def action_layout(self):


class BaseMeasurement(BaseGui):
    def __init__(self, experiment, measurement, parent=None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating BaseMeasurement object')
        super().__init__(parent)
        self.experiment = experiment
        self.measurement = measurement
        if not hasattr(self.experiment, 'properties'):
            self.logger.error('Experiment object needs to have properties dictionary. Make sure you load config.')
        if measurement in self.experiment.properties['Measurements']:
            self.actionlist = self.experiment.properties['Measurements'][measurement]
        else:
            self.logger.error('Unknown measurement: {}'.format(measurement))
            self.actionlist = []
        if 'ActionTypes' in self.experiment.properties:
            self.types = self.experiment.properties['ActionTypes']
        else:
            self.types = {}

        self.measurement_thread = WorkThread(experiment.dummy_measurement_for_testing_gui_buttons)

        self._valid = self.validate()
        self.outer_layout = QGridLayout()
        self.outer_layout.setSpacing(20)
        # self.outer_layout.setContentsMargins(0,0,0,0)

        self.button_layout = self.create_buttons()
        # buttons_placeholder = QWidget()
        # buttons_placeholder.setLayout(self.button_layout)
        # self.outer_layout.addWidget(buttons_placeholder, 0, 0)
        self.outer_layout.addLayout(self.button_layout, 0, 0)
        # action_layout = self.build_action_gui_list(self.actionlist)
        actions_layout = self.add_actions_recursively(self.actionlist)
        self.outer_layout.addLayout(actions_layout, 1, 0)
        self.setLayout(self.outer_layout)


        # if 'Defaults' in actionlist:
        #     if 'folder' in self.actionlist['Defaults']:
        #         self.folder = self.actionlist['Defaults']['folder']
        #     else:
        #         self.folder = os.path.join(package_path, 'data')

        self.dialog_config = ModifyMeasurement(self.experiment, self.measurement, self)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_buttons)
        self.timer.start(50) # in ms
        self.show()






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

    def __shift(self, level, maxlev=5):
        inverted = max(0, maxlev - level)
        shift = 0
        for s in range(inverted, maxlev):
            shift += s+2
        return inverted, shift

    def add_actions_recursively(self, actionlist, nesting_level=0):
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        # layout.setContentsMargins(18,3,0,3)
        # layout.setSpacing(15-min(nesting_level,3)*3)
        layout.setSpacing(5+self.__shift(nesting_level)[0])
        for act in actionlist:
            actiondict = ActionDict(act, self.types)
            box = QGroupBox(actiondict['Name'])
            # box.setObjectName("ColoredGroupBox")  # Changed here...
            # box.setStyleSheet("QGroupBox#ColoredGroupBox { border: 1px inset black; margin-top: 2ex} QGroupBox#ColoredGroupBox::title {subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #FFOECE, stop: 1 #FFFFFF);}")
            # box.setStyleSheet("QGroupBox#ColoredGroupBox { border: 1px inset black; margin-top: 2ex} QGroupBox#ColoredGroupBox::title {subcontrol-origin: margin; subcontrol-position: top left; padding: 3 3px;}")
            # QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #FFOECE, stop: 1 #FFFFFF);}

            # box.setStyleSheet(
            #     "QGroupBox#ColoredGroupBox {border-style: solid; border-width: 1px; border-color: black; text-align: left;} QGroupBox#ColoredGroupBox::title {left:10px; bottom : 0px;margin-top:8px;}")


            # box.setContentsMargins(0, 25, 0, 0)
            box.setCheckable(True)
            box_layout = QVBoxLayout()
            box_layout.setContentsMargins(0,5,0,0)
            box_layout.setSpacing(0)                    # distance between action widget and its nested items
            if '_view' in actiondict:
                action_gui_class = get_class(actiondict['_view'])
                action_gui_widget = action_gui_class(actiondict, self.experiment)
                action_gui_widget.layout.setContentsMargins(7,0,20-self.__shift(nesting_level)[1],10)
                # action_gui_widget.layout.setContentsMargins(0, 0, 0, 0)
                box_layout.addWidget(action_gui_widget)
            if '~nested' in actiondict:
                nested_layout = self.add_actions_recursively(actiondict['~nested'], nesting_level+1)
                # right = 5 if nesting_level<2 else 0
                nested_layout.setContentsMargins(max(3,12-nesting_level), 0, self.__shift(nesting_level)[0],5+max(0,5-nesting_level))
                box_layout.addLayout(nested_layout)
            if box_layout.count():
                box.setLayout(box_layout)
                layout.addWidget(box)
        return layout

    # def build_action_gui_list(self, actionlist):
    #     action_layout = QVBoxLayout()
    #     action_layout.setContentsMargins(5, 5, 5, 5)
    #     action_layout.setSpacing(5)
    #     action_layout.addLayout(self.button_layout)
    #     self.logger.debug('Creating action list')
    #     if self._valid:
    #         for act in self.actionlist:
    #             actiondict = ActionDict(act, self.types)
    #             action_widget = BaseActionGui(self.experiment, actiondict)
    #             if '_view' in actiondict:
    #                 action_widget = get_class(actiondict['_view'])(self.experiment, actiondict)
    #             elif 'Type' in actiondict:
    #                 tp = actiondict['Type']
    #                 if tp in self.experiment.properties['ActionTypes']:
    #                     type_dict = self.experiment.properties['ActionTypes'][tp]
    #                     if '_view' in type_dict:
    #                         action_widget = get_class(type_dict['_view'])(self.experiment, actiondict)
    #                 else:
    #                     self.logger.debug('ActionType {} not found for {}'.format(tp, actiondict['Name']))
    #
    #             # else:
    #             #     self.logger.debug('No gui found for action: {}'.format(actiondict['Name']))
    #             #     action_widget = QVBoxLayout
    #             # if '~nested' in actiondict:
    #             #     pass
    #             #     nested_layout = self.build_ui(actiondict['~nested'])
    #             #     if action_layout is None:
    #             #         action_layout = QGroupBox(actiondict['Name'])
    #             #         action_layout = setContentsMargins(0, 9, 0, 0)
    #             #         outer_layout.addLayout(action_layout)
    #             #
    #             #
    #             #         action_layout = QVBoxLayout()
    #             #         action_layout.setContentsMargins(0, 0, 0, 0)
    #             #         action_layout.setSpacing(0)
    #             #
    #             #     outer_layout.addWidget(action_widget)
    #             # else:
    #             if action_widget is not None:
    #                 action_layout.addWidget(action_widget)
    #
    #
    #     return action_layout

    def _add_actionbox(self, actiondict):
        pass

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