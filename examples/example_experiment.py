"""
    ==================
    Example Experiment
    ==================

    This is an example of an experiment class.


"""
import os
import logging

import numpy as np
import yaml
import winsound
from time import time, sleep, strftime
from datetime import datetime
from hyperion import ur, root_dir
from hyperion.experiment.base_experiment import BaseExperiment


class ExampleExperiment(BaseExperiment):
    """ Example class with basic functions """

    def __init__(self):
        """ initialize the class"""

        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing the Base_Experiment class.')

        self.devices = {}
        self.properties = {}
        self.instruments_instances = {}
        self.view_instances = {}

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

        """
        self.logger.debug('Making sound')
        winsound.Beep(3000, 800)  # (frequency in Hz, Duration in ms)
        winsound.Beep(1500, 200)
        winsound.Beep(3000, 500)
        sleep(0.1)

    def load_instruments(self):
        #rewriting this code:
        for instrument in self.properties['Instruments']:
            if not instrument == 'VariableWaveplate':
                instrument_name = instrument
                self.instrument_name = self.load_instrument(instrument_name)
                self.logger.debug('Class'+instrument_name+": {}".format(self.instrument_name))

        # self.vwp = self.load_instrument('VariableWaveplate')
        # self.logger.debug('Class vwp: {}'.format(self.vwp))
        # self.example_instrument = self.load_instrument('ExampleInstrument')
        # self.logger.debug('Class example_instrument: {}'.format(self.example_instrument))



if __name__ == '__main__':
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with ExampleExperiment() as e:

        name = 'example_experiment_config'
        config_folder = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(config_folder, name)

        print('Using the config file: {}.yml'.format(config_file))
        e.load_config(config_file + '.yml')

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
        e.load_interfaces()

        # save metadata
        #e.save_scan_metadata()
        #e.VariableWaveplate.set_analog_value(1,2.25*ur('volt'))

        # perform scan
        # e.set_scan()
        # e.do_scan()
        e.make_sound()

        # # save data
        # e.save_scan_data()


    print('--------------------- DONE with the experiment')

