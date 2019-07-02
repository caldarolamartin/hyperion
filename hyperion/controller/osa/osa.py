# -*- coding: utf-8 -*-
"""
==================
Example controller
==================

This is an example of a controller with a fake (invented) device. It should help to gide
developers to create new controllers for real devices.


"""
import logging
import visa
import time
import matplotlib.pyplot as plt
from hyperion.controller.base_controller import BaseController


class Osa(BaseController):
    """ Example output device that does not connect to anything"""

    FAKE_RESPONSES = {'A': 1,
                      }

    def __init__(self, settings={'port': 'AUTO', 'dummy': False}):
        """ Init of the class.

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict

        """
        super().__init__(settings)  # mandatory line
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class Osa created.')
        self.name = 'OSA Controller'

        self._amplitude = []

        self.__rm = visa.ResourceManager()
        self.__resource_list = self.__rm.list_resources()
        self.__osa = None
        self.__start_wav = None
        self.__end_wav = None
        self.__optical_resolution = None
        self.__sample_points = None
        self.__settings = settings
        if 'port' in self.__settings:
            self.__port = self.__settings['port']
        else:
            self.__port = 'AUTO'


    def initialize(self):
        """ Starts the connection to the device in port """
        self.logger.info('Opening connection to OSA')

        if self.__port == 'AUTO':
            for dev in self.__resource_list:
                if dev[:4] == 'GPIB':
                    self.__osa = self.__rm.open_resource(dev)
                    if self.__osa.query("*IDN?")[:11] == 'ANDO,AQ6317':
                        break
                    self.__osa.close()
                    logging.error('OSA not found')
        else:
            self.__osa = self.__rm.open_resource(self.__port)

        self.__osa.read_termination = '\r\n'

        self.__osa.write('SRQ1')    # This seems to be necessary in order to poll whether device is done with self.__osa.read_stb())
        self._is_initialized = True  # THIS IS MANDATORY!!
        # this is to prevent you to close the device connection if you
        # have not initialized it inside a with statement
        #self._amplitude = self.query('A?')
        self.start_wav


    def wait_for_osa(self, timeout):
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if ((self.__osa.read_stb()) % 2) == 1:
                return
            time.sleep(.01)

    @property
    def start_wav(self):
        self.__start_wav = self.__osa.query_ascii_values('STAWL?')[0]
        return self.__start_wav


    @start_wav.setter
    def start_wav(self, start_wav):
        # note that OSA works from 600 to 1750 nm
        if start_wav != self.__start_wav:
            self.__start_wav = start_wav
            self.__osa.write('STAWL{:1.2f}'.format(start_wav))
            self.__start_wav = self.__osa.query_ascii_values('STAWL')[0]

            #print('STAWL{:1.2f}'.format(self.__start_wav))
            #self.__osa.write('STAWL{:1.2f}'.format(self.__start_wav))

    @property
    def end_wav(self):
        self.__end_wav = self.__osa.query_ascii_values('STpWL?')[0]
        return self.__end_wav

    @end_wav.setter
    def end_wav(self, end_wav):
        if end_wav != self.__end_wav:
            self.__end_wav = end_wav
            self.__osa.write('STpWL{:1.2f}'.format(end_wav))
            self.__end_wav = self.__osa.query_ascii_values('STpWL')[0]

            #print('STpWL{:1.2f}'.format(self.__end_wav))
            #self.__end_wav = end_wav

    @property
    def optical_resolution(self):
        self.__optical_resolution = self.__osa.query_ascii_values('RESLN?')[0]
        return self.__optical_resolution

    @optical_resolution.setter
    def optical_resolution(self, optical_resolution):
        if optical_resolution != self.__optical_resolution:
            self.__optical_resolution = optical_resolution
            self.__osa.write('RESLN{:1.2f}'.format(optical_resolution))
            self.__optical_resolution = self.__osa.query_ascii_values('RESLN')[0]


    @property
    def sample_points(self):
        self.__sample_points = self.__osa.query_ascii_values('SMPL?')[0]
        return self.__sample_points

    @sample_points.setter
    def sample_points(self, sample_points):
        if sample_points != self.__sample_points:
            self.__sample_points = sample_points
            self.__osa.write('SMPL{:1.2f}'.format(sample_points))
            self.__sample_points = self.__osa.query_ascii_values('SMPL')[0]

    def perform_single_sweep(self):
        self.__osa.write('SGL')

    def get_data(self):
        # wait for OSA to finish before grabbing data
        time.sleep(5)

        wav = self.__osa.query_ascii_values('WDATA')[1:]
        spec = self.__osa.query_ascii_values('LDATA')[1:]
        plt.plot(wav, spec, '.-')

    def finalize(self):
        """ This method closes the connection to the device.
        It is ran automatically if you use a with block

        """
        self.logger.info('Closing connection to device.')
        self.__osa.close()
        self._is_initialized = False

    def idn(self):
        """ Identify command

        :return: identification for the device
        :rtype: string
        """
        self.logger.debug('Ask IDN to device.')
        return 'ExampleController device'

    def query(self, msg):
        """ writes into the device msg

        :param msg: command to write into the device port
        :type msg: string
        """
        self.logger.debug('Writing into the example device:{}'.format(msg))
        self.write(msg)
        ans = self.read()
        return ans

    def read(self):
        """ Fake read that returns always the value in the dictionary FAKE RESULTS.

        :return: fake result
        :rtype: string
        """
        return self.FAKE_RESPONSES['A']

    def write(self, msg):
        """ Writes into the device
        :param msg: message to be written in the device port
        :type msg: string
        """
        self.logger.debug('Writing into the device:{}'.format(msg))

    @property
    def amplitude(self):
        """ Gets the amplitude value.

        :getter:
        :return: amplitude value in Volts
        :rtype: float

        For example, to use the getter you can do the following

        >>> with DummyOutputController() as dev:
        >>>    dev.initialize('COM10')
        >>>    dev.amplitude
        1

        :setter:
        :param value: value for the amplitude to set in Volts
        :type value: float

        For example, using the setter looks like this:

        >>> with DummyOutputController() as dev:
        >>>    dev.initialize('COM10')
        >>>    dev.amplitude = 5
        >>>    dev.amplitude
        5


        """
        self.logger.debug('Getting the amplitude.')
        return self._amplitude

    @amplitude.setter
    def amplitude(self, value):
        # would be nice to add a way to check that the value is within the limits of the device.
        if self._amplitude != value:
            self.logger.info('Setting the amplitude to {}'.format(value))
            self._amplitude = value
            self.write('A{}'.format(value))
        else:
            self.logger.info('The amplitude is already {}. Not changing the value in the device.'.format(value))


