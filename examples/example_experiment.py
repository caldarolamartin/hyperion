"""
    ==================
    Example Experiment
    ==================



    This is an example of an experiment class.
"""
import os
from hyperion.core import logman
# You could also import the logging manager as logging if you don't want to change your line: logger = logging.getLogger(__name_)
# from hyperion.core import logman as logging
# from hyperion import logging    # equivalent to line aboveimport numpy as np
import winsound
from time import sleep
# from hyperion import ur, root_dir
from hyperion.experiment.base_experiment import BaseExperiment
from hyperion.tools.array_tools import *
import sys

class ExampleExperiment(BaseExperiment):
    """ Example class with basic functions """

    def __init__(self):
        """ initialize the class"""
        self.logger = logman.getLogger(__name__)
        self.logger.info('Initializing the ExampleExperiment object.')
        super().__init__()                      # Mandatory line
        self.logger.critical('test critical')
        self.logger.error('test error')
        self.logger.warning('test warning')
        self.logger.info('test info')
        self.logger.debug('test debug')

        #initialize dictionaries where instances of instruments and gui's can be found
        self.devices = {}
        self.properties = {}
        self.instruments_instances = {}
        self.view_instances = {}
        self.graph_view_instance = {}

        # scanning variables
        self.scan = {}
        self.stop_monitor = False
        self.scan['detectors'] = []
        self.scan['detector_units'] = []
        self.scan['number detectors'] = len(self.scan['detectors'])
        self.scan['running'] = False

        # data
        self.xdata = np.zeros(0)
        self.ydata = np.zeros(0)
        self.zdata = np.zeros(0)
        self.wavelength = []
        # to save the time
        self.tdata_h_scan = np.zeros(0)
        self.tdata_m_scan = np.zeros(0)
        self.tdata_s_scan = np.zeros(0)

        # to save the data of the scan
        self.xdata_scan = np.zeros(0)
        self.xdata_scan_v = np.zeros(0)
        self.ydata_scan = np.zeros(0)
        self.ydata_scan_error = np.zeros(0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.finalize()

    def make_sound(self):
        """ This methods makes a sound to call the attention of humans
            This method is by far the best method Martin has made, trust me, I am an expert
        """
        self.logger.debug('Making sound')
        winsound.Beep(3000, 800)  # (frequency in Hz, Duration in ms)
        winsound.Beep(1500, 200)
        winsound.Beep(3000, 500)
        sleep(0.1)

    def measurement(self):
        for i in range(1, 10):
            print(i)


if __name__ == '__main__':
    # ### To change the logging level:
    # logman.stream_level(logman.WARNING)
    # logman.file_level('INFO')
    # ### To change the stream logging layout:
    # logman.set_stream(compact=0.2, color_scheme='dim') # and other parameters
    # ### To change the logging file:
    # logman.set_file('example_experiment.log')

<<<<<<< HEAD
        for instrument in self.properties['Instruments']:
            try:
                self.instruments_instances[instrument] = self.load_instrument(instrument)  # this method from base_experiment adds intrument instance to self.instrument_instances dictionary
                self.logger.debug('Class: '+instrument+" has been loaded in instrument_instances {}".format(self.instruments_instances[instrument]))
            except Exception:
                self.logger.warning("The instrument: "+str(instrument)+" is not connected to your computer")
                self.instruments_instances[instrument] = None
        # self.instruments_instances["vwp"] = self.load_instrument('VariableWaveplate')
        # self.logger.debug('Class vwp: {}'.format(self.vwp))
        # self.instruments_instances["example_instrument"] = self.load_instrument('ExampleInstrument')
        # self.logger.debug('Class example_instrument: {}'.format(self.example_instrument))

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


    def image(self, actiondict, perform_nested_actions):
        print('performing action of Name {} with exposuretime {}'.format(actiondict['Name'],actiondict['exposuretime']))
        perform_nested_actions()
        data = np.array([[0,1],[2,3]])
        return data

    def image_modified(self, actiondict, perform_nested_actions):
        print('image: ',actiondict['Name'])
        perform_nested_actions()

    def spectrum(self, actiondict, perform_nested_actions):
        print('spectrum: ',actiondict['Name'])
        perform_nested_actions()

    def spectrum_modified(self, actiondict, perform_nested_actions):
        print('spectrum: ',actiondict['Name'])
        perform_nested_actions()

    def histogram(self, actiondict, perform_nested_actions):
        print('histogram: ',actiondict['Name'])
        perform_nested_actions()

    def sweep_atto(self, actiondict, perform_nested_actions):
        print('sweep_atto: ',actiondict['Name'])
        arr, unit = array_from_settings_dict(actiondict)
        for s in arr:
            print(actiondict['axis'],' : ', s)
            perform_nested_actions(s)
=======
    with ExampleExperiment() as e:
>>>>>>> 565ffe25330348fcd10c9a59c951d7aca193bcbd

        name = 'second_example_experiment_config_'
        config_folder = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(config_folder, name)

        print('Using the config file: {}.yml'.format(config_file))
        e.load_config(config_file + '.yml')

        # read properties just loaded
        #print('\n {} \n'.format(e.properties))

        #  remember you can change these values directly here
        #e.properties['Scan']['start'] = '0.5V'


        # # Initialize devices
        print('\n-------------- LOADING DEVICES ----------------\n')
        e.load_instruments()
        print(e.instruments_instances.keys())
        print('-------------- DONE LOADING DEVICES ----------------')
        #

        # save metadata

        #e.save_scan_metadata()
        #e.save_scan_metadata()
        #e.VariableWaveplate.set_analog_value(1,2.25*ur('volt'))
        # perform scan
        # e.set_scan()
        # e.do_scan()
        # e.make_sound()

        # # save data
        # e.save_scan_data()


    print('--------------------- DONE with the experiment')
