"""
    ==================
    Example Experiment
    ==================



    This is an example of an experiment class.
"""
import os
import logging

import numpy as np
import winsound
from time import sleep
# from hyperion import ur, root_dir
from hyperion.experiment.base_experiment import BaseExperiment


class ExampleExperiment(BaseExperiment):
    """ Example class with basic functions """

    def __init__(self):
        """ initialize the class"""

        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing the Base_Experiment class.')

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


    def load_instruments(self):
        """"
        This method gets the instance of every instrument and sets this instance
        in the self.instruments_instances(this is a dictionary). This way they are approachable via self.instruments_instances.items(),
        The option to set the instruments by hand is still possible, but not necessary because the pointer
        to the instrument 'lives' in the instruments_instances.
        """

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



if __name__ == '__main__':

    # For the new of logging: import hyperion
    import hyperion

    # That will be enough for default logging, but if you want to change level or the location of the file:
    hyperion.stream_logger.setLevel( logging.WARNING )          # To change logging level on the console
    # hyperion.file_logger.setLevel( logging.INFO )             # To change logging level in the file (default is DEBUG)
    # hyperion.set_logfile('my_new_file_path_and_name.log')     # To change the logging file (default is DEBUG)

    # with ExampleExperiment() as e:
    #
    #     name = 'second_example_experiment_config_'
    #     config_folder = os.path.dirname(os.path.abspath(__file__))
    #     config_file = os.path.join(config_folder, name)
    #
    #     print('Using the config file: {}.yml'.format(config_file))
    #     e.load_config(config_file + '.yml')
    #
    #     # read properties just loaded
    #     print('\n {} \n'.format(e.properties))
    #
    #     #  remember you can change these values directly here
    #     #e.properties['Scan']['start'] = '0.5V'
    #
    #
    #     # # Initialize devices
    #     print('\n-------------- LOADING DEVICES ----------------\n')
    #     e.load_instruments()
    #     print(e.instruments_instances.keys())
    #     print('-------------- DONE LOADING DEVICES ----------------')
    #     #
    #
    #     # save metadata
    #
    #     #e.save_scan_metadata()
    #     #e.save_scan_metadata()
    #     #e.VariableWaveplate.set_analog_value(1,2.25*ur('volt'))
    #     # perform scan
    #     # e.set_scan()
    #     # e.do_scan()
    #     # e.make_sound()
    #
    #     # # save data
    #     # e.save_scan_data()


    e = ExampleExperiment()

    name = 'example_experiment_config_smartscan.yml'
    config_folder = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(config_folder, name)

    print('Using the config file: {}'.format(config_file))
    e.load_config(config_file)

    # read properties just loaded
    print('\n {} \n'.format(e.properties))

    #  remember you can change these values directly here
    #e.properties['Scan']['start'] = '0.5V'


    # # Initialize devices
    print('\n-------------- LOADING DEVICES ----------------\n')
    e.load_instruments()
    print(e.instruments_instances.keys())
    print('-------------- DONE LOADING DEVICES ----------------')
    #

    # save metadata



    print('--------------------- DONE with the experiment')

