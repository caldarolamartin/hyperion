# utf 8
"""
========
AOTF GUI
========

Instrument gui to controller the AOTF.





"""
import sys, os
from hyperion import logging
from hyperion import ur
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from hyperion.instrument.position.anc_instrument import Anc350Instrument
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

    def __init__(self, instr, output_gui=None, also_close_output=True):
        super().__init__()
        self.logger = logman.getLogger(__name__)
        self.also_close_output = also_close_output
        self.inst= instr
        self.output_gui = output_gui

        # load the UI file
        name = 'attocube.ui'
        gui_folder = os.path.dirname(os.path.abspath(__file__))
        gui_file = os.path.join(gui_folder, name)
        self.logger.debug('Loading the GUI file: {}'.format(gui_file))
        self.gui = uic.loadUi(gui_file, self)

        self.initUI()

    def initUI(self):
        """Connect all buttons, comboBoxes and doubleSpinBoxes to methods
        """
        self.logger.debug('Setting up the Measurement GUI')
        self.setWindowTitle(self.title)

        self.show()


    def stop(self):
        """
        Stop the instruments activity. This can be used by a measurement or an ExperimentGui to tell an instrument to stop doing what it's doing (so that it can start taking
        """
        if self.cont_plot_timer.isActive():
            self.cont_plot_timer.stop()

    def closeEvent(self, event):
        if self.also_close_output and self.output_gui is not None:
            if self.cont_plot_timer.isActive():
                self.logger.debug('Stop continuous plotting')
                self.cont_plot_timer.stop()
            self.logger.debug('Closing output widget')
            try:
                self.output_gui.close()
            except:
                pass


if __name__ == '__main__':
    from hyperion.instrument.polarization.aa_aotf import AaAotf
    aotf = AaAotf(settings= {'port':'COM8', 'dummy':False,
                                        'controller': 'hyperion.controller.aa.aa_modd18012/AaModd18012',
                                        'apply defaults': False})
    app = QApplication(sys.argv)
    ex = AotfInstrumentGui(aotf)
    sys.exit(app.exec_())