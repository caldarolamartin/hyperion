import sys
from PyQt5.QtWidgets import QApplication
from hyperion.view.master_gui import MasterGui
from examples.example_experiment import ExampleExperiment
from hyperion.instrument.correlator.hydraharp_instrument import HydraInstrument
from hyperion.instrument.position.thorlabs_motor_instr import Thorlabsmotor
from hyperion import ur
# from hyperion.core import logman
ureg = ur

def main():
    """"
    Example of how to call the master_gui in a seperate file
    """
    experiment = ExampleExperiment()
    app = QApplication(sys.argv)
    main_gui = MasterGui(experiment)
    sys.exit(app.exec_())

def hydraharp_and_thorlabsmotor_experiment():
    """
    This method is here to have a small example of how in the hyperion way
    multiple instruments can be combined to do a experiment. In this case the instruments
    are the correlator and the thorlabsmotor.
    """
    #create instances of the correlator and thorlabsmotor
    hydra = HydraInstrument(settings={'devidx':0, 'mode':'Histogram', 'clock':'Internal',
                                   'controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'})
    motor = Thorlabsmotor(settings = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850090, 'name': 'Waveplate'})
    #initialize the correlator and thorlabsmotor
    #thorlabs_motor.initialize(83815760)
    # print(motor.list_devices())
    # motor.initialize(83841160)
    # hydra.initialize()
    # hydra.configurate()
    #doing something that resembles an experiment:
    motor_steps = 5
    for step in range(0, motor_steps):
        #for each step their should be done a scan and the thorlabs_motor should move a certain distance
        #take histogram with the correlator
        hydra.set_histogram(leng=65536, res=8.0 * ureg('ps'))
        hist = hydra.make_histogram(integration_time=5 * ureg('s'), count_channel=0)
        #move the thorlabs_motor 0.01 micrometer
        value = 0.01 *ur('micrometer')
        motor.move_relative(value.m_as('micrometer'), True)
    motor.finalize()
    hydra.finalize()

hydraharp_and_thorlabsmotor_experiment()