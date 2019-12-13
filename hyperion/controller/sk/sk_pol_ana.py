# -*- coding: utf-8 -*-
"""
======================
SK polarization driver
======================

This class uses the 64bit dll from SK to use the SK polarization. For more details refer to the manual
of the device.

For now it only supports one polarization analyzer connected.

    :copyright: 2019 by Hyperion Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import ctypes
from hyperion import logging
from time import time, sleep
from hyperion.controller.base_controller import BaseController

class Skpolarimeter(BaseController):
    """ This is the controller for the SK polarization. Based on their dll.

        :param settings: dictionary with the entry 'dll_name' : 'SKPolarimeter' (default value)
        :type settings: dict

    """
    def __init__(self, settings):
        """ Init method for the class

        """
        super().__init__()  # runs the init of the base_controller class.
        self.logger = logging.getLogger(__name__)
        self.name = 'SK polarization'
        self.logger.debug('Is initialized state: {}'.format(self._is_initialized))

        # TODO: put this in a config file so the code doe not depend on the location (PC)
        path = 'C:/Users/mcaldarola/surfdrive/NanoCD/Setup/SK/SKPolarimeterMFC_VS2015_x64/x64/Release/'
        name = settings['dll_name']
        self.logger.debug('DLL to use: {}'.format(path + name))
        self.dll = ctypes.CDLL(path + name)
        self.logger.debug('DLL: {}'.format(self.dll))

        # this is the info needed to get the measurement point
        self.time_out = 300  # in ms
        self.vector_length = 13
        self.get_data_delay = 0.7   # in sec
        self.start_measurement_time = 0  # initialize the value

    def wait_to_measure(function):
        """ This function is meant to be used to delay the first measurement so the device
        is ready and producing data.
        It is used as a decorator.

        """
        def wait_to_measure_wrapper(self, *arg, **kw):
            while time() - self.start_measurement_time < self.get_data_delay:
                pass    # self.logger.debug('Waiting until the time has passed')
            res = function(self, *arg, **kw)
            return res
        return wait_to_measure_wrapper

    def initialize(self, wavelength = 630):
        """ Initiate communication with the SK polarization analyzer

        :param wavelength: the working wavelength in nm
        :type wavelength: int

        """
        self.wavelength = wavelength
        file = "C:\\unit_test.ini"
        wave = ctypes.c_int(int(wavelength))
        id = ctypes.c_int(int(self.id))
        self.logger.info('Initialization of SK polarimiter with ID = {} at wavelength {} nm. '
                         'save file: {}'.format(id.value, wave.value, file))

        func = self.dll.SkInitPolarimeterByID
        func.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]

        ans = func(self.id, br"C:\\unit_test.ini", wave)
        self.logger.debug('Answer from the SkInitPolarimeter: {}'.format(ans))
        if ans == 0:
            self._is_initialized = True

        self.logger.debug('Contrller _is_initialized state: {}'.format(self._is_initialized))

        return ans

    def get_wavelength(self):
        """ Get current wavelength

        :return: wavelength in nm
        :rtype: float

        """
        self.logger.debug('Getting wavelength from the device.')
        ans = self.dll.SkGetWavelengthByID(self.id)
        self.logger.debug('Wavelength: {} nm'.format(ans))

        return ans

    def finalize(self):
        """ Closing communication with device

        """
        ans = None
        if self._is_initialized:
            self.logger.info('Closing connection with device number: {}'.format(self.id))
            ans = self.dll.SkCloseConnectionByID(self.id)
            self.logger.debug('Answer from the SkCloseConnection: {}'.format(ans))
            self._is_initialized = False

        return ans

    def get_number_polarizers(self):
        """ Get the number of polarizers available in the system

        """
        self.logger.info('Getting the number of polarizers')
        ans = self.dll.SkGetNumberOfPolAnalyzers()
        self.logger.debug('Answer from SkGetNumberOfPolAnalyzers: {}'.format(ans))
        self.logger.info('Number of polarization analysers: {}'.format(ans))
        self.number_of_analyzers = int(ans)
        return ans

    def get_device_information(self):
        """ Get SK polarization analyzer information. This function adds the obtained values
        to the properties of the class so they are accessible for all the functions

        :return: reading answer from the function
        :rtype: int
        """
        len = ctypes.c_int(0)
        id = ctypes.c_int(0)
        serial_number = ctypes.c_int(0)
        min_w = ctypes.c_int(0)
        max_w = ctypes.c_int(0)
        self.logger.info('Getting device information')
        self.logger.debug('Sending to device: len: {}, id: {}, serial: {}, min: {}, max: {}. '.format(
            len, id, serial_number, min_w, max_w))
        ans = self.dll.SkGetDeviceInformation(len, ctypes.pointer(id), ctypes.pointer(serial_number),
                                              ctypes.pointer(min_w), ctypes.pointer(max_w))
        self.logger.debug('Answer from SkGetDeviceInformation: {}'.format(ans))
        self.id = int(id.value)
        self.serial_number = int(serial_number.value)
        self.min_w = int(min_w.value)
        self.max_w = int(max_w.value)
        self.logger.info('ID: {}'.format(self.id))
        self.logger.info('Serial number: {}'.format(self.serial_number))
        self.logger.info('Min Wavelength: {} nm'.format(self.min_w))
        self.logger.info('Max Wavelength: {} nm'.format(self.max_w))
        return ans

    def start_measurement(self):
        """ start measurement """
        self.logger.info('Starting a measurement with device: {}'.format(self.id))
        ans = self.dll.SkStartMeasurementByID(self.id)
        self.start_measurement_time = time()
        self.logger.debug('Answer: {}'.format(ans))

        return ans

    def stop_measurement(self):
        """ start measurement """
        self.logger.info('Stopping a measurement with device: {}'.format(self.id))
        ans = self.dll.SkStopMeasurementByID(self.id)
        self.logger.debug('Answer: {}'.format(ans))

        return ans

    @wait_to_measure
    def get_measurement_point(self):
        """ Get measurement point. The command start_measurement should have been called before
        using this method.
        it appends the data obtained (13 values with different meaning) to the data property of the class


        :return: v: a vector with the values given by the device
        :rtype: v: float

        """
        #self.logger.debug('Getting data from device')
        time_out = ctypes.c_ulong(self.time_out)  # 100ms timeout
        len = ctypes.c_int(self.vector_length)

        # create the array to give as an input to the dll function
        data = (ctypes.c_double * self.vector_length)()

        #self.logger.debug(
        #    'Sending to device: id: {}, time out: {}, data: {}, len: {}. '.format(self.id, time_out, data, len))
        ans = self.dll.SkGetMeasurementPointByID(self.id, time_out, ctypes.cast(data, ctypes.POINTER(ctypes.c_double)),
                                                 len)
        #self.logger.debug('Answer from device: {}'.format(ans))

        v = []
        for i in range(self.vector_length):
            v.append(data.__getitem__(i))
            #self.logger.debug('result {}: {}'.format(i, data.__getitem__(i)))

        if ans == 0:
            #self.logger.debug('Measurement OK')
            pass
        elif ans == -1:
            self.logger.warning('The length indicated for the vector is wrong')
        elif ans == -4:
            self.logger.warning('Measurement signal too high: data may be wrong.')
        elif ans == -3:
            self.logger.warning('TIMEOUT occurred')

        return v


class SkpolarimeterDummy(Skpolarimeter):
    """ This is the dummy controller for the SK polarization. Based on their dll.

    """
    # def __init__(self, settings):
    #     """ Init method for the class
    #
    #     """
    #     super().__init__(settings=settings)  # runs the init of the base_controller class.
    #     self.logger = logging.getLogger(__name__)
    #     self.name = 'SK polarization Dummy'
    #     self.logger.warning('Dummy not implemented yet')
    pass


if __name__ == "__main__":
    # logging.stream_level('DEBUG')

    with Skpolarimeter(settings = {'dll_name': 'SKPolarimeter'}) as s:
        # get the info needed to open connection
        s.get_number_polarizers()
        s.get_device_information()
        # open connection
        s.initialize()

        # unit_test wavelength
        #s.get_wavelength()

        # unit_test get data
        t = time()
        s.start_measurement()

        N = 5
        print('Getting data {} times'.format(N))
        for i in range(N):
            data = s.get_measurement_point()
            print('Elapsed time: {}'.format(time()-t))
            t = time()
            print('Data: {}'.format(data))

        s.stop_measurement()
