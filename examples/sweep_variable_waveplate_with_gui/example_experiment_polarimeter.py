"""
    ==============================================================
    Example Experiment with a variable waveplate and a polarization
    ==============================================================

    This is an example of an experiment class with two devices


"""
import os
from hyperion.core import logman
# You could also import the logging manager as logging if you don't want to change your line: logger = logging.getLogger(__name_)
# from hyperion.core import logman as logging
# from hyperion import logging    # equivalent to line above
import numpy as np
import winsound
from time import sleep
from hyperion import ur
from hyperion.experiment.base_experiment import BaseExperiment
from hyperion.tools.array_tools import array_from_pint_quantities, array_from_string_quantities, array_from_settings_dict


class ExampleExperimentPolarimeter(BaseExperiment):
    """ Example class  """

    def __init__(self):
        super().__init__()
        self.logger = logman.getLogger(__name__)
        self.logger.info('Initializing the ExampleExperimentPolarimeter class.')

        # data
        self.xdata = np.zeros(0)
        self.xdata_unit = ''
        self.ydata = np.zeros_like(self.xdata)
        self.ydata_error = np.zeros_like(self.xdata)
        self.ydata_unit = ''

        self.wavelength = []

        self._sweep_waveplate_polarimeter_in_progress = False


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.finalize()

    def make_sound(self):
        """ This methods makes a sound to call the attention of humans
            This method is by far the best method Martin has made, trust me, I am an expert
        """
        self.logger.debug('Making sound')
        winsound.Beep(1600, 800)  # (frequency in Hz, Duration in ms)
        winsound.Beep(1500, 200)
        winsound.Beep(1600, 500)
        sleep(0.1)

    def sweep_waveplate_polarimeter(self):
        """ Sweeping """
        self._sweep_waveplate_polarimeter_in_progress = True        # always set the "in progress" flag True at the start of a measurement method
        self.logger.info('Starting the Sweep')
        self.logger.debug('Getting the settings from the config file.')
        scan_properties = self.properties['Measurements']['SweepWaveplate']['settings']   # shorthand copy for inside this method only
        self.logger.debug('Scan properties: {}'.format(scan_properties))

        self.xdata, self.xdata_unit = array_from_settings_dict(scan_properties)

        # # The line above replaces the commented section below

        # start = ur(scan_properties['start'])
        # unit = start.u
        # stop = ur(scan_properties['stop'])
        # step = ur(scan_properties['step'])
        # n = np.floor(np.abs(stop.m_as(unit)-start.m_as(unit))/step.m_as(unit)) + 1
        # self.xdata = np.linspace(start.m_as(unit),stop.m_as(unit),n)
        # self.xdata_unit = unit
        self.ydata = np.zeros_like(self.xdata)
        self.ydata_error = np.zeros_like(self.xdata)
        self.ydata_unit = 'normalized'

        # set the devices values
        self.logger.debug('Setting the wavelength for the measurement')
        wl = ur(scan_properties['wavelength'])
        self.instruments_instances['Polarimeter'].change_wavelength(wl)
        self.wavelength = wl

        # turn on the output of the VWP
        self.instruments_instances['VariableWaveplate'].output = True


        self.logger.info('Starting the for loop that measures')
        for index, value in enumerate(self.xdata):
            #set
            self.instruments_instances['VariableWaveplate'].set_analog_value(1,value*self.xdata_unit)
            sleep(ur(scan_properties['stabilization']).m_as('s'))
            # colect data
            av, st = self.instruments_instances['Polarimeter'].get_average_data(scan_properties['average'])
            self.ydata[index] = av[2]
            self.ydata_error[index] = st[2]
            if not self._sweep_waveplate_polarimeter_in_progress:
                self.logger.info('VWP sweep aborted')
                break

        self.logger.info('Finished looping over VWP voltages')

        # turn of the VWP
        self.instruments_instances['VariableWaveplate'].output = False
        self._sweep_waveplate_polarimeter_in_progress = False           # always set the "in progress" flag False at the end of a measurement method


if __name__ == '__main__':
    # ### To change the logging level:
    # logman.stream_level(logman.WARNING)
    # logman.file_level('INFO')
    # ### To change the stream logging layout:
    # logman.set_stream(compact=0.2, color_scheme='dim') # and other parameters
    # ### To change the logging file:
    # logman.set_file('example_experiment.log')

    with ExampleExperimentPolarimeter() as e:

        name = 'example_experiment_polarimeter_config'
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
        print('Loaded instruments: {}'.format(e.instruments_instances.keys()))
        print('-------------- DONE LOADING DEVICES ----------------')
        #

        # save metadata
        #e.save_scan_metadata()
        #e.save_scan_metadata()

        # perform scan
        # e.set_scan()
        e.sweep_waveplate_polarimeter()

        # if you want to use the instruments directly, you can:
        # wl = 532*ur('nm')
        # e.instruments_instances['Polarimeter'].initialize(wavelength = wl)
        # data = e.instruments_instances['Polarimeter'].get_multiple_data(2)
        # print('\n\n {} \n\n'.format(data))
        #
        # print(e.instruments_instances['VariableWaveplate'].controller._is_initialized)

        # make sound
        e.make_sound()

        # # save data
        # e.save_scan_data()


    print('--------------------- DONE with the experiment')

