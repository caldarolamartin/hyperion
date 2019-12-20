from hyperion import logging
from hyperion.view.base_guis import BaseActionGui

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QTimer

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
