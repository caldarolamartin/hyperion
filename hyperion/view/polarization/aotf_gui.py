# utf 8
"""
========
AOTF GUI
========

Instrument gui to controller the AOTF.





"""
import sys, os
from hyperion.core import logman
from hyperion import ur
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from hyperion.view.base_guis import BaseGui
from hyperion.view.general_worker import WorkThread

class AotfInstrumentGui(BaseGui):
    """
    GUI for the AOTF

    :param instr: class for the instrument to control.
    :type instr: instance of the instrument class
    :param output_gui:
    :type output_gui:

    """

    def __init__(self, instr, also_close_output=True):
        super().__init__()
        self.logger = logman.getLogger(__name__)
        self.also_close_output = also_close_output
        self.instr= instr

        self.instr.blanking(True)

        # load the UI file
        name = 'aotf_instrument.ui'
        gui_folder = os.path.dirname(os.path.abspath(__file__))
        gui_file = os.path.join(gui_folder, name)
        self.logger.debug('Loading the GUI file: {}'.format(gui_file))
        self.gui = uic.loadUi(gui_file, self)

        self.mode = 'internal'
        self.wavelength = 532 * ur('nm')
        self.delta_wavelength = 1 *ur('nm')
        self.power = 20
        self.enable = False

        self.initUI()

    def initUI(self):
        """Connect all buttons, comboBoxes and doubleSpinBoxes to methods
        """
        self.logger.debug('Setting up the Measurement GUI')

        self.show()

        self.gui.comboBox_mode.setCurrentText(self.mode)
        self.gui.comboBox_mode.currentTextChanged.connect(self.mode_changed)

        self.gui.doubleSpinBox_wavelength.setValue(self.wavelength.m_as('nm'))
        self.gui.doubleSpinBox_wavelength.valueChanged.connect(self.wav_changed)

        self.gui.doubleSpinBox_wavelength_delta.setValue(self.delta_wavelength.m_as('nm'))
        self.gui.doubleSpinBox_wavelength_delta.valueChanged.connect(self.delta_wav_changed)

        self.gui.doubleSpinBox_power.setValue(self.power)
        self.gui.doubleSpinBox_power.valueChanged.connect(self.power_changed)

        self.gui.checkBox_enable.setChecked(self.enable)
        self.gui.checkBox_enable.stateChanged.connect(self.enable_changed)

        self.gui.pushButton_goto.clicked.connect(self.apply_wavelength)

    def mode_changed(self):
        self.mode = self.gui.comboBox_mode.currentText()
        self.logger.debug('Mode changed')

    def wav_changed(self):
        wavelength_lims = self.instr.wavelength_lims

        wav = self.gui.doubleSpinBox_wavelength.value()

        self.gui.doubleSpinBox_wavelength.setSingleStep(self.delta_wavelength.m_as('nm'))

        if wav > wavelength_lims[1].m_as('nm'):
            wav = wavelength_lims[1]
            self.gui.doubleSpinBox_wavelength.setValue(wav.m_as('nm'))

        if wav < wavelength_lims[0].m_as('nm'):
            wav = wavelength_lims[0]
            self.gui.doubleSpinBox_wavelength.setValue(wav.m_as('nm'))

        self.wavelength = wav * ur('nm')
        self.logger.debug('Wavelength changed')

    def delta_wav_changed(self):
        self.delta_wavelength = self.gui.doubleSpinBox_wavelength_delta.value() * ur('nm')

        self.gui.doubleSpinBox_wavelength.setSingleStep(self.delta_wavelength.m_as('nm'))

        self.logger.debug('Changed the wavelength step')

    def power_changed(self):

        if self.gui.doubleSpinBox_power.value() > 21:
            self.gui.doubleSpinBox_power.setValue(21)

        if self.gui.doubleSpinBox_power.value() < 0:
            self.gui.doubleSpinBox_power.setValue(0)

        self.power = self.gui.doubleSpinBox_power.value()

        self.logger.debug('Changed the power')

    def enable_changed(self):
        self.enable = self.gui.checkBox_enable.isChecked()
        self.logger.debug('Enabling or disabling')

    def apply_wavelength(self):
        self.logger.debug('Applying the wavelength calibration and doing stuff in instrument')
        self.instr.set_wavelength(self.wavelength, self.power, self.enable, self.mode)



if __name__ == '__main__':
    from hyperion.instrument.polarization.aa_aotf import AaAotf
    with AaAotf(settings= {'port':'COM8', 'dummy':False,
                                        'controller': 'hyperion.controller.aa.aa_modd18012/AaModd18012',
                                        'apply defaults': False})  as aotf:
        app = QApplication(sys.argv)
        ex = AotfInstrumentGui(aotf)
        sys.exit(app.exec_())