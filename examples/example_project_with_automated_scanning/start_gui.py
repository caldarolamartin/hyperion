"""
=========
Start GUI
=========

This is an example file demonstrating how to start your experiment in a GUI.

"""
import os
import sys
import hyperion
from examples.example_project_with_automated_scanning.my_experiment import MyExperiment
from hyperion.view.experiment_gui import ExpGui
from PyQt5.QtWidgets import QApplication


# logger = logging.getLogger(__name__)

config_file = os.path.join(hyperion.repository_path, 'examples', 'example_project_with_automated_scanning',
                           'my_experiment.yml')

# logging.stream_level = logging.WARNING
experiment = MyExperiment()
# logging.stream_level = logging.DEBUG
experiment.load_config(config_file)
experiment.load_instruments()

app = QApplication(sys.argv)
main_gui = ExpGui(experiment)
# sys.exit(app.exec_())
app.exec_()