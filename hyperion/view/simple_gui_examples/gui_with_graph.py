import sys
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'simple gui with just a graph'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()
        """"
        dock_widget_content = QWidget()
            vbox = QVBoxLayout()
            self.random_plot = pg.PlotWidget()
            vbox.addWidget(self.random_plot)
            dock_widget_content.setLayout(vbox)
            dock.setWidget(dock_widget_content)
        """

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        self.random_plot = pg.PlotWidget()
        vbox.addWidget(self.random_plot)
        self.setLayout(vbox)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
