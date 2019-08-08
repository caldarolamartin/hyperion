import importlib
import random
import string
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDockWidget, QListWidget, QTextEdit, QPushButton, \
    QGraphicsView, QAction, QLineEdit, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout
import pyqtgraph as pg
from examples.example_experiment import ExampleExperiment

class App(QMainWindow):

    def __init__(self, experiment):
        super().__init__()
        self.title = 'PyQt5 simple window'
        self.left = 40
        self.top = 40
        self.width = 800
        self.height = 500
        self.button_pressed = False
        self.experiment = experiment

        self.setWindowTitle("Dock demo")

        self.initUI()

    def set_gui_specifics(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        _DOCK_OPTS = QMainWindow.AllowTabbedDocks
        # _DOCK_OPTS |= QMainWindow.AllowNestedDocks         # Dit kan evt aan
        # _DOCK_OPTS |= QMainWindow.AnimatedDocks            # Ik weet niet wat dit toevoegt

        # Turn the central widget into a QMainWindow with more docking
        self.central = QMainWindow()
        self.central.setWindowFlags(Qt.Widget)
        self.central.setDockOptions(_DOCK_OPTS)
        self.setCentralWidget(self.central)

    def set_menu_bar(self):
        mainMenu = self.menuBar()
        self.fileMenu = mainMenu.addMenu('File')
        self.fileMenu.addAction("Exit NOW", self.close)
        self.edgeDockMenu = mainMenu.addMenu('Edge Dock windows')
        self.centralDockMenu = mainMenu.addMenu('Central Dock Windows')

        self.draw_something = mainMenu.addMenu('draw')
        self.draw_something.addAction("Draw", self.draw_random_graph)

        self.toolsMenu = mainMenu.addMenu('Tools')
        self.toolsMenu.addAction("Let widget 1 disappear", self.get_status_open_or_closed)
        self.toolsMenu.addAction("Make widget", self.create_single_qdockwidget)

        self.helpMenu = mainMenu.addMenu('Help')


    def get_status_open_or_closed(self):
        self.dock_widget_dict["dock_1_ariel"].setVisible(not self.dock_widget_dict["dock_1_ariel"].isVisible())
    def create_single_qdockwidget(self):
        #in this method the goal is to create a blank QDockwidget and set in the main_gui
        if self.button_pressed == False:
            self.random_widget = QDockWidget("some_widget",self)

            self.random_widget.setFloating(False)

            self.random_widget.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
            self.random_widget.setAllowedAreas(Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)

            self.addDockWidget(Qt.TopDockWidgetArea, self.random_widget)

            self.button_pressed = True

    def draw_random_graph(self):
        self.ydata = [random.random() for i in range(25)]
        self.xdata = [random.random() for i in range(25)]
        self.random_plot.plot(self.xdata, self.ydata, clear=True)

    def make_automatic_dock_widgets(self):
        lijst_met_dock_widget = ["dock_1_ariel", "dock_2_ariel", "dock_3_ariel", "dock_4_ariel", "dock_5_ariel", "dock_6_ariel",
                                 "central_dock_1_ariel", "central_dock_2_ariel", "central_dock_3_ariel", "central_dock_4_ariel"]
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

    def randomString(self, N):
        return ''.join([random.choice(string.ascii_lowercase) for n in range(N)])
    def randomDockWindow(self, menu, name=None):
        if name == None:
            name = self.randomString(7)
        dock = QDockWidget(name, self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        if name == "dock_1_ariel":
            dock.setWidget(self.experiment.view_instances["ExampleInstrument"])
        elif name == "dock_2_ariel":
            dock.setWidget(self.experiment.view_instances["OsaInstrument"])
        elif name == "dock_3_ariel":
            dock_widget_content = QWidget()
            vbox = QVBoxLayout()
            self.random_plot = pg.PlotWidget()
            vbox.addWidget(self.random_plot)
            dock_widget_content.setLayout(vbox)
            dock.setWidget(dock_widget_content)

        else:
            string_list = [self.randomString(5) for n in range(5)]
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


    def set_dock_widget_2(self):
        """
        Old code needed to have an example of how to add a QdockWidget by hand.
        For the rest, it is not needed.
        :return:
        """
        """
                how to add Qobjects to a dockable goes as follows.
                First you make a Qwidget where the content will be placed in. Call this things something with content in the name
                Then define the Qobjects you want to make
                Finally, you choose a layout((maybe absolute positioning is possible,
                haven't seen it in examples so it is not implemented in this code)QVBoxLayout, QHBoxLayout and QGridLayout)
                then you add the layout to the content widget and lastly you set the beginning Qwhatever as the widget of the dockwidget.

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
                """
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

    def get_view_instances_and_load_instruments(self):
        # name = 'example_experiment_config'
        # config_folder = os.path.dirname(os.path.abspath(__file__))
        # config_file = os.path.join(config_folder, name)

        self.experiment.load_config('C:\\Users\\ariel\\Desktop\\Delft_code\\hyperion\\examples\\example_experiment_config.yml')
        self.experiment.load_instruments()
        self.load_interfaces()
    def load_interfaces(self):
        #method to get an instance of a grafical interface to set in the master gui.
        self.ins_bag = {}

        for instrument in self.experiment.properties['Instruments']:
            if not instrument == 'VariableWaveplate':
                #get the right name
                self.ins_bag[instrument] = self.load_gui(instrument)
    def load_gui(self, name):
        """ Loads gui's

        :param name: name of the instrument to load. It has to be specified in the config file under Instruments
        :type name: string
        """
        try:
            dictionairy = self.experiment.properties['Instruments'][name]
            module_name, class_name = dictionairy['view'].split('/')
            MyClass = getattr(importlib.import_module(module_name), class_name)
            #instr is variable that will be the instrument name of a device. For example: OsaInstrument.
            instr = ((dictionairy['instrument']).split('/')[1])
            #self.experiment.instruments_instances[instr] = the name of the instrument for a device. This is necessary
            #to communicate between instrument and view. Instance is still an instance of for example OsaView.
            instance = MyClass(self.experiment.instruments_instances[instr])
            self.experiment.view_instances[name] = instance
        except KeyError:
            print("the key(aka, your view/gui) does not exist in properties,\n meaning that it is not in the .yml file.")
            return None

    def initUI(self):
        self.set_gui_specifics()

        self.get_view_instances_and_load_instruments()

        self.set_menu_bar()

        self.make_automatic_dock_widgets()

        self.show()

if __name__ == '__main__':
    experiment = ExampleExperiment()

    app = QApplication(sys.argv)

    main_gui = App(experiment)

    sys.exit(app.exec_())