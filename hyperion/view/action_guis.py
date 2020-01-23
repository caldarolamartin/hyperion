"""
===========
Action GUIs
===========

This file contains little action gui widgets that can be used for the automated gui building (for automated scanning).

Typically a user would have their own file of action gui widgets.
This file contains a basic example and some common action guis.

"""
from hyperion.core import logman
from hyperion.view.base_guis import BaseGui
from hyperion.tools.ui_tools import *
from hyperion import Quan as Q_             # Note this is not the regular Q_
from hyperion import parent_path
from hyperion.tools.saving_tools import name_incrementer

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QTimer, Qt
from PyQt5 import uic
import os


class ExampleActionGui(BaseGui):
    def __init__(self, actiondict, experiment = None, parent = None):
        self.logger = logman.getLogger(__name__)
        self.logger.debug('Creating example action gui')
        super().__init__(parent)
        self.actiondict = actiondict
        self.experiment = experiment

        # # To load a ui file:
        # uic.loadUi(path_to_file, self)

        # # or maybe like this:
        # gui = QWidget()
        # uic.loadUi(path_to_file, gui)

        self.initUI()
        self.setLayout(self.layout)

    def initUI(self):
        # Create layout of your choice, but call it layout:
        self.layout = QHBoxLayout()

        # Create your gui elements and add them to the layout
        dsp = QDoubleSpinBox()
        cb = QComboBox()
        self.layout.addWidget(dsp)
        self.layout.addWidget(cb)

class ScanMicroPositioner(BaseGui):
    def __init__(self, actiondict, experiment = None, parent = None):
        self.logger = logman.getLogger(__name__)
        self.logger.debug('Creating ScanMicroPositioner gui')
        super().__init__(parent)
        self.actiondict = actiondict
        self.experiment = experiment

        # # To load a ui file:
        # uic.loadUi(path_to_file, self)

        # # or maybe like this:
        # gui = QWidget()
        # uic.loadUi(path_to_file, gui)

        self.initUI()
        self.setLayout(self.layout)

    def initUI(self):
        # Create layout of your choice:
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)

        right = Qt.AlignRight + Qt.AlignVCenter  # create shorthand for right Label alignment

        positioner_units = ['nm', 'um', 'mm']

        self.start_value = QDoubleSpinBox()
        self.start_units = QComboBox()
        self.start_units.addItems(positioner_units)
        add_pint_to_combo(self.start_units)
        if 'start' in self.actiondict:
            self.logger.debug('Applying config value to start in gui')
            pint_to_spin_combo(Q_(self.actiondict['start']), self.start_value, self.start_units)
        self.start_value.valueChanged.connect(self.start_changed)
        self.start_units.currentIndexChanged.connect(self.start_changed)

        self.stop_value = QDoubleSpinBox()
        self.stop_units = QComboBox()
        self.stop_units.addItems(positioner_units)
        add_pint_to_combo(self.stop_units)
        if 'stop' in self.actiondict:
            self.logger.debug('Applying config value to stop in gui')
            pint_to_spin_combo(Q_(self.actiondict['stop']), self.stop_value, self.stop_units)
        self.stop_value.valueChanged.connect(self.stop_changed)
        self.stop_units.currentIndexChanged.connect(self.stop_changed)

        self.step_value = QDoubleSpinBox()
        self.step_units = QComboBox()
        self.step_units.addItems(positioner_units)
        add_pint_to_combo(self.step_units)
        if 'step' in self.actiondict:
            self.logger.debug('Applying config value to step in gui')
            pint_to_spin_combo(Q_(self.actiondict['step']), self.step_value, self.step_units)
        elif 'num' in self.actiondict:
            self.logger.debug('Calculating step from num in config value and apply it to step in gui')
            step = ( spin_combo_to_pint_apply_limits(self.stop_value, self.stop_units) -
                                  spin_combo_to_pint_apply_limits(self.start_value, self.start_units)  ) / (self.actiondict['num']-1)
            self.actiondict['step'] = str(step)
            pint_to_spin_combo( step, self.step_value, self.step_units)
        self.step_value.valueChanged.connect(self.step_changed)
        self.step_units.currentIndexChanged.connect(self.step_changed)


        self.stop_um = QDoubleSpinBox()
        self.step_um = QDoubleSpinBox()
        self.layout.addWidget(QWidget())  # adding this empty widget helps with aligning the layout in a prettier way
        self.layout.addWidget(QLabel('start', alignment=right))
        self.layout.addWidget(self.start_value)
        self.layout.addWidget(self.start_units)
        self.layout.addWidget(QLabel('  stop', alignment=right))
        self.layout.addWidget(self.stop_value)
        self.layout.addWidget(self.stop_units)
        self.layout.addWidget(QLabel('  step', alignment=right))
        self.layout.addWidget(self.step_value)
        self.layout.addWidget(self.step_units)

    def start_changed(self):
        self.actiondict['start'] = str(
            spin_combo_to_pint_apply_limits(self.start_value, self.start_units, Q_(self.actiondict['start_min']),
                                            Q_(self.actiondict['start_max'])))

    def stop_changed(self):
        self.actiondict['stop'] = str(
            spin_combo_to_pint_apply_limits(self.stop_value, self.stop_units, Q_(self.actiondict['stop_min']),
                                            Q_(self.actiondict['stop_max'])))

    def step_changed(self):
        self.actiondict['step'] = str(
            spin_combo_to_pint_apply_limits(self.step_value, self.step_units, Q_(self.actiondict['step_min']),
                                            Q_(self.actiondict['step_max'])))


