from hyperion import logging
from hyperion.view.base_guis import BaseGui

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QTimer

class BaseActionGui(BaseGui):
    def __init__(self, experiment, actiondict):
        self.logger = logging.getLogger(__name__)
        super().__init__()
        self.init()
        self.experiment = experiment
        self.actiondict = actiondict
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0,0,0,0)
        outer_layout.setSpacing(0)
        self.box = QGroupBox(actiondict['Name'])
        self.box.setContentsMargins(0, 9, 0, 0)
        self.initUI()
        outer_layout.addWidget(self.box)
        self.setLayout(outer_layout)

    def init(self):
        self.logger.warning('This method should be overridden by child class')

    def initUI(self):
        self.logger.warning('This method should be overridden by child class')

class ExampleAction(BaseActionGui):
    # Don't add an __init__. Or if you do make sure to call super().__init__(*args, **kwargs)

    # def __init__(self, experiment, actiondict):
    #     super().__init__(experiment, actiondict)
    def init(self):
        self.logger = logging.getLogger(__name__)

    def initUI(self):
        # Create layout of your choice:
        layout = QHBoxLayout()

        # Create your gui elements and add them to the layout
        dsp = QDoubleSpinBox()
        cb = QComboBox()
        layout.addWidget(dsp)
        layout.addWidget(cb)

        # Set your layout to self.box
        self.box.setLayout(layout)


if __name__=='__main__':
    app = QApplication([])
    example_action_dict = {'Name':'ExampleAction'}
    test = ExampleAction(example_action_dict)
    test.show()
    app.exec_()
