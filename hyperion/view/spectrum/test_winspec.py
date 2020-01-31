from hyperion import logging
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from hyperion.instrument.spectrum.winspec_instr import WinspecInstr
from hyperion.view.general_worker import WorkThread
from hyperion import Q_

class TestWinspec(QWidget):
    """
    Gui for beam blocker flags.
    Requires hyperion.instrument.misc.beam_flags_instr/BeamFlagsInstr instrument as input.

    :param beam_flags_instr: instrument object to control
    :type beam_flags_instr: an instance of the class
    """

    def __init__(self, winspec_instr):
        """
        Gui for beam blocker flags.

        :param beam_flags_instr: The beam flags instrument object to create the gui for
        :type beam_flags_instr: BeamFlagsInstr object
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.title = 'Test Winspec'
        self.left = 400
        self.top = 400
        self.width = 240
        self.height = 80

        self.ws = winspec_instr

        self.initUI()


    def initUI(self):
        """
        Create all the gui elements and connect signals to methods.
        Adds 'state' and 'label' key and value to each flag in the settings dict.
        Reads the current state from the device and sets 'state' key and gui accordingly.
        """

        self.logger.info('Creating gui elements')
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        layout = QGridLayout()

        button = QPushButton('test', self)
        button.pressed.connect(self.button_clicked)

        layout.addWidget(button, 0 , 0)
        self.setLayout(layout)
        self.show()


    def button_clicked(self):
        print('test button is clicked')
        ws.controller.spt_set('NEW_POSITION',300)

        self.worker_thread = WorkThread(ws.controller.spt.Move)
        self.worker_thread.start()

        # """
        # The gui buttons connect to this function.
        # It toggles the state flag of the corresponding beam flag in the settings dict.
        # It creates and runs a thread that sets the state of the beam flag on the instrument.
        # """
        # self.logger.info("Button of flag '{}' clicked".format(flag_id))
        # state = self.bf_settings[flag_id]['state']
        # if state == self.red_char:
        #     state = self.green_char
        # elif state == self.green_char:
        #     state = self.red_char
        # else:
        #     self.logger.warning('unknown state in internal dictionary')
        # self.worker_thread = WorkThread(self.bfi.set_specific_flag_state, flag_id, state)
        # self.worker_thread.start()
        # # self.bfi.set_specific_flag_state(flag_id, state)
        # self.bf_settings[flag_id]['state'] = state
        # self.set_label_state(flag_id)


if __name__ == '__main__':

    settings = {'port': 'None', 'dummy': False,
                                'controller': 'hyperion.controller.princeton.winspec_contr/WinspecContr',
                                'shutter_controls': ['Disabled Closed', 'Disabled Opened']}


    with WinspecInstr(settings) as ws:
        ws.initialize()
        app = QApplication(sys.argv)
        g = TestWinspec(ws)
        # sys.exit(app.exec_())
        app.exec_()
