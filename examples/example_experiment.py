"""
    ===============
    Base Experiment
    ===============

    This is a base experiment class. The propose is put all the common methods needed for the experiment
    classes so they are shared and easily modified.

"""
import os
import logging
import importlib
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

    def set_scan(self, scan):
        """ Method to setup a scan.

        :param scan: a dict containing all the information

        """

        self.logger.debug('Setting up devices: detectors and actuators.')
        self.setup_device(device, settings)

        if 'Triger' in scan:
            # set up trigger
            self.set_up_trigger(trigger_device)

        # creating variables needed for the scan
        self.logger.debug('Reading parameters for Scan from the config file.')
        # wavelength
        units = start.u
        stop = stop.to(units)
        num_points = (stop - start) / step
        num_points = round(num_points.m_as(''))
        scan = np.linspace(start, stop, num_points + 1)

        # initialize the vectors to save data
        self.xdata_scan = scan
        self.ydata_scan = np.zeros((np.size(scan), self.number_detectors))
        self.ydata_scan_error = np.zeros((np.size(scan), self.number_detectors))

        self.tdata_h_scan = np.zeros(np.size(scan))
        self.tdata_m_scan = np.zeros(np.size(scan))
        self.tdata_s_scan = np.zeros(np.size(scan))

    def load_instruments(self):

        self.vwp = self.load_instrument('VariableWaveplate')
        self.logger.debug('Class vwp: {}'.format(self.vwp))
        self.example_instrument = self.load_instrument('ExampleInstrument')
        self.logger.debug('Class example_instrument: {}'.format(self.example_instrument))

    def load_instrument(self, name):
        """ Loads instrument

        :param name: name of the instrument to load
        :type name: string
        """

        self.logger.debug('Loading instrument: {}'.format(name))

        for inst in self.properties['Instruments']:
            self.logger.debug('instrument name: {}'.format(inst))

            if name in inst:
                module_name, class_name = inst[name]['driver'].split('/')
                self.logger.debug('Module name: {}. Class name: {}'.format(module_name, class_name))
                my_class = getattr(importlib.import_module(module_name), class_name)
                return my_class(inst[name])

        self.logger.warning('The name "{}" does not exist in the config file'.format(name))
        return None




if __name__ == '__main__':


    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with ExampleExperiment() as e:

        config_folder = 'D:/mcaldarola/hyperion/examples/' # this should be your path for the config file you use
        name = 'example_experiment_config'
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
        # # e.load_aotf_controller()
        # # # e.load_voltage_controller()
        # # e.load_fun_gen()
        print('-------------- DONE LOADING DEVICES ----------------')
        #
        # # save metadata
        # e.save_scan_metadata()
        #
        # # got to wavelength
        # # w = 605*ur('nanometer')
        # # print('Wavelength = {}'.format(w))
        # # e.go_to_wavelength(w, 22)
        #
        # # perform scan
        # e.do_wavelength_scan()
        #
        # # save data
        # e.save_scan_data()
        #
        # # finalize
        # e.finalize_aotf()
        # # e.finalize_analog_voltage_controller()
        # e.finalize_fun_gen()

    print('--------------------- DONE with the experiment')

