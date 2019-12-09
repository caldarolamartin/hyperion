import sys
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from hyperion.view.base_guis import BaseGraph, TimeAxisItem
from pyqtgraph.Qt import QtGui

class Example_graph(BaseGraph):
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
        self.random_plot.plotItem.setLabel(axis="bottom", text="art", units="seconds")
        self.random_plot.plotItem.setLabel(axis="left", text="modern", units="meter")
        vbox.addWidget(self.random_plot)

        self.layout_plot()

        self.setLayout(vbox)
        self.show()

    def layout_plot(self):
        """| This method is purely for the layout. What I did here, is:
        | 1. make the background white
        | 2. set the title in orange
        | 3. set the labels in black with a specific size
        | 4. change the font size of the numbers on the axes
        | 5. use the TimeAxisItem from BaseGraph to make the axes black
        | 1 to 4 you can do without the extra class of TimeAxisItem, for 5 you need it.
        | 3 you can also do as is shown above in the initUI. But than you cannot access the size, only the text and units.
        """

        black_colour = (0,0,0)

        self.random_plot.setBackground('w')
        self.random_plot.setTitle("<span style=\"color:orange;font-size:30px\"> Your fancy title </span>")

        Xaxis = TimeAxisItem(orientation = 'bottom')
        Xaxis.attachToPlotItem(self.random_plot.getPlotItem())
        Xaxis.setPen(color = black_colour)

        Yaxis = TimeAxisItem(orientation = 'left')
        Yaxis.attachToPlotItem(self.random_plot.getPlotItem())
        Yaxis.setPen(color = black_colour)

        self.random_plot.setLabel('left', "<span style=\"color:black;font-size:20px\"> Physical quantity </span>")
        self.random_plot.setLabel('bottom', "<span style=\"color:black;font-size:20px\"> Physical quantity </span>")

        font = QtGui.QFont()
        font.setPixelSize(20)
        self.random_plot.getAxis("bottom").tickFont = font
        self.random_plot.getAxis("left").tickFont = font

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example_graph()
    sys.exit(app.exec_())
