from hyperion.core import logman
from hyperion.view.base_guis import BaseGui
from hyperion.tools.ui_tools import *
from hyperion import Quan as Q_             # Note this is not the regular Q_

from PyQt5.QtWidgets import *


class SpectrumGUI(BaseGui):
    """| This class creates a Gui with all the things that you usually change when taking a Spectrum:
    | - exposuretime
    | - grating
    | - central wavelength to put grating to
    | - ROI to integrate over
    """
    def __init__(self, actiondict, experiment=None, parent=None):
        self.logger = logman.getLogger(__name__)
        self.logger.debug('Creating SpectrumWithFilters Gui')
        super().__init__(parent)
        self.actiondict = actiondict
        self.experiment = experiment
        self.last_row = 0

        self.initUI()
        self.setLayout(self.layout)

    def initUI(self):
        self.layout = QGridLayout()

        self.make_fields()
        self.roi_fields()
        self.place_in_grid()

    def make_fields(self):
        """| In this method, the possible user input spinboxes and comboboxes are made.
        | For the exposure time, the value and unit are combined with Arons add_pint_to_combo methods.
        | The gratings are numbered and added.
        | The central wavelength is a spinbox and the suffix nm is always added.
        """
        self.expo_value = QDoubleSpinBox()
        self.expo_value.setMaximum(99999)
        self.expo_units = QComboBox()
        display_units = ['us', 'ms', 's', 'min', 'hr']
        self.expo_units.addItems(display_units)
        add_pint_to_combo(self.expo_units)
        if 'exposuretime' in self.actiondict and self.actiondict['exposuretime'] is not None:
            self.logger.debug('Applying config value to exposuretime in gui')
            pint_to_spin_combo(Q_(self.actiondict['exposuretime']), self.expo_value, self.expo_units)
        # After setting initial values, connect changes to the function that tries to apply them:
        self.expo_value.valueChanged.connect(self.expo_changed)
        self.expo_units.currentIndexChanged.connect(self.expo_changed)

        self.grating = QComboBox()
        possible_gratings = ['1','2','3']
        self.grating.addItems(possible_gratings)

        if 'grating' in self.actiondict and self.actiondict['grating'] is not None:
            self.logger.debug('Choosing grating as in config file')
            self.grating.setCurrentText(str(self.actiondict['grating']))
        self.grating.currentIndexChanged.connect(self.grating_changed)

        self.central_nm = QDoubleSpinBox()
        self.central_nm.setMaximum(2000)
        if 'central_nm' in self.actiondict and self.actiondict['central_nm'] is not None:
            self.logger.debug('Putting the central wavelength in gui')
            self.central_nm.setValue(self.actiondict['central_nm'])
            self.central_nm.setSuffix('nm')
        self.central_nm.valueChanged.connect(self.central_nm_changed)

        if 'accumulations' in self.actiondict and self.actiondict['accumulations'] is not None:
            self.accumulations = QSpinBox()
            self.accumulations.setValue(self.actiondict['accumulations'])
            self.accumulations.valueChanged.connect(self.accum_changed)

        self.progress_label = QLabel()
        self.progress_label.setText('')
        self.progress_label.setObjectName('progress_label')
        self.progress_label.setStyleSheet('QLabel#progress_label {color: magenta}')

    def roi_fields(self):
        """This method checks in the actiondict for the keyword ROI,
        and than adds spinboxes for every ROI key that it finds (top, bottom, left, right etc.).
        The maximum is set to 1500, I guess most spectrometers don't have more pixels than that.
        """
        self.layout.addWidget(QLabel('ROI:'), 0, 3)

        if 'ROI' in self.actiondict:
            self.roilist = {}
            teller = 0

            for key in self.actiondict['ROI']:
                self.roilist[key] = QDoubleSpinBox()
                self.roilist[key].setMaximum(1500)
                self.roilist[key].setValue(self.actiondict['ROI'][key])
                self.roilist[key].valueChanged.connect(self.roi_changed)

                self.layout.addWidget(QLabel(key), teller+1, 3)
                self.layout.addWidget(self.roilist[key],teller+1,4)

                teller+=1

        self.last_row = teller

    def place_in_grid(self):
        """In this method, the labels and the user input fields made in make_fields are put in a grid.
        """
        self.layout.addWidget(QLabel('exposure time: '),0,0)
        self.layout.addWidget(self.expo_value,0,1)
        self.layout.addWidget(self.expo_units,0,2)

        self.layout.addWidget(QLabel('grating: '),1,0)
        self.layout.addWidget(self.grating,1,1)

        self.layout.addWidget(QLabel('central wavelength: '),2,0)
        self.layout.addWidget(self.central_nm,2,1)

        self.layout.addWidget(self.progress_label,2,2)

        if hasattr(self,'accumulations'):
            self.layout.addWidget(QLabel('accumulations:'))
            self.layout.addWidget(self.accumulations, 3, 1)
            if self.last_row < 3:
                self.last_row = 3

    def roi_changed(self, this_roi):
        """This method is the one that makes sure of updating the actiondict if any of the ROI is changed by the user.
        Because the method roi_fields is walking through the list of rois and appending it,
        if you send the key to this method via valueChanged, it will always give you the list key in the row.
        So in this method, you walk through the dictionary of spinboxes and compare them to the spinbox that was sending you the valueChanged command,
        and than you change the actiondict. It's slightly crappy but it works...
        """
        for roi in self.roilist:
            if self.roilist[roi] == self.sender():
                self.actiondict['ROI'][roi] = self.sender().value()
                self.logger.debug('Changing ROI {} value to {}'.format(roi,self.sender().value()))

    def accum_changed(self):
        self.actiondict['accumulations'] = int(self.accumulations.value())
        self.logger.debug('changing winspec accumulations')

    def expo_changed(self):
        """This method is the one that makes sure of updating the actiondict if the exposure time is changed by the user.
        """
        self.actiondict['exposuretime'] = str(spin_combo_to_pint_apply_limits(self.expo_value, self.expo_units,
                                                                              Q_(self.actiondict['exposuretime_min']),
                                                                              Q_(self.actiondict['exposuretime_max'])))
        self.logger.debug('Changing winspec exposuretime')

        if hasattr(self,'measurement_gui_parent'):
            self.logger.debug('winspec action gui can find his parent master gui')
            self.measurement_gui_parent.update_from_guis()

    def grating_changed(self):
        """This method updates the grating in the actiondict if the user changes it.
        """
        self.actiondict['grating'] = int(self.grating.currentText())
        self.logger.debug('Changing winspec grating')

    def central_nm_changed(self):
        """This method updates the central wavelength in the actiondict if the user changes it.
        """
        self.actiondict['central_nm'] = int(self.central_nm.value())
        self.logger.debug('Changing winspec central wavelength')