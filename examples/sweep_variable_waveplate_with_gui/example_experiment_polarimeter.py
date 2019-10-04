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
from hyperion import ur
from hyperion.experiment.base_experiment import BaseExperiment


class ExampleExperimentPolarimeter(BaseExperiment):
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
        winsound.Beep(1600, 800)  # (frequency in Hz, Duration in ms)
        winsound.Beep(1500, 200)
        winsound.Beep(1600, 500)
        sleep(0.1)

    def sweep_waveplate_polarimeter(self):
        """ Sweeping """
        self.logger.info('Starting the Sweep')
        self.logger.debug('Getting the settings from the config file.')
        scan_properties = self.properties['Measurements']['SweepWaveplate']['settings']
        self.logger.debug('Scan properties: {}'.format(scan_properties))


        start = ur(scan_properties['start'])
        unit = start.u
        stop = ur(scan_properties['stop'])
        step = ur(scan_properties['step'])
        n = np.floor(np.abs(stop.m_as(unit)-start.m_as(unit))/step.m_as(unit)) + 1
        self.xdata = np.linspace(start.m_as(unit),stop.m_as(unit),n)
        self.xdata_unit = unit
        self.ydata = np.zeros_like(self.xdata)
        self.ydata_error = np.zeros_like(self.xdata)
        self.ydata_unit = 'normalized'

        # set the devices values
        self.logger.debug('Setting the wavelength for the measurement')
        wl = ur(scan_properties['wavelength'])
        self.instruments_instances['Polarimeter'].change_wavelength(wl)

        # turn on the output of the VWP
        self.instruments_instances['VariableWaveplate'].output = True


        self.logger.info('Starting the for loop that measures')
        for index, value in enumerate(self.xdata):
            #set
            self.instruments_instances['VariableWaveplate'].set_analog_value(1,value*unit)
            sleep(ur(scan_properties['stabilization']).m_as('s'))
            # colect data
            av, st = self.instruments_instances['Polarimeter'].get_average_data(scan_properties['average'])
            self.ydata[index] = av[2]
            self.ydata_error[index] = st[2]

        self.logger.info('Finished with the for')

        # turn of the VWP
        self.instruments_instances['VariableWaveplate'].output = False
        print(self.ydata)




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

        # Adding manual name because I'll always use this instrument with this experiment
        if 'Polarimeter' in self.instruments_instances:
            self.pol = self.instruments_instances['Polarimeter']

        # self.instruments_instances["vwp"] = self.load_instrument('VariableWaveplate')
        # self.logger.debug('Class vwp: {}'.format(self.vwp))
        # self.instruments_instances["example_instrument"] = self.load_instrument('ExampleInstrument')
        # self.logger.debug('Class example_instrument: {}'.format(self.example_instrument))


if __name__ == '__main__':
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

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
        print(e.instruments_instances.keys())
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

