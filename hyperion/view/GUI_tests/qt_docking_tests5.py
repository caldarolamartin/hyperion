from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QListWidget, QTextEdit, QPushButton
from PyQt5.QtCore import Qt
import sys

import random
import string

class Window(QMainWindow):

    def __init__(self):
        super().__init__()
        
        title = "Dockable Application"
        top = 100
        left = 400
        width = 1000
        height = 800

        self.setWindowTitle(title)
        self.setGeometry(left, top, width , height)

        _DOCK_OPTS = QMainWindow.AllowTabbedDocks
        #_DOCK_OPTS |= QMainWindow.AllowNestedDocks         # Dit kan evt aan
        #_DOCK_OPTS |= QMainWindow.AnimatedDocks            # Ik weet niet wat dit toevoegt

        # Turn the central widget into a QMainWindow with more docking
        self.central = QMainWindow()
        self.central.setWindowFlags(Qt.Widget)
        self.central.setDockOptions(_DOCK_OPTS)
        self.setCentralWidget(self.central)

        self.mainMenu = self.menuBar()
        self.fileMenu = self.mainMenu.addMenu('File')
        self.edgeDockMenu = self.mainMenu.addMenu('Edge Dock windows')
        self.centralDockMenu = self.mainMenu.addMenu('Central Dock Windows')

        self.make_automatic_dock_widgets()

    def make_automatic_dock_widgets(self):
        lijst_met_dock_widget = ["dock_1_ariel","dock_2_ariel","dock_3_ariel","dock_4_ariel","dock_5_ariel","dock_6_ariel",
                                 "central_dock_1_ariel","central_dock_2_ariel","central_dock_3_ariel","central_dock_4_ariel"]
        self.dock_widget_dict = {}
        opteller = 0
        for dock_widget in lijst_met_dock_widget:
            if opteller <=2:
                self.make_left_dock_widgets(dock_widget, opteller)
            elif opteller > 2 and opteller <=5:
                self.make_right_dock_widgets(dock_widget, opteller)
            elif opteller > 5 and opteller <= 7:
                self.make_central_right_dock_widgets(dock_widget, opteller)
            elif opteller > 7 and opteller <= 9:
                self.make_central_left_dock_widgets(dock_widget, opteller)
            opteller += 1
    def make_left_dock_widgets(self, dock_widget, opteller):
        self.dock_widget_dict[dock_widget] = self.randomDockWindow(self.edgeDockMenu, dock_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget_dict[dock_widget])
        if opteller == 0:
            self.dock_widget_dict[dock_widget].setFeatures(QDockWidget.NoDockWidgetFeatures)
        elif opteller == 1:
            self.dock_widget_dict[dock_widget].setFeatures(
                QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetClosable)
    def make_right_dock_widgets(self, dock_widget, opteller):
        self.dock_widget_dict[dock_widget] = self.randomDockWindow(self.edgeDockMenu, dock_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_dict[dock_widget])
        if opteller == 3:
            self.dock_widget_dict[dock_widget].setFeatures(
                QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetMovable)
        elif opteller == 4:
            self.dock_widget_dict[dock_widget].setFeatures(
                QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetFloatable)
    def make_central_right_dock_widgets(self, dock_widget, opteller):
        self.dock_widget_dict[dock_widget] = self.randomDockWindow(self.centralDockMenu, dock_widget)
        self.central.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_dict[dock_widget])
        if opteller == 6:
            self.dock_widget_dict[dock_widget].setFeatures(QDockWidget.NoDockWidgetFeatures)
    def make_central_left_dock_widgets(self, dock_widget, opteller):
        self.dock_widget_dict[dock_widget] = self.randomDockWindow(self.centralDockMenu, dock_widget)
        self.central.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget_dict[dock_widget])
        if opteller == 8:
            self.dock_widget_dict[dock_widget].setFeatures(QDockWidget.NoDockWidgetFeatures)

    def dock2_menu(self):
        self.dock2.setVisible(not self.dock2.isVisible())

    def randomString(selfself, N):
        return ''.join([random.choice(string.ascii_lowercase) for n in range(N)])

    def randomDockWindow(self, menu, name=None):
        if name == None:
            name = self.randomString(7)
        dock = QDockWidget(name, self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.collapsed = False
        dock.collapsed_height = 22
        dock.uncollapsed_height = 200
        string_list = [self.randomString(5) for n in range(5)]
        listwidget = QListWidget(dock)
        listwidget.addItems(string_list)
        dock.setWidget(listwidget)
        def toggle_visibility():
            dock.setVisible(not dock.isVisible())
        def toggle_collapsed():
            if not dock.collapsed:
                #dock.uncollapsed_height = dock.height()    # Haven't worked this out yet
                dock.setMinimumHeight(dock.collapsed_height)
                dock.setMaximumHeight(dock.collapsed_height)
                dock.collapsed = True
            else:
                dock.setMinimumHeight(dock.uncollapsed_height)
                dock.collapsed = False

        menu.addAction(name, toggle_collapsed)
        return dock
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec()
        