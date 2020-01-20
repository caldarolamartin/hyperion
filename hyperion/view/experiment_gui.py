



import importlib
import random
import string
import sys
import os
from hyperion import logging
import pyqtgraph as pg
from PyQt5.QtCore import *
from PyQt5.QtGui import *
# from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDockWidget, QPushButton, QVBoxLayout, QAction
from PyQt5.QtWidgets import *
from examples.example_experiment import ExampleExperiment
import traceback
import yaml
from hyperion.tools.loading import get_class


import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.console
import numpy as np

from pyqtgraph.dockarea import DockArea, Dock

class ExpGui(QMainWindow):

    def __init__(self, experiment):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating ExpGui object')

        # sys.excepthook = self.excepthook  # This is very handy in case there are exceptions that force the program to quit.

        self.experiment = experiment
        self._config_file = None
        # Create central pyqtgraph dock area for graphics outputs
        self.plot_area= DockArea()
        self.setCentralWidget(self.plot_area)

        # # Turn the central widget into a QMainWindow which gives more docking possibilities
        # self.setDockOptions(QMainWindow.AllowTabbedDocks)



        self.instrument_guis = {}  # dictionary to hold the instrument guis (including meta instruments)
        self.measurement_guis = {}  # dictionary to hold the measurement guis (both manual and automatic)
        self.visualization_guis = {}
        self.output_guis = {}

        # NOTE:
        # I think it might sometimes make sense to re-use the graph window of an instrument for measurement outputs
        # how to give a measurement access to those plotwindows
        # AND how to do plottin in the first place
        # WHO does the updating? should be different thread from actual measurement!
        # The BaseMeasurementGui runs a thread that runs the experiment
        #  that same BaseMeasurementGui could be updating graphs
        # How about: an action can have a _graph key, which will tell the masergui what graph to load and to update
        # the updating is kind of still done in the experiment:
        #   when the "plot_method" is executed, a flag with new plot data availalble is set
        #   and

        # MAYBE, the masterGui or a measruement should have a PlotManager
        # One would add "plots" with:
        #   the gui to use
        #   the data variable to grab
        #   the update type (regular interval, or by available_flag)    e.g. positive is ms, 0 is once (, negative values is ms how often to check for flag
        # flag
        #
        # When the measurement starts, the plotmanager "starts" and keeps checking for


        self.resize(1000,500)
        self.setWindowTitle(self.experiment.display_name)


        self.logger.debug('Creating Menubar')
        self.set_menu_bar()

        self.logger.debug('Loading instrument guis (if experiment already has instruments)')
        self.load_all_instrument_guis()


        self.logger.debug('Creating Example graphs')
        self.example()


    def set_menu_bar(self):
        """"
        In this method the menubar of the gui is created and filled with
        menu's and menu's are filled with actions. The actions of edgeDockMenu and centralDockMenu
        are filled in randomDockWindow method.
        """
        mainMenu = self.menuBar()
        self.fileMenu = mainMenu.addMenu('&File')
        self.fileMenu.addAction("&Load Config File", self.load_config)
        self.fileMenu.addAction("&Modify Config File", self.modify_config)
        self.fileMenu.addAction("&Reconnect Instruments", self.reconnect_instruments)
        self.fileMenu.addAction("&Quit", self.close)
        self.measurement_menu = mainMenu.addMenu('&Measurements')

        self.instrument_menu = mainMenu.addMenu('&Instruments')
        # for inst_name, inst_gui_obj in self.instrument_guis.items():
        #     # add the menu item to the view object:
        #     inst_gui_obj._menu_action = self.instrument_menu.addAction(inst_name)
        #     inst_gui_obj._menu_action.setCheckable(True)
        #     inst_gui_obj._menu_action.setChecked(True)
        #     inst_gui_obj._menu_action.triggered.connect(lambda state, x=inst_name: self.hide_show_outut_gui(state, x))


        self.instrument_graph_menu = mainMenu.addMenu('Graph windows')
        self.measurement_graph_menu = mainMenu.addMenu('Measurement graph windows')

        self.toolsMenu = mainMenu.addMenu('Tools')
        # self.toolsMenu.addAction("Let widget 1 disappear", self.get_status_open_or_closed)
        # self.toolsMenu.addAction("Make widget", self.create_single_qdockwidget)

        self.helpMenu = mainMenu.addMenu('Help')

    # def hide_show_outut_gui(self, state, inst_name, start_hidden=False):
    #     print(state)
    #     print(inst_name)
    #     if self.instrument_guis[inst_name].isVisible():
    #         self.instrument_guis[inst_name]._menu_action.setChecked(False)
    #         self.instrument_guis[inst_name].setVisible(False)
    #     else:
    #         self.instrument_guis[inst_name]._menu_action.setChecked(True)
    #         self.instrument_guis[inst_name].setVisible(True)
    #         # obj=QWidget()

    def load_all_instrument_guis(self):
        # clear gui dicts
        self.instrument_gui_outputs = {}
        self.instrument_guis = {}
        for name in self.experiment.instruments_instances:
            self.load_instrument_gui(name)

    def load_visualization_gui(self, vis_name):
        if vis_name in self.visualization_guis:
            return self.visualization_guis[vis_name]
        if vis_name in self.experiment.properties['VisualizationGuis']:
            vis_dict = self.experiment.properties['VisualizationGuis'][vis_name]
            plotargs = {}
            if 'plotargs' in vis_dict:
                plotargs = vis_dict['plotargs']
            vis_cls = get_class(vis_dict['view'])
            vis_inst = vis_cls(**plotargs)
            dock = Dock(name=vis_name)
            dock.addWidget(vis_inst)
            self.plot_area.addDock(dock)
            self.visualization_guis[vis_name] = dock
            return vis_inst
        return None


    def load_instrument_gui(self, inst_name):
        # assumes the instrument exists (intended to be called by load_all_instrument_guis)
        instr_inst = self.experiment.instruments_instances[inst_name]
        conf_dict = self.experiment.properties['Instruments'][inst_name]
        vis_gui_instances = {}
        out_view_instance = None
        if 'visualization_guis' in conf_dict and 'VisualizationGuis' in self.experiment.properties:
            for vis_gui_name in conf_dict['visualization_guis']:
                vis_inst = self.load_visualization_gui(vis_gui_name)
                if vis_inst is not None:
                    vis_gui_instances[vis_gui_name] = vis_inst
        elif 'graphView' in conf_dict:
            out_view = conf_dict['graphView']
            if type(out_view) is str:
                plotargs = {}
                if 'plotargs' in conf_dict:
                    plotargs = conf_dict['plotargs']
                out_view_class = get_class(out_view)
                out_view_instance = out_view_class(**plotargs)
                new_name = '{} (instr)'.format(inst_name)
                dock = Dock(name=new_name)
                dock.addWidget(out_view_instance)
                self.plot_area.addDock(dock)
                self.visualization_guis[new_name] = dock
        if 'view' in conf_dict:
            inst_view = conf_dict['view']
            if type(inst_view) is str:
                inst_view_class = get_class(inst_view)
                if vis_gui_instances:
                    inst_view_instance = inst_view_class(instr_inst, vis_gui_instances)
                elif out_view_instance:
                    inst_view_instance = inst_view_class(instr_inst, out_view_instance)
                else:
                    inst_view_instance = inst_view_class(instr_inst)
                self.instrument_guis[inst_name] = inst_view_instance

                # self.logger.debug('Adding Instrument gui: {}'.format(inst_name))
                # # dock, name = self.setting_standard_dock_settings('test 1')
                # dock = QDockWidget(inst_name)
                # dock.setWidget(inst_view_instance)
                # dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
                # act = self.instrument_menu.addAction(inst_name, lambda d=dock: d.close() if d.isVisible() else d.setVisible(True))
                # act.setCheckable(True)
                # dock.visibilityChanged.connect(act.setChecked)
                # self.addDockWidget(Qt.RightDockWidgetArea, dock)



                if out_view_instance is not None:
                    self.logger.debug('Adding Instrument output gui: {}'.format(inst_name))
                    dock = Dock(name=inst_name)
                    dock.addWidget(out_view_instance)
                    self.plot_area.addDock(dock)
                    self.instrument_gui_outputs[inst_name] = dock


    def load_all_measurement_guis(self):
        for meas_name in self.experiment.properties['Measurements']:
            self.load_measurement_gui(meas_name)

    def load_measurement_gui(self, meas_name):
        meas_dict = self.experiment.properties['Measurements'][meas_name]
        if 'view' in meas_dict:
            # Check if required instruments are available
            if 'required_instruments' in meas_dict:
                missing_instr = [instr_name for instr_name in meas_dict['required_instruments'] if instr_name not in self.experiment.instruments_instances]
                if missing_instr:
                    for instr in missing_instr:
                        self.logger.error('Missing instrument {} for measurement {}'.format(instr, meas_name))
                    return
            # First create visualization output guis
            output_guis = {}
            if 'visualization_guis' in meas_dict:
                for output_gui_name, load_srt in meas_dict[output_guis].items():
                    output_guis[output_gui_name]



    def load_config(self):
        # folder, basename = self.experiment._validate_folder_basename(self.actiondict)
        # self._config_file gets updated on successful load of yaml

        temp = os.path.join(hyperion.repository_path, 'examples', 'example_project_with_automated_scanning',
                                   'my_experiment.yml')
        fname = QFileDialog.getOpenFileName(self, 'Save data as', temp,
                                            filter="YAML (*.yml);;All Files (*.*)")
        # If cancel was pressed, don't change the folder and file
        if fname[0] == '':
            return
        try:
            self.experiment.load_config(fname[0])
            self._config_file = fname[0]
        except:
            self.logger.warning('Failed to load YAML config file.')
            QMessageBox.warning(self, 'Loading config failed', "Perhaps invalid YAML?", QMessageBox.Ok)
            return
        self.reconnect_instruments(dialog=False)

    def reconnect_instruments(self, dialog=True):
        if dialog:
            buttonReply = QMessageBox.question(self, 'Reconnect to all instruments', "Are you sure you want to close and re-open all instruments?",
                                               QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Yes)
            if buttonReply == QMessageBox.Cancel:
                return
        if not 'Instruments' in self.experiment.properties:
            QMessageBox.warning(self, 'No instruments specified', "No config loaded or no instruments listed in config file.", QMessageBox.Ok)
            return
        try:
            self.logger.debug('Closing open instruments')
            self.experiment.close_all_instruments()
            self.logger.debug('Loading all instruments in config')
            self.experiment.load_instruments()
        except:
            self.logger.warning('Error while loading instruments')
            QMessageBox.warning(self, 'Loading instruments failed', "Perhaps a device is not connected or it's still in use by another process?", QMessageBox.Ok)
            self.logger.debug('Closing open instruments')
            self.experiment.load_instruments()
        for inst in self.experiment.instruments_instances:
            inst_dict = self.experiment.properties['Instruments'][inst]
            # if inst in
        self.load_all_instrument_guis()

    def modify_config(self):
        dlg = ModifyConfigFile(self._config_file, self.experiment, self)
        dlg.exec_()


    def example(self):

        ## Create docks, place them into the window one at a time.
        ## Note that size arguments are only a suggestion; docks will still have to
        ## fill the entire dock area and obey the limits of their internal widgets.
        d1 = Dock("Dock1", size=(1, 1))     ## give this dock the minimum possible size
        d2 = Dock("Dock2 - Console", size=(500,300), closable=True)
        d3 = Dock("Dock3", size=(500,400))
        d4 = Dock("Dock4 (tabbed) - Plot", size=(500,200))
        d5 = Dock("Dock5 - Image", size=(500,200))
        d6 = Dock("Dock6 (tabbed) - Plot", size=(500,200))
        self.plot_area.addDock(d1, 'left')      ## place d1 at left edge of dock area (it will fill the whole space since there are no other docks yet)
        self.plot_area.addDock(d2, 'right')     ## place d2 at right edge of dock area
        self.plot_area.addDock(d3, 'bottom', d1)## place d3 at bottom edge of d1
        self.plot_area.addDock(d4, 'right')     ## place d4 at right edge of dock area
        self.plot_area.addDock(d5, 'left', d1)  ## place d5 at left edge of d1
        self.plot_area.addDock(d6, 'top', d4)   ## place d5 at top edge of d4

        ## Test ability to move docks programatically after they have been placed
        self.plot_area.moveDock(d4, 'top', d2)     ## move d4 to top edge of d2
        self.plot_area.moveDock(d6, 'above', d4)   ## move d6 to stack on top of d4
        self.plot_area.moveDock(d5, 'top', d2)     ## move d5 to top edge of d2


        ## Add widgets into each dock

        ## first dock gets save/restore buttons
        w1 = pg.LayoutWidget()
        label = QtGui.QLabel(""" -- DockArea Example -- 
        This window has 6 Dock widgets in it. Each dock can be dragged
        by its title bar to occupy a different space within the window 
        but note that one dock has its title bar hidden). Additionally,
        the borders between docks may be dragged to resize. Docks that are dragged on top
        of one another are stacked in a tabbed layout. Double-click a dock title
        bar to place it in its own window.
        """)
        saveBtn = QtGui.QPushButton('Save dock state')
        restoreBtn = QtGui.QPushButton('Restore dock state')
        restoreBtn.setEnabled(False)
        w1.addWidget(label, row=0, col=0)
        w1.addWidget(saveBtn, row=1, col=0)
        w1.addWidget(restoreBtn, row=2, col=0)
        d1.addWidget(w1)
        state = None
        def save():
            global state
            state = self.plot_area.saveState()
            restoreBtn.setEnabled(True)
        def load():
            global state
            self.plot_area.restoreState(state)
        saveBtn.clicked.connect(save)
        restoreBtn.clicked.connect(load)


        w2 = pg.console.ConsoleWidget()
        d2.addWidget(w2)

        ## Hide title bar on dock 3
        d3.hideTitleBar()
        w3 = pg.PlotWidget(title="Plot inside dock with no title bar")
        w3.plot(np.random.normal(size=100))
        d3.addWidget(w3)

        w4 = pg.PlotWidget(title="Dock 4 plot")
        w4.plot(np.random.normal(size=100))
        d4.addWidget(w4)

        w5 = pg.ImageView()
        w5.setImage(np.random.normal(size=(100,100)))
        d5.addWidget(w5)

        w6 = pg.PlotWidget(title="Dock 6 plot")
        w6.plot(np.random.normal(size=100))
        d6.addWidget(w6)



        self.show()

    def excepthook(self, etype, value, tb):
        """This is what it gets executed when there is an error. Here we build an
        error dialog box

        """
        self.logger.error('An error occurred. NameError: {} '.format(value))
        self.error_dialog(etype, value, tb)

    def error_dialog(self, etype, value, tb):
        """ Builds an error dialog box that pops up when there is an error. It shows the error in the details.
        It has two buttons: Ignore and Abort. Ignore continues and Abort closes

        """
        traceback.print_exception(etype, value, tb) # this prints the error in the terminal.
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)

        msg.setText("There was an error. \n Press Ignore or (x) to continue and Abort to exit the GUI.")
        msg.setWindowTitle("Error Box")
        text = ''
        for a in traceback.format_exception(etype, value, tb):
            text += '{}'.format(a)

        msg.setDetailedText("{}".format(text))
        msg.setStandardButtons(QMessageBox.Ignore | QMessageBox.Abort)
        msg.setDefaultButton(QMessageBox.Abort)
        msg.setEscapeButton(QMessageBox.Ignore)
        msg.buttonClicked.connect(self.__error_dialog_btn)
        msg.exec_()

    def __error_dialog_btn(self, i):
        """ Function that decides what to do when you press the buttons in the error dialog box.

        :param i: event when the QMessageBox buttons are pressed

        """
        self.logger.debug("Button pressed is: {}".format(i.text()))
        if i.text() == 'Abort':
            self.close() # to close the Qwidget


