# -*- coding: utf-8 -*-
"""
==============
Stanford SR830
==============

This controller (lock-in.py) supplies one class with several methods to communicate
    with the lock-in  from "??" model.

Based on the OSA Controller since it also uses GPIB connection.

"""
import logging
import visa
import time
from hyperion.controller.base_controller import BaseController

class sr830(BaseController):
    """ The controller for the lock-in.

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict

    """
    def __init__(self, settings={'port': 'AUTO', 'dummy': False}):
        super().__init__(settings)  # mandatory line
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class Lock-in created.')
        self.name = 'Lock-in Controller'

        self._rm = visa.ResourceManager()
        self._resource_list = self._rm.list_resources()
        self._osa = None
        #these are @properties variables
        self._start_wav = None
        self._end_wav = None
        self._optical_resolution = None
        self._sample_points = None
        self._sensitivity = None                # will match value of OSA (1-6)
        self._settings = settings
        if 'port' in self._settings:
            self._port = self._settings['port']
        else:
            self._port = 'AUTO'
        self._sensitivities = ['high1', 'high2', 'high3', 'norm_hold', 'norm_auto', 'mid']
        self._time_constants = [0.02, 0.12, 1.125, 0.001, 0.001, 0.002]
        self._sens_commands = ['SH1', 'SH2', 'SH3', 'SNHD', 'SNAT', 'SMID']

    def initialize(self):
        """ Starts the connection to the device with given port """
        self.logger.info('Opening connection to OSA')

        if self._port == 'AUTO':
            for dev in self._resource_list:
                if dev[:4] == 'GPIB':
                    self._osa = self._rm.open_resource(dev)
                    if self._osa.query("*IDN?")[:11] == 'ANDO,AQ6317':
                        break
                    self._osa.close()
                    logging.error('OSA not found')
        else:
            self._osa = self._rm.open_resource(self._port)

        self._osa.read_termination = '\r\n'

        self._osa.write('SRQ1')     # This seems to be necessary in order to poll whether device is done with self._osa.read_stb())
        self._is_initialized = True  # THIS IS MANDATORY!!
        # this is to prevent you to close the device connection if you
        # have not initialized it inside a with statement
        self.start_wav; self.end_wav; self.sample_points; self.sensitivity; self.optical_resolution
        # make sure self._start_wav/end_wav/sample_points/optical_resolution is the same as on the osa machine.
        # This is mandatory

    def wait_for_osa(self, timeout=None):
        """
        Method to let the program do nothing for a while
        in order to create enough time to let the osa machine take a spectrum.

        :param timeout: time in seconds how long the program must wait before it resumes
        if no timeout is specified a timeout will be calculated using self._time_constants
        :type timeout: float

        """
        if timeout==None:
            timeout = 4.0 + 1.05 * self._sample_points * self._time_constants[self._sensitivity-1]
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if ((self._osa.read_stb()) % 2) == 1:
                return
            time.sleep(.1)
        self.logger.info('Timout expired')


    @property
    def start_wav(self):
        """"
        The start_wav is the start wavelength of the osa.
        :param start_wav: a value between 600 and 1750
        :type int
        """
        self._start_wav = self._osa.query_ascii_values('STAWL?')[0]
        return self._start_wav

    @start_wav.setter
    def start_wav(self, start_wav):
        start_wav = round(start_wav, 2)
        if start_wav < 600 or start_wav > 1750:
            self.logger.warning('Invalid start_wav value')
        if start_wav != self._start_wav:
            self._start_wav = start_wav
            self._osa.write('STAWL{:1.2f}'.format(start_wav))
            self._start_wav = self._osa.query_ascii_values('STAWL?')[0]
            if start_wav != self._start_wav:
                self.logger.warning('Start_wav value not set in OSA')

    @property
    def end_wav(self):
        """"
        The end_wav is the end wavelength of the osa.
        :param end_wav: a value between 600 and 1750, must be greater than start_wav
        :type int
        """
        self._end_wav = self._osa.query_ascii_values('STPWL?')[0]
        return self._end_wav

    @end_wav.setter
    def end_wav(self, end_wav):
        end_wav = round(end_wav, 2)
        if end_wav <600 or end_wav > 1750:
            self.logger.warning("invalid end_wav value")
        if end_wav != self._end_wav:
            self._end_wav = end_wav
            self._osa.write('STPWL{:1.2f}'.format(end_wav))
            self._end_wav = self._osa.query_ascii_values('STPWL?')[0]
            if end_wav != self._end_wav:
                self.logger.warning("End_wav value not set in OSA")

    @property
    def optical_resolution(self):
        """"
        The optical resolution is the resolution of the spectrum you can take
        :param optical_resolution: a value that must be : 0.01, 0.02 ,0.05 ,0.1 ,0.2 ,0.5 ,1.0 ,2.0 , 5.0
        :type float
        """
        self._optical_resolution = self._osa.query_ascii_values('RESLN?')[0]
        return self._optical_resolution

    @optical_resolution.setter
    def optical_resolution(self, optical_resolution):
        optical_resolution = round(optical_resolution, 2)
        if not optical_resolution in [0.01,0.02,0.05,0.1,0.2,0.5,1.0,2.0,5.0]:
            self.logger.warning("invalid optical resolution value")
        if optical_resolution != self._optical_resolution:
            self._optical_resolution = optical_resolution
            self._osa.write('RESLN{:1.2f}'.format(optical_resolution))
            self._optical_resolution = self._osa.query_ascii_values('RESLN?')[0]
            if optical_resolution != self._optical_resolution:
                self.logger.warning("The optical resolution value did not set in OSA")


    @property
    def sample_points(self):
        """"
        The amount of sample_points the osa machine must use in order to take a spectrum
        :param sample_points: the amount of points that will be on the x axis
        :type int
        """
        self._sample_points = self._osa.query_ascii_values('SMPL?')[0]
        return self._sample_points

    @sample_points.setter
    def sample_points(self, sample_points):
        if sample_points != self._sample_points:
            self._sample_points = sample_points
            self._osa.write('SMPL{:1.2f}'.format(sample_points))
            self._sample_points = self._osa.query_ascii_values('SMPL?')[0]
            if sample_points != self._sample_points:
                self.logger.warning("The sample points value did not set in OSA")

    @property
    def sensitivity(self):
        """"
        The sensitivity of the osa machine
        :param sensitivity_string: a string that says how much the sensitivity must be
        :type string
        """
        self._sensitivity = int(self._osa.query_ascii_values('SENS?')[0])
        return self._sensitivities[self._sensitivity - 1]

    @sensitivity.setter
    def sensitivity(self, sensitivity_string):
        if sensitivity_string in self._sensitivities:
            sensitivity_number = self._sensitivities.index(sensitivity_string)
        else:
            self.logger.warning("the sensitivity string is not right")
            return
        if sensitivity_number != self._sensitivity:
            self._sensitivity = sensitivity_number
            self._osa.write(self._sens_commands[self._sensitivity - 1])
            if sensitivity_number != self._sensitivity:
                self.logger.warning('Value not set in OSA')

    def perform_single_sweep(self):
        """
        Gives a command to the osa machine to perform a single sweep.
        """
        self._osa.write('SGL')

    def get_data(self):
        """
        Calculates the data created with the single sweep.
        Wait for OSA to finish before grabbing data

        :return wav: an list of the wavelengths, spec an list with spectrum data.
        :rtype wav: a list of floats and a list of floats
        """
        wav = self._osa.query_ascii_values('WDATA')[1:]
        spec = self._osa.query_ascii_values('LDATA')[1:]

        return wav, spec

    def finalize(self):
        """
        This method closes the connection to the osa machine.
        This method should be called when all the things are done which you wanted to do with
        osa machine.
        """
        self.logger.info('Closing connection to device.')
        self._osa.close()
        self._is_initialized = False

    def query(self, msg):
        """ writes into the device message

        :param msg: command to write into the device port
        :type msg: string
        :return ans: answer from the osa
        :rtype ans: string
        """
        print(self._osa.session)
        self.logger.debug('Writing into the osa machine:{}'.format(msg))
        self.write(msg)
        ans = self.read()
        return ans


    def set_settings_for_osa(self):
        """
        in this method the parameters for the osa machine are set with
        hand in order to quickly get results.
        """
        # start and end between 600.00 and 1750.00
        self.start_wav = 900.00
        self.end_wav = 1200.00
        # allowed are 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0
        self.optical_resolution = 1.00
        #recommended sample points are: 1+(2 *(end_wav-start_wav)/ optical_resolution)
        self.sample_points = 601.00