class SaverGui(BaseGui):
    def __init__(self, actiondict, experiment = None, parent = None):
        self.logger = logman.getLogger(__name__)
        self.logger.debug('Creating saver gui')
        super().__init__(parent)
        self.actiondict = actiondict
        self.experiment = experiment

        # Add incrementer method to experiment so that it can call the incrementer after a measurement finished.
        # This is not strictly necessary (the experiment class will increment by itself if auto_increment is set),
        # but it's nices for the user if the name updates.
        self.experiment._saver_gui_incremeter = self.apply_incrementer

        # # To load a ui file:
        # uic.loadUi(path_to_file, self)

        # # or maybe like this:
        # gui = QWidget()
        # uic.loadUi(path_to_file, gui)

        self.initUI()
        self.setLayout(self.layout)

    def initUI(self):
        # Create layout of your choice, but call it layout:
        self.layout = QGridLayout()

        # gui elements
        folder, basename = self.experiment._validate_folder_basename(self.actiondict)
        self.folder_line = QLineEdit(folder)
        self.file_line = QLineEdit(basename)
        self.browse_butn = QPushButton('Browse')
        self.check_store_prop = QCheckBox('store properties', checked=bool(self.actiondict['store_properties']))
        self.check_auto_incr = QCheckBox('auto-increment', checked=bool(self.actiondict['auto_increment']))
        self.comment_line = QLineEdit()
        if self.actiondict['auto_increment']:
            self.apply_incrementer()

        # Positioning them in the widget:
        right = Qt.AlignRight + Qt.AlignVCenter  # create shorthand for right Label alignment
        self.layout.addWidget(QLabel('folder', alignment=right), 0, 0)
        self.layout.addWidget(self.folder_line, 0, 1, 1, 2)

        self.layout.addWidget(QLabel('file', alignment=right), 1, 0)
        self.layout.addWidget(self.file_line, 1, 1)
        self.layout.addWidget(self.browse_butn, 1, 2)

        self.layout.addWidget(QLabel(''), 0, 3)
        self.layout.addWidget(self.check_store_prop, 0, 4)
        self.layout.addWidget(self.check_auto_incr, 1, 4)

        self.layout.addWidget(QLabel('comment', alignment=right), 2, 0)
        self.layout.addWidget(self.comment_line, 2, 1, 1, 4)

        # connecting active elements to methods (or directly to dictionary):
        self.browse_butn.clicked.connect(self.browse)
        self.folder_line.editingFinished.connect(lambda: self.line_updated(self.folder_line, 'folder'))
        self.file_line.editingFinished.connect(lambda: self.line_updated(self.file_line, 'basename'))
        self.comment_line.editingFinished.connect(lambda: self.line_updated(self.comment_line, 'comment'))
        self.check_auto_incr.stateChanged.connect(self.incr_checked)
        self.check_store_prop.stateChanged.connect(lambda state: self.actiondict.__setitem__('store_properties', state))

    def incr_checked(self, state):
        self.actiondict['auto_increment'] = state
        if state:
            self.apply_incrementer()

    def line_updated(self, obj, key):
        self.actiondict[key] = obj.text()
        if key=='basename' or key=='folder':
            self.apply_incrementer()

    def apply_incrementer(self):
        """ Updates both actiondict and the QLineEdit"""
        if self.actiondict['auto_increment'] and os.path.isdir(self.actiondict['folder']):
            existing_files = os.listdir(self.actiondict['folder'])
            basename = name_incrementer(self.actiondict['basename'], existing_files)
            self.actiondict['basename'] = basename
            self.file_line.setText(basename)

    def browse(self):
        folder, basename = self.experiment._validate_folder_basename(self.actiondict)
        fname = QFileDialog.getSaveFileName(self, 'Save data as', os.path.join(folder, basename), filter="netCDF4 (*.nc);;All Files (*.*)")
        # If cancel was pressed, don't change the folder and file
        if fname[0] == '':
            return
        folder, basename = os.path.split(fname[0])
        self.actiondict['folder'] = folder
        self.actiondict['basename'] = basename
        self.folder_line.setText(folder)
        self.file_line.setText(basename)
        self.apply_incrementer()
