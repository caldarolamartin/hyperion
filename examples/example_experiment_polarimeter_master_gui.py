import os, sys
import logging
from PyQt5.QtWidgets import QApplication
from hyperion.view.master_gui import App
from examples.example_experiment_polarimeter import ExampleExperimentPolarimeter
from hyperion import _logger_format, _logger_settings

logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                    handlers=[
                        logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                             maxBytes=_logger_settings['maxBytes'],
                                                             backupCount=_logger_settings['backupCount']),
                        logging.StreamHandler()])

logging.info('Running Example GUI file.')
examples_folder = os.path.dirname( os.path.realpath(__file__) )
config_file = 'example_experiment_polarimeter_config.yml'
config_filepath = os.path.join(examples_folder, config_file)

with ExampleExperimentPolarimeter() as e:
    e.load_config(config_filepath)
    app = QApplication(sys.argv)
    main_gui = App(e) # remember the main gui initializes the instruments
    app.exec_()
