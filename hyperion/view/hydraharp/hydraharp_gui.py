import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout
from hyperion.instrument.correlator.hydraharp_instrument import HydraInstrument

class App(QWidget):

    def __init__(self, hydra_instrument):
        super().__init__()
        self.title = 'hydraharp gui, hail hydra'
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 200
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.hydra_instrument = hydra_instrument
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.save_histogram_button = QPushButton('save histrogram', self)
        self.save_histogram_button.setToolTip('save your histogram in a file')
        self.save_histogram_button.clicked.connect(self.save_histogram)
        self.grid_layout.addWidget(self.save_histogram_button,0, 2)

        self.take_histogram_button = QPushButton('take histogram', self)
        self.take_histogram_button.setToolTip('take the histogram')
        self.take_histogram_button.clicked.connect(self.take_histogram)


        self.show()
    def take_histogram(self):
        print("Take the histrogram")

    def save_histogram(self):
        print('save the histogram')


if __name__ == '__main__':
    hydra_instrument = HydraInstrument(settings = {'devidx':0, 'mode':'Histogram', 'clock':'Internal',
                                   'controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'})

    app = QApplication(sys.argv)
    ex = App(hydra_instrument)
    sys.exit(app.exec_())
