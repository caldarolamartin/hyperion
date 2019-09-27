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



class BeamFlagsGui(QWidget):
    """"
    This is simple pyqt5 gui with the ability to create threads and stop them,
    that is harder than it sounds.
    """

    def __init__(self, beam_flags_instr):
        super().__init__()

        # uic.loadUi(os.path.join(p, 'GUI', 'double_flag.ui'), self)
        # uic.loadUi('double_flag.ui', self)

        self.title = 'Beam Flags Gui'
        # self.left = 40
        # self.top = 40
        # self.width = 320
        # self.height = 200

        self.bfi = beam_flags_instr
        self.flags = {}

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        # self.setGeometry(self.left, self.top, self.width, self.height)

        self.setAutoFillBackground(True)
        self.p = self.palette()
        self.set_color(Qt.red)

        self.get_icons(self.bfi.settings)

        layout = QVBoxLayout()

        toolbar = QToolBar("My main toolbar")
        # self.addToolBar(Qt.LeftToolBarArea, toolbar)


        for index, flag_settings in enumerate(self.bfi.settings['flags']):
            # create QAction flag object and add it to the internal dictionary
            flag = self.create_flag_gui(flag_settings, index)
            self.flags[ flag_settings['controller_id'] ] = flag
            toolbar.addAction(flag)

        self.setLayout(layout)
        self.show()

    def get_icons(self, settings):
        try:
            self.icon_red  = QIcon( os.path.join(settings['icon_base_path'], settings['icon_red'] ) )
            self.icon_green= QIcon( os.path.join(settings['icon_base_path'], settings['icon_green']) )
        except:
            self.icon_red  = QIcon(None)
            self.icon_green= QIcon(None)

    def create_flag_gui(self, flag_settings, index):

        flag = QAction(self.icon_red,flag_settings['gui_name'],self)
        flag.setStatusTip("Toggle {}".format(flag_settings['gui_name']))
        flag.triggered.connect( lambda x: self.on_flag_clicked(flag, x, index) )
        flag.setCheckable(True)
        return flag

    def on_flag_clicked(self, flag, signal, index, update_instrument = True):
        flag_settings = self.bfi.settings['flags'][index]
        if flag_settings['gui_pressed_is_red']:
            signal = not signal

        flag.setText( flag_settings[ ['gui_red_name', 'gui_green_name'][signal] ] )
        flag.setIcon( [self.icon_green,self.icon_green][signal] )

        if update_instrument:
            self.bfi.set_specific_flag_state(flag_settings['controller_id'], flag_settings[ ['controller_red_command',controller_green_command][signal] ] )



    def auto_update_gui_flag_states(self):
        for flag_settings in self.bfi.settings['flags']:
            if flag_settings['controller_id'] in self.bfi.flag_states:
                current_state = self.bfi.flag_states[flag_settings['controller_id']]
                if current_state == flag_settings['controller_red_command']:
                    self.flags[flag_settings['controller_id']].setText(flag_settings['gui_red_name'])
                elif current_state == flag_settings['controller_green_command']:
                    self.flags[flag_settings['controller_id']].setText(flag_settings['gui_green_name'])
                else:
                    pass

    def make_button_1(self):
        self.button = QPushButton('start button', self)
        self.button.setToolTip('This is an example button')
        self.button.move(10,10)
        self.button.clicked.connect(self.on_click)
    def make_button_2(self):
        self.button_2 = QPushButton('end button',self)
        self.button_2.setToolTip('end the function')
        self.button_2.move(90, 10)
        self.button_2.clicked.connect(self.stop_on_click_function)


    def set_color(self, color):
        """
        Set the color of the widget
        :param color: a color you want the gui to be
        :type string
        """
        self.p.setColor(self.backgroundRole(), color)
        self.setPalette(self.p)

    def on_click(self):
        #initialize a long(couple of seconds) test function.
        self.worker_thread = WorkThread(self.go_to_sleep)
        self.worker_thread.start()

    def stop_on_click_function(self):
        """
        stop a thread if one is running
        """
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
            print('this function is going to stop the on_click function')
        else:
            return

    def go_to_sleep(self):
        """
        function that starts the thread.
        """
        print('button click')
        self.button.setEnabled(False)
        self.set_color(Qt.yellow)
        time.sleep(4)
        self.set_color(Qt.red)
        self.button.setEnabled(True)

if __name__ == '__main__':
    import logging
    import yaml

    example_config_file = 'beam_flags_example_config.yml'
    with open(example_config_file,'r') as file:
        example_config = yaml.full_load(file)
    beam_flag_settings = example_config['Instruments']['BeamFlags']
    # beam_flag_settings['port']='COM4'   # modify the port if required

    with BeamFlagsInstr(beam_flag_settings) as instr:
        app = QApplication(sys.argv)
        ex = BeamFlagsGui(instr)
        sys.exit(app.exec_())

