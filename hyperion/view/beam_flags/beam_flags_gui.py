import sys
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
# from PyQt5.QtCore import Qt
# from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from hyperion.instrument.beam_flags.beam_flags_instr import BeamFlagsInstr
from hyperion.view.general_worker import WorkThread
import os
from PyQt5 import uic
import pyqtgraph as pg

class BeamFlagsGui(QWidget):
    """"
    This is simple pyqt5 gui with the ability to create threads and stop them,
    that is harder than it sounds.
    """

    def __init__(self, beam_flags_instr):
        super().__init__()

        self.logger = logging.getLogger(__name__)

        # uic.loadUi(os.path.join(p, 'GUI', 'double_flag.ui'), self)
        # uic.loadUi('double_flag.ui', self)

        self.title = 'Beam Flags Gui'
        self.left = 400
        self.top = 400
        self.width = 240
        self.height = 80

        self.bfi = beam_flags_instr
        self.bf_settings = self.bfi.settings['gui_flags']

        self.red_char   = self.bfi.settings['flag_states']['red']
        self.green_char = self.bfi.settings['flag_states']['green']

        self.red_color   = self.bfi.settings['gui_red_color']
        self.green_color = self.bfi.settings['gui_green_color']


        self.initUI()

        indicator_update_time = 100 # ms
        if 'gui_state_update_ms' in self.bfi.settings:
            indicator_update_time = self.bfi.settings['gui_state_update_ms']

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_label_states)
        self.timer.start(indicator_update_time)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        layout = QGridLayout()

        for index, (flag_id, gui_flag) in enumerate(self.bf_settings.items()):
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
        for flag_id in self.bf_settings.keys():
            state = self.bfi.get_specific_flag_state(flag_id)
            if state != self.bf_settings[flag_id]['state']:
                self.bf_settings[flag_id]['state'] = state
                self.set_label_state(flag_id)

    def set_label_state(self, flag_id):
        label = self.bf_settings[flag_id]['label']
        state = self.bf_settings[flag_id]['state']
        if state == self.red_char:
            label.setStyleSheet('background-color: ' + self.red_color)
            label.setText(self.bf_settings[flag_id]['red_name'])
        elif state == self.green_char:
            label.setStyleSheet('background-color: ' + self.green_color)
            label.setText(self.bf_settings[flag_id]['green_name'])
        else:
            self.logger.warning('received state is unknown')

    def button_clicked(self, flag_id):
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


    #     for index, flag_settings in enumerate(self.bfi.settings['flags']):
    #         # create QAction flag object and add it to the internal dictionary
    #         flag = self.create_flag_gui(flag_settings, index)
    #         self.flags[ flag_settings['controller_id'] ] = flag
    #         toolbar.addAction(flag)
    #
    #     self.setLayout(layout)
    #     self.show()
    #
    # def get_icons(self, settings):
    #     try:
    #         self.icon_red  = QIcon( os.path.join(settings['icon_base_path'], settings['icon_red'] ) )
    #         self.icon_green= QIcon( os.path.join(settings['icon_base_path'], settings['icon_green']) )
    #     except:
    #         self.icon_red  = QIcon(None)
    #         self.icon_green= QIcon(None)
    #
    # def create_flag_gui(self, flag_settings, index):
    #     flag_gui =
    #
    #     flag = QAction(self.icon_red,flag_settings['gui_name'],self)
    #     flag.setStatusTip("Toggle {}".format(flag_settings['gui_name']))
    #     flag.triggered.connect( lambda x: self.on_flag_clicked(flag, x, index) )
    #     flag.setCheckable(True)
    #     return flag
    #
    # def on_flag_clicked(self, flag, signal, index, update_instrument = True):
    #     flag_settings = self.bfi.settings['flags'][index]
    #     if flag_settings['gui_pressed_is_red']:
    #         signal = not signal
    #
    #     flag.setText( flag_settings[ ['gui_red_name', 'gui_green_name'][signal] ] )
    #     flag.setIcon( [self.icon_green,self.icon_green][signal] )
    #
    #     if update_instrument:
    #         self.bfi.set_specific_flag_state(flag_settings['controller_id'], flag_settings[ ['controller_red_command',controller_green_command][signal] ] )
    #
    #
    #
    # def auto_update_gui_flag_states(self):
    #     for flag_settings in self.bfi.settings['flags']:
    #         if flag_settings['controller_id'] in self.bfi.flag_states:
    #             current_state = self.bfi.flag_states[flag_settings['controller_id']]
    #             if current_state == flag_settings['controller_red_command']:
    #                 self.flags[flag_settings['controller_id']].setText(flag_settings['gui_red_name'])
    #             elif current_state == flag_settings['controller_green_command']:
    #                 self.flags[flag_settings['controller_id']].setText(flag_settings['gui_green_name'])
    #             else:
    #                 pass
    #
    # def make_button_1(self):
    #     self.button = QPushButton('start button', self)
    #     self.button.setToolTip('This is an example button')
    #     self.button.move(10,10)
    #     self.button.clicked.connect(self.on_click)
    # def make_button_2(self):
    #     self.button_2 = QPushButton('end button',self)
    #     self.button_2.setToolTip('end the function')
    #     self.button_2.move(90, 10)
    #     self.button_2.clicked.connect(self.stop_on_click_function)
    #
    #
    # def set_color(self, color):
    #     """
    #     Set the color of the widget
    #     :param color: a color you want the gui to be
    #     :type string
    #     """
    #     self.p.setColor(self.backgroundRole(), color)
    #     self.setPalette(self.p)
    #
    # def on_click(self):
    #     #initialize a long(couple of seconds) test function.
    #     self.worker_thread = WorkThread(self.go_to_sleep)
    #     self.worker_thread.start()
    #
    # def stop_on_click_function(self):
    #     """
    #     stop a thread if one is running
    #     """
    #     if self.worker_thread.isRunning():
    #         self.worker_thread.quit()
    #         self.worker_thread.wait()
    #         print('this function is going to stop the on_click function')
    #     else:
    #         return
    #
    # def go_to_sleep(self):
    #     """
    #     function that starts the thread.
    #     """
    #     print('button click')
    #     self.button.setEnabled(False)
    #     self.set_color(Qt.yellow)
    #     time.sleep(4)
    #     self.set_color(Qt.red)
    #     self.button.setEnabled(True)

if __name__ == '__main__':
    import logging
    import yaml
    from hyperion import _logger_format, _logger_settings

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])


    example_config_file = 'beam_flags_example_config.yml'
    with open(example_config_file,'r') as file:
        example_config = yaml.full_load(file)
    beam_flag_settings = example_config['Instruments']['BeamFlags']
    # beam_flag_settings['port']='COM4'   # modify the port if required

    with BeamFlagsInstr(beam_flag_settings) as instr:
        instr.initialize()
        app = QApplication(sys.argv)
        ex = BeamFlagsGui(instr)
        sys.exit(app.exec_())

