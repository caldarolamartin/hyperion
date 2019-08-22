import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QLabel, QLineEdit, QComboBox
from hyperion.instrument.correlator.hydraharp_instrument import HydraInstrument
from hyperion import ur

class App(QWidget):

    def __init__(self, hydra_instrument):
        super().__init__()
        self.title = 'hydraharp gui, hail hydra'
        self.left = 50
        self.top = 50
        self.width = 320
        self.height = 200
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.hydra_instrument = hydra_instrument
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        #initialize and configurate the settings of the hydraharp
        self.hydra_instrument.initialize()
        self.hydra_instrument.configurate()

        self.make_buttons()
        self.make_labels()
        self.make_textfields()
        self.show()
    def make_buttons(self):
        self.make_save_histogram_button()
        self.make_take_histogram_button()
    def make_labels(self):
        self.make_array_length_label()
        self.make_resolution_label()
        self.make_integration_time_label()
        self.make_channel_label()
        self.make_data_label()
        self.make_end_time_label()
    def make_textfields(self):
        self.make_array_length_textfield()
        self.make_resolution_textfield()
        self.make_integration_time_textfield()
        self.make_channel_combobox()
        self.make_data_textfield()
        self.make_end_time_textfield()

    def make_save_histogram_button(self):
        self.save_histogram_button = QPushButton('save histrogram', self)
        self.save_histogram_button.setToolTip('save your histogram in a file')
        self.save_histogram_button.clicked.connect(self.save_histogram)
        self.grid_layout.addWidget(self.save_histogram_button,1, 0)
    def make_take_histogram_button(self):
        self.take_histogram_button = QPushButton('take histogram', self)
        self.take_histogram_button.setToolTip('take the histogram')
        self.take_histogram_button.clicked.connect(self.take_histogram)
        self.grid_layout.addWidget(self.take_histogram_button, 0,0)

    def make_array_length_label(self):
        self.array_length_label = QLabel(self)
        self.array_length_label.setText("Array lengh\n(standard value is fine\n(most of the time)): ")
        self.grid_layout.addWidget(self.array_length_label, 0, 1)
    def make_resolution_label(self):
        self.resolution_label = QLabel(self)
        self.resolution_label.setText("Resolution in ps: ")
        self.grid_layout.addWidget(self.resolution_label, 1, 1)
    def make_integration_time_label(self):
        self.integration_time_label = QLabel(self)
        self.integration_time_label.setText("Integration time(in sec.): ")
        self.grid_layout.addWidget(self.integration_time_label, 2, 1)
    def make_channel_label(self):
        self.channel_label = QLabel(self)
        self.channel_label.setText("Channel: ")
        self.grid_layout.addWidget(self.channel_label, 3, 1)
    def make_data_label(self):
        self.data_label = QLabel(self)
        self.data_label.setText("Data")
        self.grid_layout.addWidget(self.data_label, 4, 1)
    def make_end_time_label(self):
        self.end_time_label = QLabel(self)
        self.end_time_label.setText("End time(in sec.): ")
        self.grid_layout.addWidget(self.end_time_label, 5, 1)

    def make_array_length_textfield(self):
        self.array_length_textfield = QLineEdit(self)
        self.array_length_textfield.setText("65536")
        self.grid_layout.addWidget(self.array_length_textfield, 0, 2)
    def make_resolution_textfield(self):
        self.resolution_textfield = QLineEdit(self)
        self.resolution_textfield.setText("8.0")
        self.grid_layout.addWidget(self.resolution_textfield, 1, 2)
    def make_integration_time_textfield(self):
        self.integration_time_textfield = QLineEdit(self)
        self.integration_time_textfield.setText("5")
        self.grid_layout.addWidget(self.integration_time_textfield, 2, 2)
    def make_channel_combobox(self):
        self.channel_combobox = QComboBox()
        self.channel_combobox.addItems(["1","2"])
        self.grid_layout.addWidget(self.channel_combobox, 3, 2)
    def make_data_textfield(self):
        self.data_textfield = QLineEdit(self)
        self.data_textfield.setText("???")
        self.grid_layout.addWidget(self.data_textfield, 4, 2)
    def make_end_time_textfield(self):
        self.end_time_textfield = QLineEdit(self)
        self.end_time_textfield.setText("some time")
        self.grid_layout.addWidget(self.end_time_textfield, 5, 2)


    def take_histogram(self):
        print("Take the histrogram")
        #needs time and count_channel( 1 or 2)
        self.hydra_instrument.set_histogram(leng=int(self.array_length_textfield.text()),res = float(self.resolution_textfield.text()) *ur('ps'))
        self.histogram= self.hydra_instrument.make_histogram(int(self.integration_time_textfield.text()) * ur('s'), self.channel_combobox.currentText())

    def save_histogram(self):
        print('save the histogram')


if __name__ == '__main__':
    hydra_instrument = HydraInstrument(settings = {'devidx':0, 'mode':'Histogram', 'clock':'Internal',
                                   'controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'})

    app = QApplication(sys.argv)
    ex = App(hydra_instrument)
    sys.exit(app.exec_())
