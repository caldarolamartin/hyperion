import os, sys
from hyperion import logging
from PyQt5.QtWidgets import QApplication
from hyperion.view.master_gui import MasterGui
from examples.sweep_variable_waveplate_with_gui.example_experiment_polarimeter import ExampleExperimentPolarimeter

logging.info('Running Example GUI file.')
examples_folder = os.path.dirname( os.path.realpath(__file__) )
config_file = 'example_experiment_polarimeter_config.yml'
config_filepath = os.path.join(examples_folder, config_file)

with ExampleExperimentPolarimeter() as e:
    e.load_config(config_filepath)
    app = QApplication(sys.argv)
    main_gui = MasterGui(e) # remember the main gui initializes the instruments
    app.exec_()