# class OsaControllerDummy(OsaController):
#     """
#     Example Controller Dummy for the Osa machine
#     ========================
#     A dummy version of the Example Controller.
#     ========================
#
#     In essence we have the same methods and we re-write the query to answer something meaningful but
#     without connecting to the real device.
#     """
#
#     def query(self, msg):
#         """ writes into the device msg
#
#         :param msg: command to write into the device port
#         :type msg: string
#         """
#         self.logger.debug('Writing into the dummy device:{}'.format(msg))
#         ans = 'A general dummy answer'
#         return ans
#     def read(self):
#         """ Fake read that returns always the value in the dictionary FAKE RESULTS.
#
#         :return: fake result
#         :rtype: string
#         """
#         return 'A'
#     def write(self, msg):
#         """ Writes into the device
#
#         :param msg: message to be written in the device port
#         :type msg: string
#         """
#         self.logger.debug('Writing into the device:{}'.format(msg))
#     def idn(self):
#         """ Identify command
#
#         :return: identification for the device
#         :rtype: string
#         """
#         self.logger.debug('Ask id to example device.')
#         return 'ExampleController device'
#
#     def initialize(self):
#         """ Dummy initialize"""
#         self.logger.info('Dummy initialize')
#         self._is_initialized = True


if __name__ == "__main__":
    from hyperion import _logger_format, _logger_settings

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    dummy = True  # change this to false to work with the real device in the COM specified below.

    if dummy:
        my_class = OsaControllerDummy
    else:
        my_class = OsaController

    with my_class(settings={'dummy': dummy}) as dev:
        dev.initialize()
        #change paramaters
        print('OSA start wav is {}'.format(dev._start_wav))
        dev.start_wav = 800.00
        print('OSA start wav is {}'.format(dev._start_wav))
        print("-"*40)
        print('OSA end wav is {}'.format(dev._end_wav))
        dev.end_wav = 900.00
        print('OSA start wav is {}'.format(dev._end_wav))
        print("-" * 40)
        print('OSA optical resolution is {}'.format(dev._optical_resolution))
        dev.optical_resolution = 1.0
        print('OSA optical resolution is {}'.format(dev._optical_resolution))
        print("-" * 40)
        print('OSA sample points is {}'.format(dev._sample_points))
        dev.sample_points = 161
        print('OSA sample points is {}'.format(dev._sample_points))
        print("-" * 40)
        print('OSA sensitivity is {}'.format(dev._sensitivity))
        dev.sensitivity = "high1"
        print('OSA sensitivity is {}'.format(dev._sensitivity))

        #dev.set_settings_for_osa()

        dev.perform_single_sweep()
        dev.wait_for_osa()
        #dev.get_data()
        dev.finalize()



