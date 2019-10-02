import os, sys
import hyperion
from PyQt5.QtWidgets import QApplication
from hyperion.view.master_gui import App
from examples.example_experiment_polarimeter import ExampleExperimentPolarimeter

examples_folder = os.path.dirname( os.path.realpath(__file__) )
config_file = 'example_experiment_polarimeter_config.yml'
config_filepath = os.path.join(examples_folder, config_file)

with ExampleExperimentPolarimeter() as e:
    e.load_config(config_filepath)
    e.load_instruments()
    # e.pol.initialize()

    app = QApplication(sys.argv)
    main_gui = App(e)
    sys.exit(app.exec_())