# import pyqtgraph.examples.dockarea



import importlib
import random
import string
import sys
import os
import hyperion
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
from hyperion.view.base_guis import AutoMeasurementGui

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

        # Add reference to this gui to the experiment object
        self.experiment._gui_parent = self

        self.statusBar().showMessage('Ready')

        self._config_file = None
        # Create central pyqtgraph dock area for graphics outputs
        self.plot_area= DockArea()
        self.setCentralWidget(self.plot_area)

        # # Turn the central widget into a QMainWindow which gives more docking possibilities
        # self.setDockOptions(QMainWindow.AllowTabbedDocks)



        self.instrument_guis = {}  # dictionary to hold the instrument guis (including meta instruments)
        self.measurement_guis = {}  # dictionary to hold the measurement guis (both manual and automatic)
        self.visualization_guis = {}

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


        # self.resize(1500,800)


        self.setWindowTitle(self.experiment.display_name)


        self.logger.debug('Creating Menubar')
        self.set_menu_bar()

        self.logger.debug('Loading instrument guis (if experiment already has instruments)')
        self.load_all_instrument_guis()

        self.logger.debug('Loading Measurement guis (if experiment already has measurement)')
        self.load_all_measurement_guis()


        # self.logger.debug('Creating Example graphs')
        # self.example()

        self.resize(1500,800)
        self.showMaximized()

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
        self.measurement_menu.addAction('&Show all', lambda: self._show_hide_all_qt(self.measurement_guis, show=True))
        self.measurement_menu.addAction('&Hide all', lambda: self._show_hide_all_qt(self.measurement_guis, show=False))
        self.measurement_menu.addSeparator()

        self.instrument_menu = mainMenu.addMenu('&Instruments')
        self.instrument_menu.addAction('&Show all', lambda: self._show_hide_all_qt(self.instrument_guis, show=True))
        self.instrument_menu.addAction('&Hide all', lambda: self._show_hide_all_qt(self.instrument_guis, show=False))
        self.instrument_menu.addSeparator()

        self.visualization_menu = mainMenu.addMenu('&Visualization')
        self.visualization_menu.addAction('&Show all', lambda: self._show_hide_all_plots(show=True))
        self.visualization_menu.addAction('&Hide all', lambda: self._show_hide_all_plots(show=False))
        self.visualization_menu.addSeparator()


        self.toolsMenu = mainMenu.addMenu('Tools')
        # self.toolsMenu.addAction("Let widget 1 disappear", self.get_status_open_or_closed)
        # self.toolsMenu.addAction("Make widget", self.create_single_qdockwidget)

        self.helpMenu = mainMenu.addMenu('Help')

        # When we build sphinx docs, we could add a link to open them in a browser
        self.helpMenu.addAction('&Documentation', lambda: print('Documentation is not implemented yet'))
        self.helpMenu.addAction('&PyQtGraph examples', self.__show_pyqtgraph_examples)
        self.helpMenu.addAction('&About', self.__about_dialog)

    def _show_hide_all_plots(self, show):
        for key, value in self.plot_area.docks.items():
            self.__hide_show_raise_pg_dock(value, show=show)
            value._menu_item.setChecked(show)

    def _show_hide_all_qt(self, gui_dict, show):
        for value in gui_dict.values():
            if show:
                value._dock.setVisible(True)
            else:
                value._dock.close()


    def lock_instruments(self, lock, measurement_name):
        """
        This method can be used by a measurement gui to stop or lock/disable instruments while measuring.
        Per instrument specify whether stop method should be run and if the gui of the instrument should be locked.

        :param instr_dict: keys should be instrument names, values are a dict {'stop': True, 'lock': False}
        """
        self.logger.debug(['un',''][lock]+'locking {}'.format(measurement_name))
        if 'required_instruments' in self.experiment.properties['Measurements'][measurement_name]:
            self.logger.debug('(un)locking required instruments of Measurement')
            for name, req_dict in self.experiment.properties['Measurements'][measurement_name]['required_instruments'].items():
                self.logger.debug('{}: {}'.format(name, req_dict))
                if name in self.instrument_guis:
                    # call stop if: lock AND req_dict['stop']==True AND if the gui has stop method
                    if lock and 'stop' in req_dict and req_dict['stop']:
                        instance = self.instrument_guis[name]
                        if hasattr(instance, 'stop'):
                            instance.stop()
                    # disable / enable according to lock if 'lock' in req_dict and True
                    if 'lock' in req_dict:
                        self.instrument_guis[name].setDisabled(req_dict['lock'] and lock)

    def load_all_instrument_guis(self):
        # clear gui dicts
        self.instrument_gui_outputs = {}
        self.instrument_guis = {}
        for inst_name in self.experiment.meta_instr_instances:
            self.load_meta_instrument_gui(inst_name)
        self.instrument_menu.addSeparator()
        for inst_name in self.experiment.instruments_instances:
            self.load_instrument_gui(inst_name)

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
            # dock.visibilityChanged.connect(act.setChecked)
            hidden = ('start_hidden' in vis_dict and vis_dict['start_hidden'])
            self.__add_vis_dock_to_menu(vis_name, vis_inst, self.visualization_menu, hidden)
            return vis_inst
        return None

    def __add_vis_dock_to_menu(self, name, pg_inst, menu, hidden=False):
        dock = Dock(name=name, closable=True)
        dock.addWidget(pg_inst)
        dock._is_closed = False  # add this flag for hiding/closing the graph
        self.plot_area.addDock(dock)
        # act = self.visualization_menu.addAction(name,
        #                                     lambda d=dock: d.setVisible(False) if d.isVisible() else d.setVisible(True))
        act = self.visualization_menu.addAction(name, lambda d=dock: self.__hide_show_raise_pg_dock(d))
        act.setCheckable(True)
        act.setChecked(not hidden)
        dock.setVisible(not hidden)
        # pg_inst._menu_item = act # add this reference here for possible deleting later
        dock._menu_item = act  # add this reference here for possible deleting later
        pg_inst._dock = dock
        pg_inst.show_dock = lambda show, d=dock: self.__hide_show_raise_pg_dock(d, show)
        dock.sigClosed.connect(lambda d=dock, a=act: self.__vis_dock_closed(d, a))
        # dock.visibilityChanged.connect(act.setChecked)
        self.visualization_guis[name] = pg_inst  # dock

    def __vis_dock_closed(self, dock, act):
        act.setChecked(False)
        dock.setVisible(False)
        dock._is_closed=True

    def __hide_show_raise_pg_dock(self, dock, show=None):
        if show is None:
            show = not dock.isVisible()
        if not show:
            dock.setVisible(False)
        else:
            dock.setVisible(True)
            if dock._is_closed:
                self.plot_area.addDock(dock)
                dock._is_closed = False
            # dock.raiseDock()
            dock._menu_item.setChecked(True)

    def load_instrument_gui(self, inst_name):
        # assumes the instrument exists (intended to be called by load_all_instrument_guis)
        instr_inst = self.experiment.instruments_instances[inst_name]
        conf_dict = self.experiment.properties['Instruments'][inst_name]
        self.__load_instr_gui(inst_name, instr_inst, conf_dict)

    def load_meta_instrument_gui(self, inst_name):
        # assumes the MetaInstrument exists (intended to be called by load_all_instrument_guis)
        instr_inst = self.experiment.meta_instr_instances[inst_name]
        conf_dict = self.experiment.properties['MetaInstruments'][inst_name]
        self.__load_instr_gui(inst_name, instr_inst, conf_dict)

    def __load_instr_gui(self, inst_name, instr_inst, conf_dict):
        # Shared helper function for load_instrument_gui() and load_meta_instrument_gui()
        vis_gui_instances = {}
        out_view_instance = None
        if 'visualization_guis' in conf_dict and 'VisualizationGuis' in self.experiment.properties:
            for vis_gui_name in conf_dict['visualization_guis']:
                vis_inst = self.load_visualization_gui(vis_gui_name)
                if vis_inst is not None:
                    vis_gui_instances[vis_gui_name] = vis_inst  # for passing to instrument view object
        elif 'graphView' in conf_dict:
            out_view = conf_dict['graphView']
            if type(out_view) is str:
                plotargs = {}
                if 'plotargs' in conf_dict:
                    plotargs = conf_dict['plotargs']
                out_view_class = get_class(out_view)
                out_view_instance = out_view_class(**plotargs)
                new_name = '{} (instr)'.format(inst_name)
                hidden = ('start_hidden' in conf_dict and conf_dict['start_hidden'])
                self.__add_vis_dock_to_menu(new_name, out_view_instance, self.visualization_menu, hidden)
        if 'view' in conf_dict:
            inst_view = conf_dict['view']
            if type(inst_view) is str:
                inst_view_class = get_class(inst_view)
                if vis_gui_instances:
                    instr_view_instance = inst_view_class(instr_inst, vis_gui_instances, also_close_output=False)
                elif out_view_instance:
                    instr_view_instance = inst_view_class(instr_inst, out_view_instance, also_close_output=False)
                else:
                    instr_view_instance = inst_view_class(instr_inst, also_close_output=False)
                self.instrument_guis[inst_name] = instr_view_instance

                self.logger.debug('Adding Instrument gui: {}'.format(inst_name))
                self.__add_qt_dock_to_menu(inst_name, instr_view_instance, self.instrument_menu, Qt.RightDockWidgetArea)
                if 'start_hidden' in conf_dict and conf_dict['start_hidden']:
                    instr_view_instance._dock.close()
                    instr_view_instance._menu_item.setChecked(False)

    def __add_qt_dock_to_menu(self, name, instance, menu, dock_area):
        # helper function for
        dock = QDockWidget(name)
        dock.setWidget(instance)
        dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(dock_area, dock)
        # act = menu.addAction(name,
        #                                      lambda d=dock: d.close() if d.isVisible() else d.setVisible(True))
        act = menu.addAction(name, lambda d=dock: self.__hide_show_raise_dock(d))
        act.setCheckable(True)
        act.setChecked(True)
        instance._menu_item = act # add this reference here for possible deleting later
        instance._dock = dock
        dock.visibilityChanged.connect(act.setChecked)

    def __hide_show_raise_dock(self, dock):
        if dock.isVisible():
            dock.close()
        else:
            dock.setVisible(True)
            dock.raise_()

    def load_all_measurement_guis(self):
        if 'Measurements' in self.experiment.properties:
            for meas_name in self.experiment.properties['Measurements']:
                self.load_measurement_gui(meas_name)

    def load_measurement_gui(self, meas_name):
        meas_dict = self.experiment.properties['Measurements'][meas_name]
        if 'view' in meas_dict:
            meas_class = get_class(meas_dict['view'])
            # Check if required instruments are available
            if 'required_instruments' in meas_dict:
                missing_instr = [instr_name for instr_name in meas_dict['required_instruments'] if instr_name not in self.experiment.instruments_instances]
                if missing_instr:
                    for instr in missing_instr:
                        self.logger.error('Missing instrument {} for measurement {}'.format(instr, meas_name))
                    return
            # First create visualization output guis
            vis_gui_instances = {}
            if 'visualization_guis' in meas_dict:
                # for output_gui_name, load_srt in meas_dict[output_guis].items():
                #     output_guis[output_gui_name]
                for vis_gui_name in meas_dict['visualization_guis']:
                    vis_inst = self.load_visualization_gui(vis_gui_name)
                    if vis_inst is not None:
                        vis_gui_instances[vis_gui_name] = vis_inst  # for apssing to measurement view object
            if vis_gui_instances:
                meas_instance = meas_class(self.experiment, meas_name, parent=self, output_guis=vis_gui_instances)
            else:
                meas_instance = meas_class(self.experiment, meas_name, parent=self)
            self.measurement_guis[meas_name] = meas_instance
            self.__add_qt_dock_to_menu(meas_name, meas_instance, self.measurement_menu, Qt.LeftDockWidgetArea)
            if 'start_hidden' in meas_dict and meas_dict['start_hidden']:
                meas_instance._dock.close()
                meas_instance._menu_item.setChecked(False)

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
        self.load_all_measurement_guis()

    def reconnect_instruments(self, dialog=True):
        if dialog:
            buttonReply = QMessageBox.question(self, 'Reconnect to all instruments',
                                               "Are you sure you want to close and re-open all instruments?\n"
                                               "Note that this functionality might not work properly yet.",
                                               QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Yes)
            if buttonReply == QMessageBox.Cancel:
                return
        self.remove_all_instrument_guis()
        if not 'Instruments' in self.experiment.properties:
            QMessageBox.warning(self, 'No instruments specified', "No config loaded or no instruments listed in config file.", QMessageBox.Ok)
            return
        try:
            self.experiment.remove_all_instruments()
        except:
            self.logger.warning('Error while removing instruments')
        try:
            self.experiment.load_instruments()  # this loads both regular and meta instruments
        except:
            self.logger.warning('Error while loading instruments')
            QMessageBox.warning(self, 'Loading instruments failed', "Perhaps a device is not connected or it's still in use by another process?", QMessageBox.Ok)
            self.logger.debug('Closing open instruments')
            self.experiment.load_instruments()
        for inst in self.experiment.instruments_instances:
            inst_dict = self.experiment.properties['Instruments'][inst]
            # if inst in
        self.load_all_instrument_guis()

    def remove_all_instrument_guis(self):
        """
        """
        # remove visualization guis that are not in VisualizationGuis and remove entry from Visualization menu
        keys = list(self.visualization_guis.keys())
        for name in keys:
            if name not in self.experiment.properties['VisualizationGuis']:
                try:
                    self.visualization_menu.removeAction(self.visualization_guis[name]._menu_item)
                    self.visualization_guis[name]._dock.close()
                    self.visualization_guis[name]._dock.setParent(None)
                    del self.visualization_guis[name]._dock
                    self.visualization_guis[name].close()
                    self.visualization_guis[name].setParent(None)
                    del self.visualization_guis[name]
                except:
                    pass
        # remove the instrument guis and remove entry from Instrument menu
        keys = list(self.instrument_guis.keys())
        for name in keys:
            try:
                self.instrument_menu.removeAction(self.instrument_guis[name]._menu_item)
                self.instrument_guis[name]._dock.close()
                self.instrument_guis[name]._dock.setParent(None)
                del self.instrument_guis[name]._dock
                self.instrument_guis[name].close()
                self.instrument_guis[name].setParent(None)
                del self.instrument_guis[name]
            except:
                pass
        self.instrument_guis = {}

    def modify_config(self):
        """ Opens the window for modifying the config.
        Note that this is still buggy when re-loading."""
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

    def update_statusbar(self, measurement=None, timer=None):
        """ This method should be started on a thread by the Measurement gui Start button.
        It will grab the measurement status, name and message from experiment and display them in the statusbar.
        If the timer is passed it will also stop its own timer when experiment.running_status is 0 again
        """
        msg = ['Ready', 'Measuring', 'Pausing', 'Breaking', 'Stopping'][self.experiment.running_status]
        if self.experiment.running_status:
            if self.experiment._measurement_name:
                msg += ': '+self.experiment._measurement_name
            if self.experiment.measurement_message:
                msg += ': '+self.experiment.measurement_message
        self.statusBar().showMessage(msg)
        if not self.experiment.running_status and timer is not None:
            timer.stop()



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

    def __show_pyqtgraph_examples(self):
        """ For convenience a direct link to the PyQtGraph examples"""
        self.logger.info('Starting built-in PyQtGraph examples in separate process.')
        import pyqtgraph.examples.__main__
        import subprocess
        subprocess.Popen('python '+pyqtgraph.examples.__main__.__file__)

    def __about_dialog(self):
        """
        Show an "About" window with a bit of information about the history of development, the creators and where to get
        help.
        :return:
        """
        if hasattr(self.experiment, 'datman'):
            if hasattr(self.experiment.datman, '_version'):
                datman_str = 'DataManager version: {}\n'.format(self.experiment.datman._version)
            else:
                datman_str=''
        QMessageBox.question(self, 'About Hyperion',
                                   "Hyperion version: {}\n{}\n"
                                   "The Hyperion framework/platform was developed in the KuipersLab\n"
                                   "at the Technical University Delft in The Netherlands with the\n"
                                   "purpose of controlling lab equipment and automating measurements.\n\n"
                                   "The core design was made by:\n"
                                   "   Aron Opheij\n"
                                   "   Martin Caldarola\n\n"
                                   "Other significant contributions were made by:\n"
                                   "   Ariël Komen\n"
                                   "   Irina Komen\n"
                                   "   Marc Noordam\n\n"
                                   "Disclaimer:\n"
                                   "None of us are professional software developers and this software is "
                                   "still very buggy. If you'd like to contribute to this software, find "
                                   "Hyperion on gitlab.com, or try hyperion.python@gmail.com or contact "
                                   "the current members of the KuipersLab.".format(hyperion.__version__, datman_str),
                                   QMessageBox.Close, QMessageBox.Close)


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
        self.resize(1000, 790)
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
                self.experiment.remove_all_instruments()
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
                self.experiment.remove_all_instruments()
                self.experiment.load_config('_manually_modified_yaml_', dic)
                self.experiment.load_instruments()
            except:
                self.logger.error('Failed to load config and instruments from dict')
                QMessageBox.warning(self, 'Error', 'Error while applying config or loading instruments', QMessageBox.Ok)
                return
            try:
                for meas_name, meas_gui in self.measurement_guis.items():
                    if hasattr(meas_gui, 'create_actionlist_guis'):
                        self.logger.debug('Updating Measurement GUI: {}'.format(meas_name))
                        meas_gui.create_actionlist_guis()
                        meas_gui.update_buttons()
                        meas_gui.update()
            except:
                self.logger.warning('Encountered error while trying to update Measurement GUIs')
            self.close()


if __name__ == '__main__':
    import hyperion
    from examples.example_project_with_automated_scanning.my_experiment import MyExperiment

    # logger = logging.getLogger(__name__)

    config_file = os.path.join(hyperion.repository_path, 'examples', 'example_project_with_automated_scanning', 'my_experiment.yml')

    # logging.stream_level = logging.WARNING
    experiment = MyExperiment()
    # logging.stream_level = logging.DEBUG
    experiment.load_config(config_file)
    experiment.load_instruments()

    app = QApplication(sys.argv)
    main_gui = ExpGui(experiment)
    # sys.exit(app.exec_())
    app.exec_()