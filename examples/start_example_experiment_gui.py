import sys
from PyQt5.QtWidgets import QApplication
from hyperion.view.master_gui import App
from examples.example_experiment import ExampleExperiment

def main():
    experiment = ExampleExperiment()
    app = QApplication(sys.argv)
    main_gui = App(experiment)
    sys.exit(app.exec_())
main()