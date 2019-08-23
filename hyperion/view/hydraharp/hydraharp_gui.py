import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QLabel, QLineEdit, QComboBox, QVBoxLayout,QFileDialog
from hyperion.instrument.correlator.hydraharp_instrument import HydraInstrument
from hyperion import ur, root_dir
import pyqtgraph as pg
import pyqtgraph.exporters

class App(QWidget):

    def __init__(self, hydra_instrument, draw):
        super().__init__()
        self.title = 'hydraharp gui, hail hydra'
        self.left = 50
        self.top = 50
        self.width = 320
        self.height = 200
        self.histogram_number = 0
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.hydra_instrument = hydra_instrument
        self.draw = draw
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        #initialize and configurate the settings of the hydraharp
        self.hydra_instrument.initialize()
        self.hydra_instrument.configurate()

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.magenta)
        self.setPalette(p)

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
        self.make_export_label()
    def make_textfields(self):
        self.make_array_length_textfield()
        self.make_resolution_textfield()
        self.make_integration_time_textfield()
        self.make_channel_combobox()
        self.make_export_textfield()

    def make_save_histogram_button(self):
        self.save_histogram_button = QPushButton('save histrogram', self)
        self.save_histogram_button.setToolTip('save your histogram in a file')
        #The maek_save_button should be setEnabled False
        self.save_histogram_button.setEnabled(True)
        self.save_histogram_button.clicked.connect(self.save_histogram)
        self.grid_layout.addWidget(self.save_histogram_button, 1, 0)
    def make_take_histogram_button(self):
        self.take_histogram_button = QPushButton('take histogram', self)
        self.take_histogram_button.setToolTip('take the histogram')
        self.take_histogram_button.clicked.connect(self.take_histogram)
        self.grid_layout.addWidget(self.take_histogram_button, 0, 0)

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
    def make_export_label(self):
        self.export_label = QLabel(self)
        self.export_label.setText("Export file: ")
        self.grid_layout.addWidget(self.export_label, 4, 1)

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
    def make_export_textfield(self):
        self.export_textfield = QLineEdit(self)
        self.export_textfield.setText(root_dir)
        self.grid_layout.addWidget(self.export_textfield, 4, 2)


    def take_histogram(self):
        """
        In this method there will be made a histogram using the input of the user.
        To set(a method to clear the data from the previous histogram)the length of the array is needed and
        the resolution in picoseconds(ps). The histogram gets made by make_histogram using the integration time(how long
        does your measurement need to take?) and the channel on which to measure.
        The data gets plot in the DrawHistogram plot(self.draw.random_plot.plot())
        """
        print("Take the histrogram")
        #needs time and count_channel( 1 or 2)
        self.hydra_instrument.set_histogram(leng=int(self.array_length_textfield.text()),res = float(self.resolution_textfield.text()) *ur('ps'))
        self.histogram= self.hydra_instrument.make_histogram(int(self.integration_time_textfield.text()) * ur('s'), self.channel_combobox.currentText())
        self.draw.random_plot.plot(self.histogram, clear=True)
        #make it possible to press the save_histogram_button.(should be True)
        self.save_histogram_button.setEnabled(True)

    def save_histogram(self):
        print('save the histogram')
        try:
            #plt = pg.plot(self.histogram)
            plt = pg.plot([1,5,2,4,3])
            exporter = pg.exporters.ImageExporter(plt.plotItem)
            # set export parameters if needed
            exporter.parameters()['height'] = 100  # (note this also affects height parameter)
            exporter.parameters()['width'] = 100  # (note this also affects height parameter)
            self.actually_save_histogram(exporter)
            #there must first be made another(or the same) histogram before this method can be accessed.(should be False)
            self.save_histogram_button.setEnabled(True)
        except Exception:
            print("There is no picture to export...change that by clicking the button above")

    def actually_save_histogram(self, exporter):
        # save to file
        if self.export_textfield.text() != "":
            file_name = self.export_textfield.text() + "\\histogram_"+str(self.histogram_number)+".png"
            self.histogram_number += 1
            exporter.export(file_name)
        else:
            #a file chooser will be used
            file_name = self.get_file_path_via_filechooser()
            exporter.export(file_name)

    def get_file_path_via_filechooser(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "All Files (*);;Text Files (*.txt)", options=options)
        return fileName + ".png"

class DrawHistogram(QWidget):

    """
    In this class a widget is created to draw a graph on.
    """

    def __init__(self):
        super().__init__()
        self.title = 'draw hydraharp gui'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.random_plot = pg.PlotWidget()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        vbox.addWidget(self.random_plot)
        self.setLayout(vbox)
        self.show()

if __name__ == '__main__':
    hydra_instrument = HydraInstrument(settings={'devidx': 0, 'mode': 'Histogram', 'clock': 'Internal',
                                                 'controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'})
    app = QApplication(sys.argv)
    draw = DrawHistogram()
    ex = App(hydra_instrument, draw)
    sys.exit(app.exec_())
