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

        #self.make_automatic_dock_widgets()

        self.dock1 = self.randomDockWindow(self.edgeDockMenu, 'Dock 1')
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock1)
        self.dock1.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.dock2 = self.randomDockWindow(self.edgeDockMenu, 'Dock 2')
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock2)
        self.dock2.setFeatures(QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetClosable )

        self.dock3 = self.randomDockWindow(self.edgeDockMenu, 'Dock 3')
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock3)

        self.dock4 = self.randomDockWindow(self.edgeDockMenu, 'Dock 4')
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock4)
        self.dock4.setFeatures(QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetMovable)

        self.dock5 = self.randomDockWindow(self.edgeDockMenu, 'Dock 5')
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock5)
        self.dock5.setFeatures(QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetFloatable)

        self.dock6 = self.randomDockWindow(self.edgeDockMenu, 'Dock 6')
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock6)

        self.central_dock1 = self.randomDockWindow(self.centralDockMenu, 'Central Dock 1')
        self.central.addDockWidget(Qt.LeftDockWidgetArea, self.central_dock1)

        self.central_dock2 = self.randomDockWindow(self.centralDockMenu, 'Central Dock 2')
        self.central.addDockWidget(Qt.LeftDockWidgetArea, self.central_dock2)

        self.central_dock3 = self.randomDockWindow(self.centralDockMenu, 'Central Dock 3')
        self.central.addDockWidget(Qt.RightDockWidgetArea, self.central_dock3)

        self.central_dock4 = self.randomDockWindow(self.centralDockMenu, 'Central Dock 4')
        self.central.addDockWidget(Qt.RightDockWidgetArea, self.central_dock4)

    def make_automatic_dock_widgets(self):
        """
        instrumenten = ["trompet", "piano", "gitaar"]
        self.ins_bag = {}
        opteller = 0
        for instrument in instrumenten:
            self.ins_bag[instrument] = opteller
            #self.instrument_naam = instrument
            print(self.ins_bag.items())
            print("-"*40)
            opteller +=1

        print(self.ins_bag.items())
        """
        lijst_met_dock_widget = ["dock_1","dock_2","dock_3","dock_4","dock_5","dock_6","dock_7","dock_8","dock_9","dock_10"]
        self.dock_widget_dict = {}
        opteller = 0
        for dock_widget in lijst_met_dock_widget:
            if opteller <=2:
                self.dock_widget_dict[dock_widget] = self.randomDockWindow(self.edgeDockMenu, dock_widget)
                self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget_dict[dock_widget])
                #self.dock_widget = self.randomDockWindow(self.edgeDockMenu, dock_widget)
                #self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)
            elif opteller > 2 and opteller <=5:
                self.dock_widget_dict[dock_widget] = self.randomDockWindow(self.edgeDockMenu, dock_widget)
                self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_dict[dock_widget])
                #self.dock_widget = self.randomDockWindow(self.edgeDockMenu, dock_widget)
                #self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
            elif opteller > 5 and opteller <= 6:
                self.dock_widget_dict[dock_widget] = self.randomDockWindow(self.centralDockMenu, dock_widget)
                self.central.addDockWidget(Qt.RightDockWidgetArea, dock_widget)
                #self.dock_widget = self.randomDockWindow(self.centralDockMenu, dock_widget)
                #self.central.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
            elif opteller > 6 and opteller <= 9:
                self.dock_widget_dict[dock_widget] = self.randomDockWindow(self.centralDockMenu, dock_widget)
                self.central.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)
            opteller += 1

    def dock2_menu(self):
        #self.dock2.toggleViewAction()
        self.dock2.setVisible(not self.dock2.isVisible())

    def randString(selfself,N):
        return ''.join([random.choice(string.ascii_lowercase) for n in range(N)])

    def randomDockWindow(self, menu, name=None):
        if name == None:
            name = self.randString(7)
        dock = QDockWidget(name, self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        string_list = [self.randString(5) for n in range(5)]
        listwidget = QListWidget(dock)
        listwidget.addItems(string_list)
        dock.setWidget(listwidget)
        dock.collapsed = False
        dock.collapsed_height = 22
        dock.uncollapsed_height = 200
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
        