class OsaDummy(Osa):
    """
    Example Controller Dummy
    ========================

    A dummy version of the Example Controller.

    In essence we have the same methods and we re-write the query to answer something meaningful but
    without connecting to the real device.

    """

    def query(self, msg):
        """ writes into the device msg

        :param msg: command to write into the device port
        :type msg: string
        """
        self.logger.debug('Writing into the dummy device:{}'.format(msg))
        ans = 'A general dummy answer'
        return ans


def get_recommended_sample_points(dev):
    # recommend at the very least 1 + 2*(end_wav-start_wav)/optical_resolution
    return 1 + 2*((dev.end_wav - dev.start_wav)/dev.optical_resolution)


def set_settings_for_osa(dev):
    #in this method the parameters for the osa machine are set
    dev.end_wav = 1200
    print(dev.end_wav)
    print("-" * 40)

    dev.start_wav = 900.00
    print(dev.start_wav)
    print("-" * 40)

    # allowed are 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0
    dev.optical_resolution = 1.00
    print(dev.optical_resolution)
    print("-" * 40)

    dev.sample_points = get_recommended_sample_points(dev)
    print(dev.sample_points)


if __name__ == "__main__":
    from hyperion import _logger_format, _logger_settings

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])




    dummy = False  # change this to false to work with the real device in the COM specified below.

    if dummy:
        my_class = OsaDummy
    else:
        my_class = Osa

    with my_class(settings={'dummy': dummy}) as dev:

        dev.initialize()
        set_settings_for_osa(dev)
        
        #dev.perform_single_sweep()
        #dev.get_data()



