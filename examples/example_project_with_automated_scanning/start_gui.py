"""
=========
Start GUI
=========

This is an example file demonstrating how to start your experiment in a GUI.

"""
import os
import sys
from examples.example_project_with_automated_scanning.my_experiment import MyExperiment
from hyperion.view.experiment_gui import ExpGui
from PyQt5.QtWidgets import QApplication

# # If you want to add logging to this file, import it and create a logger:
# from hyperion import logging
# logger = logging.getLogger(__name__)

this_folder = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(this_folder, 'my_experiment.yml')

# logging.stream_level = logging.WARNING  # Temporarily change logging level
experiment = MyExperiment()
# logging.stream_level = logging.DEBUG  # Change logging level

# Loading the config from th GUI doesn't work very well yet.
# It's best to do it here already.
experiment.load_config(config_file)
experiment.load_instruments()

# Create PyQt background application.
app = QApplication(sys.argv)  # The sys.argv can also be replaced with [] if you don't need to pass command line arguments
# All QWidgets created now, will be a part of this application (use .show() to make them visible)

# Pass the experiment object into ExpGui to create the main window:
main_gui = ExpGui(experiment)

# Actually run the QApplication:
app.exec_()
# sys.exit(app.exec_())
