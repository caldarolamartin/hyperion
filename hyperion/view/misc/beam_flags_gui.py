import hyperion
import logging
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from hyperion.instrument.misc.beam_flags_instr import BeamFlagsInstr
from hyperion.view.general_worker import WorkThread

class BeamFlagsGui(QWidget):
    """
    Gui for beam blocker flags.
    Requires hyperion.instrument.misc.beam_flags_instr/BeamFlagsInstr instrument as input.

    :param beam_flags_instr: instrument object to control
    :type beam_flags_instr: an instance of the class
    """

    def __init__(self, beam_flags_instr):
        """
        Gui for beam blocker flags.

        :param beam_flags_instr: The beam flags instrument object to create the gui for
        :type beam_flags_instr: BeamFlagsInstr object
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.left = 400
        self.top = 400
        self.width = 240
        self.height = 80

        self.bfi = beam_flags_instr
        self.bf_settings = self.bfi.settings['gui_flags']

        if 'name' in self.bfi.settings:
            self.title = self.bfi.settings['name']
        else:
            self.title = 'Beam Flags'

        self.red_char   = self.bfi.settings['flag_states']['red']
        self.green_char = self.bfi.settings['flag_states']['green']
        self.red_color   = self.bfi.settings['gui_red_color']
        self.green_color = self.bfi.settings['gui_green_color']

        self.initUI()

        # Start timer to repeatedly pull the current state of the toggle switches:
        self.logger.info('Starting timer thread')
        if 'gui_state_update_ms' in self.bfi.settings:
            indicator_update_time = self.bfi.settings['gui_state_update_ms']
        else:
            indicator_update_time = 100  # ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_label_states)
        self.timer.start(indicator_update_time)

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

        for index, (flag_id, gui_flag) in enumerate(self.bf_settings.items()):
            self.logger.info("Adding flag '{}' to gui".format(flag_id))
            state = self.bfi.get_specific_flag_state(flag_id)
            self.bf_settings[flag_id]['state'] = state
            label = QLabel('')
            self.bf_settings[flag_id]['label'] = label
            button = QPushButton(gui_flag['name'], self)

            button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

            button.pressed.connect( lambda x=flag_id: self.button_clicked(x) )
            if 'shortkey' in gui_flag:
                shortk = gui_flag['shortkey']
                shortk_tip = '  ('+shortk+')'
                button.setText(gui_flag['name']+shortk_tip)
                shortcut = QShortcut(QKeySequence(shortk), self)        # not sure if this will work in our modular design
                shortcut.activated.connect(lambda x = flag_id: self.button_clicked(x) )
            else:
                shortk_tip = ''
                button.setStatusTip('Toggle '+gui_flag['name']+shortk_tip)

            label.setAlignment(Qt.AlignCenter)
            self.set_label_state(flag_id)

            layout.addWidget(button, index, 0)
            layout.addWidget(label, index, 1)

        self.setLayout(layout)
        self.show()

    def update_label_states(self):
        """ Asks device for current states of all beam flags and updates state key and gui if it has changed."""
        for flag_id in self.bf_settings.keys():
            state = self.bfi.get_specific_flag_state(flag_id)
            if state != self.bf_settings[flag_id]['state']:
                self.logger.info("Manual state change detected of switch '{}': '{}'".format(flag_id,state))
                self.bf_settings[flag_id]['state'] = state
                self.set_label_state(flag_id)

    def set_label_state(self, flag_id):
        """ Sets gui label identified by flag_id to the corresponding value in the state key in settings."""
        label = self.bf_settings[flag_id]['label']
        state = self.bf_settings[flag_id]['state']
        self.logger.info("Set flag '{}' to '{}'".format(flag_id,state))
        if state == self.red_char:
            label.setStyleSheet('background-color: ' + self.red_color)
            label.setText(self.bf_settings[flag_id]['red_name'])
        elif state == self.green_char:
            label.setStyleSheet('background-color: ' + self.green_color)
            label.setText(self.bf_settings[flag_id]['green_name'])
        else:
            self.logger.warning('received state is unknown')

    def button_clicked(self, flag_id):
        """
        The gui buttons connect to this function.
        It toggles the state flag of the corresponding beam flag in the settings dict.
        It creates and runs a thread that sets the state of the beam flag on the instrument.
        """
        self.logger.info("Button of flag '{}' clicked".format(flag_id))
        state = self.bf_settings[flag_id]['state']
        if state == self.red_char:
            state = self.green_char
        elif state == self.green_char:
            state = self.red_char
        else:
            self.logger.warning('unknown state in internal dictionary')
        self.worker_thread = WorkThread(self.bfi.set_specific_flag_state, flag_id, state)
        self.worker_thread.start()
        # self.bfi.set_specific_flag_state(flag_id, state)
        self.bf_settings[flag_id]['state'] = state
        self.set_label_state(flag_id)


if __name__ == '__main__':
    import yaml
    import os
    # import hyperion

    hyperion.set_logfile(os.path.basename(__file__)+'.log')
    hyperion.stream_logger.setLevel(logging.DEBUG)
    hyperion.file_logger.setLevel(logging.DEBUG)


    example_config_file = 'beam_flags_example_config.yml'
    example_config_filepath = os.path.join(hyperion.root_dir, 'view', 'misc', example_config_file)
    with open(example_config_filepath,'r') as file:
        example_config = yaml.full_load(file)
    beam_flag_settings = example_config['Instruments']['BeamFlags']
    # beam_flag_settings['port']='COM4'   # modify the port if required

    with BeamFlagsInstr(beam_flag_settings) as instr:
        #instr.initialize()    # removed this line because instruments should initialize themselves
        app = QApplication(sys.argv)
        ex = BeamFlagsGui(instr)
        # sys.exit(app.exec_())
        app.exec_()
