"""
==============
Measuremnt GUI
==============

This file contains an example of a Measurement Gui.
The class inherits from AutoMeasurementGui which takes care of building the gui from the config file and the
"actionwidgets".
If you like, you can add extra gui elements by adding them to self.layout (which is the outer QVBoxLayout from
AutoMeasurementGui)

The main purpose is to

"""

from hyperion.view.base_guis import AutoMeasurementGui
from hyperion import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
import numpy as np

class MyMeasurementGuiWithPlotting(AutoMeasurementGui):
    """
    Create a custom class that inherits from AutoMeasurementGui but expands it with plotting.

    :param experiment:
    :param measurement:
    :param parent:
    :param output_guis:
    :param graphs_in_standalone:

    """
    def __init__(self, experiment, measurement, parent=None, output_guis=None):

        # Initialize parent class
        super().__init__(experiment, measurement, parent=parent, output_guis=output_guis)
        logging.getLogger(__name__)
        self.experiment = experiment
        self.measurement = measurement

        self.output_guis = output_guis

        self.timer_interval_ms = 50

        # Make sure the plotting update flags exist:
        self.experiment.flag_new_spectral_data = False
        self.experiment.flag_new_camera_image = False

        self.timer_update_plotting = QTimer()
        self.timer_update_plotting.timeout.connect(self.update_plots)
        # Idea:
        # Have one thread that


        self.initialize_some_graphics()

        # To demonstrate that th gui can still be expanded, a button to swap x and y direction is added here
        button_swap_XY = QPushButton('Swap atto XY direction')
        button_swap_XY.clicked.connect(self.swap_XY)
        self.outer_layout.insertWidget(1,button_swap_XY)

    def swap_XY(self):
        self.experiment.swap_actions(
            self.experiment.properties['Measurements'][self.measurement]['automated_actionlist'],
            'Scan Atto X', 'Scan Atto Y')
        self.create_actionlist_guis()

    def initialize_some_graphics(self):
        # Note that if you have your own plotting classes you could also set these things there.
        # But in this case I'm using pyqtgraph/PlotWidget directly for my VisualizationGui
        number_of_existing_plots = len(self.output_guis['Power'].getPlotItem().listDataItems())
        if number_of_existing_plots == 1:
            self.spec_curve = self.output_guis['Power'].getPlotItem().listDataItems()[0]
        else:
            self.output_guis['Power'].getPlotItem().clear()
            self.spec_curve = self.output_guis['Power'].plot()

    def start_plotting(self, *args, **kwargs):
        self.timer_update_plotting.start(self.timer_interval_ms)


    def update_plots(self):
        # If measurement finished: stop updating plots
        if not self.experiment.running_status:
            self.timer_update_plotting.stop()
            return

        # There are multiple ways of getting the plotting data from your experiment/measurement to the plots.
        # One more direct way is to simply make a variable in you experiment class that holds the (latest) data and
        # create a boolean flag to indicate that new data is ready. Here you check if the flag is true, send the data to
        # the plotwindows and reset the flag.
        if self.experiment.flag_new_spectral_data:
            self.spec_curve.setData(self.experiment.fake_counts)
            self.experiment.flag_new_spectral_data = False

        # What is implemented below is basically the same except it doesn't use manually created data variables and flags
        # but grabs data directly from the datamanager in the experiment class. This is a bit less transparent but
        # doesn't require extra copies of the data in memory.
        # ONE DOWNSIDE IS THAT WHEN SAVING IS DISABLED, THE DATA IS NOT STORED IN THE DATAMANGER AND THEREFORE INACCESIBLE FOR PLOTTING
        # THE OTHER APPROACH IS MORE PRACTICAL

        # if self.experiment.datman.new_data_flags['Image_Before']:
        #     # grab the data:
        #     data = self.experiment.datman.root.variables['Image_Before'][:]  # Grab the whole array because it's filled all at once
        #     self.output_guis['Image'].setImage(data.transpose(), xvals=np.linspace(1., 3., data.shape[0]))
        #     # self.output_guis['Image'].show()
        #     # Clear the flag
        #     self.experiment.datman.new_data_flags['Image_Before'] = False

        # Changed it to the other approach:

        if self.experiment.flag_new_camera_image:
            self.output_guis['Image'].setImage(self.experiment.camera_image.transpose(), xvals=np.linspace(1., 3., self.experiment.camera_image.shape[0]))
            self.experiment.flag_new_camera_image = False



        # if self.experiment.datman.new_data_flags['Spectrum']:
        #     # grab the data:
        #
        #     # Because part of this array is created before it's filled with data, grab the current indices
        #     indices = self.experiment.datman.new_data_indices['Spectrum']
        #     ind0 = indices[0]
        #     # Due to the way the nesing indices are passed by the automated scanner, instead of indices being [X,0],
        #     # it will be [X]. In that case manually set index1 to 0.
        #     # (These nesting indices are deeply integrated in the automated scanning in BaseExperiment and it's not
        #     #  possible to change this behavior. The user needs to fix it at this level
        #     if len(indices) == 1:
        #         ind1 = 0
        #     else:
        #         ind1 = indices[1]
        #
        #     data = self.experiment.datman.root.variables['Spectrum'][ind0, ind1, :]
        #
        #     # data = self.experiment.datman.root.variables['Spectrum'][tuple(indices)]
        #
        #     # data = np.random.random(100)
        #     self.spec_curve.setData(data)
        #     # Clear the flag
        #     self.experiment.datman.new_data_flags['Spectrum'] = False
        #     # self.output_guis['Spectrum'].show()