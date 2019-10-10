import sys
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout


class App(QWidget):
    """"
    This class exists to have a 'large' widget where a graph can be drawn upon.
    """
    def __init__(self):
        super().__init__()
        self.title = 'simple gui with just a graph'
        self.left = 40
        self.top = 40
        self.width = 640
        self.height = 480
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        vbox = QVBoxLayout()
        self.random_plot = pg.PlotWidget()
        # setLabel(axis, text=None, units=None, unitPrefix=None, **args)[source]
        self.random_plot.plotItem.setLabel(axis="bottom", text="art", units="seconds")
        self.random_plot.plotItem.setLabel(axis="left", text="modern", units="meter")
        vbox.addWidget(self.random_plot)
        self.setLayout(vbox)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