# ## Start Qt event loop unless running in interactive mode or using pyside.
# if __name__ == '__main__':
#     import sys
#     if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#         QtGui.QApplication.instance().exec_()


class ModifyConfigFile(QDialog):


    # original
    # save
    # save and load
    # load only
    # cancel


    def __init__(self, filename, experiment, parent=None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating ModifyMeasurement window')
        super().__init__(parent)
        self.font = QFont("Courier New", 11)
        self.experiment = experiment
        self.initUI()
        self.filename = self.readfile(filename)
        self.reset()

    def readfile(self, fname):
        if type(fname) is str and os.path.isfile(fname):
            try:
                with open(fname ,'r') as f:
                    self.text = f.read()
                    return fname
            except:
                pass
        self.text = ''
        return None

    def initUI(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid = QGridLayout()
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        # create buttons, lables and the textedit:
        self.button_open = QPushButton('&Open', clicked=self.open)
        self.button_reset = QPushButton('&Reset', clicked = self.reset)
        self.button_save = QPushButton('&Save As', clicked = self.save)
        self.button_save_apply = QPushButton('Sa&ve As && Apply', clicked = self.save_apply)
        self.button_apply = QPushButton('&Apply', clicked = self.apply)
        self.button_cancel = QPushButton('&Cancel', clicked = self.close)
        self.txt = QTextEdit()
        self.txt.setLineWrapMode(QTextEdit.NoWrap)
        self.txt.setFont(self.font)
        self.txt.textChanged.connect(self.changed)
        # add all widgets to the layout:
        # grid.addWidget(self.txt, 0, 0, 1, 5)

        button_layout.addWidget(self.button_open)
        button_layout.addWidget(self.button_reset)
        button_layout.addWidget(self.button_save)
        button_layout.addWidget(self.button_save_apply)
        button_layout.addWidget(self.button_apply)
        button_layout.addWidget(self.button_cancel)
        main_layout.addWidget(self.txt)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def folder_suggestion(self):
        folder = None
        if self.filename:
            folder = os.path.dirname(self._filename)
        if not folder or not os.path.isdir(folder):
            folder = hyperion.parent_path
        return folder

    def open(self):
        fname = QFileDialog.getOpenFileName(self, 'Open File', self.folder_suggestion(),
                                        filter="YAML (*.yml);;All Files (*.*)")
        if fname[0]:
            self.filename = self.readfile(fname[0])
            self.readfile(self.filename)
            self.reset()

    def changed(self):
        self._modified = True
        self.button_reset.setEnabled(True)
        self.button_save.setEnabled(True)
        # self.button_save_apply.setEnabled(True)
        self.button_apply.setEnabled(True)

    def reset(self):
        self.txt.setText(self.text)
        self._modified = False
        self.button_reset.setEnabled(False)
        self.button_save.setEnabled(False)
        # self.button_save_apply.setEnabled(False)
        self.button_apply.setEnabled(False)
        #
        # self._doc = yaml.dump(self._original_list, indent=self._indent)
        # self.txt.setPlainText(self._doc)
        # self.clear_labels()
        # self.validate()
        # self._current_doc = 1
        # self.update_buttons()

    def valid_yaml(self):
        try:
            self._list = yaml.safe_load(self.txt.toPlainText())
            # print(self.txt.toPlainText())
            return True
        except yaml.YAMLError as exc:
            QMessageBox.warning(self, 'Invalid YAML', str(exc), QMessageBox.Ok)
            return False



    def save(self, keep_open=False):
        if self.valid_yaml():
            if type(self.filename) is str and os.path.isfile(self.filename):
                suggest = self.filename
            else:
                suggest = self.folder_suggestion()
            fname = QFileDialog.getSaveFileName(self, 'Save File', suggest,
                                                filter="YAML (*.yml);;All Files (*.*)")
            if fname[0]:
                try:
                    with open(fname[0], 'w') as f:
                        f.write(self.txt.toPlainText())
                        self.filename = fname[0]
                except Exception as e:
                    QMessageBox.warning(self, 'Failed to write to file', str(a), QMessageBox.Ok)
                    return False
                if keep_open:
                    return True
                else:
                    self.close()
        else:
            return False

    def save_apply(self):
        if self.save(keep_open=True):
            try:
                self.logger.debug('Closing instruments, loading new yaml file and loading instruments')
                self.experiment.close_all_instruments()
                self.experiment.load_config(self.filename)
                self.experiment.load_instruments()
                self.close()
            except:
                self.logger.error('Failed to load config and instruments from new file')
                QMessageBox.warning(self, 'Error', 'Error while applying config or loading instruments', QMessageBox.Ok)
                return

    def apply(self):
        if self.valid_yaml():
            try:
                self.logger.debug('Converting text to dictionary')
                dic = yaml.safe_load(self.txt.toPlainText())
                if type(dic) is not dict:
                    raise
            except:
                self.logger.error('Converting text to dictionary failed')
                QMessageBox.warning(self, 'Reading YAML failed', 'Error while converting yaml to dictionary', QMessageBox.Ok)
                return
            try:
                self.logger.debug('Closing instruments, loading dict as config and loading instruments')
                self.experiment.close_all_instruments()
                self.experiment.load_config('_manually_modified_yaml_', dic)
                self.experiment.load_instruments()
                self.close()
            except:
                self.logger.error('Failed to load config and instruments from dict')
                QMessageBox.warning(self, 'Error', 'Error while applying config or loading instruments', QMessageBox.Ok)
                return



if __name__ == '__main__':
    import hyperion
    from examples.example_project_with_automated_scanning.my_experiment import MyExperiment

    # logger = logging.getLogger(__name__)

    config_file = os.path.join(hyperion.repository_path, 'examples', 'example_project_with_automated_scanning', 'my_experiment.yml')

    logging.stream_level = logging.WARNING
    experiment = MyExperiment()
    logging.stream_level = logging.DEBUG
    experiment.load_config(config_file)
    experiment.load_instruments()

    app = QApplication(sys.argv)
    main_gui = ExpGui(experiment)
    # sys.exit(app.exec_())
    app.exec_()