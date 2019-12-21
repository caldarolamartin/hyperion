from hyperion.core import logman
from hyperion.view.base_guis import BaseGui


from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QTimer
from PyQt5 import uic

class ExampleActionGui(BaseGui):
    def __init__(self, actiondict, experiment = None, parent = None):
        self.logger = logman.getLogger(__name__)
        self.logger.debug('Creating example action gui')
        super().__init__(parent)

        # # To load a ui file:
        # uic.loadUi(path_to_file, self)

        # # or maybe like this:
        # gui = QWidget()
        # uic.loadUi(path_to_file, gui)

        self.initUI()

    def initUI(self):
        # Create layout of your choice:
        self.layout = QHBoxLayout()
        # self.layout.setContentsMargins(0,0,0,0)

        # Create your gui elements and add them to the layout
        dsp = QDoubleSpinBox()
        cb = QComboBox()
        self.layout.addWidget(dsp)
        self.layout.addWidget(cb)

        # Set your layout to self
        self.setLayout(self.layout)



if __name__=='__main__':
    app = QApplication([])
    example_action_dict = {'Name':'ExampleAction'}
    test = ExampleActionGui(example_action_dict)
    test.show()
    app.exec_()
