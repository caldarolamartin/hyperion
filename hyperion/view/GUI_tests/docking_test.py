import random

import PyQt5
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDockWidget, QListWidget, QTextEdit, QPushButton, \
    QGraphicsView, QAction, QLineEdit, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout
from lantz.qt import QtCore
import pyqtgraph as pg

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 simple window'
        self.left = 40
        self.top = 40
        self.width = 800
        self.height = 500

        self.setWindowTitle("Dock demo")

        self.initUI()
    def set_menu_bar(self):
        mainMenu = self.menuBar()
        self.fileMenu = mainMenu.addMenu('File')
        self.fileMenu.addAction("Exit NOW", self.close)
        self.dock_widget_1_file_item = mainMenu.addMenu('float dock widget 1')
        self.dock_widget_1_file_item.addAction("widget 1 loose", self.make_widget_1_loose)
        self.dock_widget_2_file_item = mainMenu.addMenu('dock_widget_2')
        self.dock_widget_2_file_item.addAction("widget 2 loose", self.make_widget_2_loose)

        self.draw_something = mainMenu.addMenu('draw')
        self.draw_something.addAction("Draw", self.on_click_submit)

        self.toolsMenu = mainMenu.addMenu('Tools')
        self.toolsMenu.addAction("Let widget 1 disappear", self.get_status_open_or_closed)
        self.helpMenu = mainMenu.addMenu('Help')

    def make_widget_1_loose(self):
        self.dock_widget_1.setFloating(True)
    def make_widget_2_loose(self):
        self.dock_widget_2.setFloating(True)


    def get_status_open_or_closed(self):
        self.dock_widget_1.setVisible(not self.dock_widget_1.isVisible())

    def on_click_submit(self):
        self.ydata = [random.random() for i in range(25)]
        self.xdata = [random.random() for i in range(25)]
        self.main_plot.plot(self.xdata, self.ydata, clear=True)

    def set_scroll_area(self):
        self.scroll_area = QScrollArea()

        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(False)

        self.widget_scroll_area_1 = QWidget()
        self.widget_scroll_area_2 = QWidget()

        self.vbox_scroll_area = QVBoxLayout()
        self.vbox_scroll_area.addWidget(self.widget_scroll_area_1)
        self.vbox_scroll_area.addWidget(self.widget_scroll_area_2)
        self.scroll_area.setLayout(self.vbox_scroll_area)

        self.scroll_area.setWidget(self.widget_scroll_area_1)

    def set_dock_widget_1(self):
        """
        how to add Qobjects to a dockable goes as follows.
        First you make a Qwidget where the content will be placed in. Call this things something with content in the name
        Then define the Qobjects you want to make
        Finally, you choose a layout((maybe absolute positioning is possible,
        haven't seen it in examples so it is not implemented in this code)QVBoxLayout, QHBoxLayout and QGridLayout)
        then you add the layout to the content widget and lastly you set the beginning Qwhatever as the widget of the dockwidget.
        """

        self.dock_widget_1 = QDockWidget("dock_widget_1", self)
        self.dock_widget_1_content = QWidget()
        self.dock_widget_1_content.setObjectName('de content voor de dock_widget')

        self.listWidget_right = QListWidget()
        self.listWidget_right.addItems(["item 1", "item 2", "item 3"])

        self.some_button = QPushButton('test', self)
        self.some_button.setToolTip('You are hovering over the button, \n what do you expect?')
        self.some_button.clicked.connect(self.on_click_submit)

        self.textbox = QLineEdit(self)
        self.textbox.setText('this is a test')

        self.vbox_1_scroll_area = QVBoxLayout()
        self.vbox_1_scroll_area.addWidget(self.some_button)
        self.vbox_1_scroll_area.addWidget(self.textbox)
        self.vbox_1_scroll_area.addWidget(self.listWidget_right)
        self.dock_widget_1_content.setLayout(self.vbox_1_scroll_area)
        self.dock_widget_1.setWidget(self.dock_widget_1_content)

        self.dock_widget_1.setFloating(False)
        self.dock_widget_1.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.dock_widget_1.setAllowedAreas(Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)

        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_1)

    def set_dock_widget_2(self):
        self.dock_widget_2 = QDockWidget("dock_widget_2", self)
        self.dock_widget_2_content = QWidget()
        self.dock_widget_2_content.setObjectName('de content voor de dock_widget')

        self.button_obey = QPushButton('obey', self)
        self.button_obey.setToolTip('You are hovering over the button, \n what do you expect?')

        self.main_plot = pg.PlotWidget()

        self.vbox_2 = QVBoxLayout()
        self.vbox_2.addWidget(self.button_obey)
        self.vbox_2.addWidget(self.main_plot)
        self.dock_widget_2_content.setLayout(self.vbox_2)
        self.dock_widget_2.setWidget(self.dock_widget_2_content)

        self.dock_widget_2.setFloating(False)
        self.dock_widget_2.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.dock_widget_2.setAllowedAreas(Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_widget_2)

    def set_all_in_some_layout(self):
        #addWidget (self, QWidget, row, column, rowSpan, columnSpan, Qt.Alignment alignment = 0)
        grid_layout = QGridLayout()

        grid_layout.addWidget(self.scroll_area, 0, 0, 1, 1)
        #todo setting widgets in a way to set other widgets too in the GUI
        #enable code and the dockable widgets will not move.
        #grid_layout.addWidget(self.dock_widget_1, 0, 1, 1, 1)

        #grid_layout.addWidget(self.dock_widget_2, 0, 1, 1, 1)

        self.central_widget = PyQt5.QtWidgets.QWidget()
        self.central_widget.setLayout(grid_layout)
        self.setCentralWidget(self.central_widget)

    def initUI(self):
        self.set_dock_widget_1()
        self.set_dock_widget_2()
        self.set_scroll_area()

        self.set_menu_bar()
        #self.get_status_open_or_closed()

        self.set_all_in_some_layout()
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())