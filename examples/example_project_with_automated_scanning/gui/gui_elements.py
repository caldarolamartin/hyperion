from hyperion.core import logman
from hyperion.view.base_guis import BaseGui
from hyperion.tools.ui_tools import *
from hyperion import Q_

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QTimer
from PyQt5 import uic

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


class PowerMeterGui(BaseGui):
    def __init__(self, actiondict, experiment = None, parent = None):
        self.logger = logman.getLogger(__name__)
        self.logger.debug('Creating Power Meter Gui')
        super().__init__(parent)
        self.actiondict = actiondict
        self.experiment = experiment
        self.initUI()
        self.setLayout(self.layout)

    def initUI(self):
        self.layout = QHBoxLayout()  # outer layout needs to be called self.layout

        sensitivity_list = ['10uW', '100uW','1mW', '10mW', '100mW']
        sensitivity = QComboBox()
        sensitivity.addItems(sensitivity_list)

        integration_s = QDoubleSpinBox()
        integration_s.setSuffix(' s')

        self.layout.addWidget(QLabel('sens:'))
        self.layout.addWidget(sensitivity)
        self.layout.addWidget(QLabel('integr:'))
        self.layout.addWidget(integration_s)


class ImageWithFilters(BaseGui):
    def __init__(self, actiondict, experiment=None, parent=None):
        # Note that actiondict is of type ActionDict, which returns default values from the corresponding ActionType if
        # the value is not available in the Action itself and returns None if the key is not available at all.
        self.logger = logman.getLogger(__name__)
        self.logger.debug('Creating ImageWithFilters Gui')
        super().__init__(parent)
        self.actiondict = actiondict
        self.experiment = experiment
        self.initUI()
        self.setLayout(self.layout)

    def initUI(self):
        self.layout = QHBoxLayout()
        self.expo_value = QDoubleSpinBox()
        self.expo_value.valueChanged.connect(self.expo_changed)
        self.expo_units = QComboBox()
        self.expo_units.currentIndexChanged.connect(self.expo_changed)
        display_units = ['us', 'ms', 's', 'min', 'hr']
        self.expo_units.addItems(display_units)
        add_pint_to_combo(self.expo_units)
        if 'exposuretime' in self.actiondict:
            self.logger.debug('Applying config value to exposuretime in gui')
            pint_to_spin_combo(Q_(self.actiondict['exposuretime']), self.expo_value, self.expo_units)

        filter_a = QCheckBox('Filter A')
        filter_b = QCheckBox('Filter B')
        if 'filter_a' in self.actiondict:
            filter_a.setChecked(self.actiondict['filter_a'])
        if 'filter_b' in self.actiondict:
            filter_b.setChecked(self.actiondict['filter_b'])
        # Two ways of updating the dictionary when the checkbox is modified.
        # One readable way using a function. And one direct way without a function.
        filter_a.stateChanged.connect(self.set_filter_a)
        filter_b.stateChanged.connect(lambda state: self.actiondict.__setitem__('filter_b', state))

        self.layout.addWidget(self.expo_value)
        self.layout.addWidget(self.expo_units)
        self.layout.addWidget(filter_a)
        self.layout.addWidget(filter_b)

        # layout_filter = QVBoxLayout()
        # layout_filter.addWidget(filter_a)
        # layout_filter.addWidget(filter_b)
        # self.layout.addLayout(layout_filter)

        # placeholder = QWidget()
        # placeholder.setLayout(layout_filter)
        # self.layout.addWidget(placeholder)

    def expo_changed(self):
        self.actiondict['exposuretime'] = str(spin_combo_to_pint_apply_limits(self.expo_value, self.expo_units, Q_(self.actiondict['exposuretime_min']), Q_(self.actiondict['exposuretime_max'])))

    def set_filter_a(self, state):
        self.actiondict['filter_a'] = state


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

        positioner_units = ['nm', 'um', 'mm']

        self.start_value = QDoubleSpinBox()
        self.start_value.valueChanged.connect(self.start_changed)
        self.start_units = QComboBox()
        self.start_units.currentIndexChanged.connect(self.start_changed)
        self.start_units.addItems(positioner_units)
        add_pint_to_combo(self.start_units)
        if 'start' in self.actiondict:
            self.logger.debug('Applying config value to start in gui')
            pint_to_spin_combo(Q_(self.actiondict['start']), self.start_value, self.start_units)


        self.stop_value = QDoubleSpinBox()
        self.stop_value.valueChanged.connect(self.stop_changed)
        self.stop_units = QComboBox()
        self.stop_units.currentIndexChanged.connect(self.stop_changed)
        self.stop_units.addItems(positioner_units)
        add_pint_to_combo(self.stop_units)
        if 'stop' in self.actiondict:
            self.logger.debug('Applying config value to stop in gui')
            pint_to_spin_combo(Q_(self.actiondict['start']), self.start_value, self.start_units)

        self.step_value = QDoubleSpinBox()
        self.step_value.valueChanged.connect(self.step_changed)
        self.step_units = QComboBox()
        self.step_units.currentIndexChanged.connect(self.step_changed)
        self.step_units.addItems(positioner_units)
        add_pint_to_combo(self.step_units)
        if 'step' in self.actiondict:
            self.logger.debug('Applying config value to step in gui')
            pint_to_spin_combo(Q_(self.actiondict['start']), self.start_value, self.start_units)
        elif 'num' in in self.actiondict:
            self.logger.debug('Calculating step from num in config value and apply it to step in gui')
            pint_to_spin_combo((spin_combo_to_pint_apply_limits(self.stop_value, self.stop_units) - spin_combo_to_pint_apply_limits(self.start_value, self.start_units)) / (self.actiondict['num']-1), self.start_value, self.start_units)

        self.stop_um = QDoubleSpinBox()
        self.step_um = QDoubleSpinBox()
        self.layout.addWidget(QLabel('start:'))
        self.layout.addWidget(self.start_value)
        self.layout.addWidget(self.start_units)
        self.layout.addWidget(QLabel('stop:'))
        self.layout.addWidget(self.stop_value)
        self.layout.addWidget(self.stop_units)
        self.layout.addWidget(QLabel('step:'))
        self.layout.addWidget(self.step_value)
        self.layout.addWidget(self.step_units)

    def start_changed(self):
        print(type(self.actiondict))
        self.actiondict['start'] = str(
            spin_combo_to_pint_apply_limits(self.start_value, self.start_units, Q_(self.actiondict['start_min']),
                                            Q_(self.actiondict['start_max'])))

    def stop_changed(self):
        self.actiondict['start'] = str(
            spin_combo_to_pint_apply_limits(self.start_value, self.start_units, Q_(self.actiondict['start_min']),
                                            Q_(self.actiondict['start_max'])))

    def step_changed(self):
        self.actiondict['start'] = str(
            spin_combo_to_pint_apply_limits(self.start_value, self.start_units, Q_(self.actiondict['start_min']),
                                            Q_(self.actiondict['start_max'])))


if __name__=='__main__':
    app = QApplication([])
    example_action_dict = {'Name':'ExampleAction'}
    test = ExampleActionGui(example_action_dict)
    test.show()
    app.exec_()
