# -*- coding: utf-8 -*-
"""
    ===============
    osa controller
    ===============

    This controller (osa_2.py) supplies one class with several methods to communicate
    with the osa machine from ando AQ6317B model: 1MODD18012_0074
"""
import visa
#import numpy as np
import matplotlib.pyplot as plt
from pyvisa.resources import serial
from hyperion.controller.base_controller import BaseController
import time


class Osa_2(BaseController):

    def __init__(self):
        super().__init__()
        self.__rm = visa.ResourceManager()
        self.__resource_list = self.__rm.list_resources()
        self.__osa = None
        self.__start_wav = 600.00
        self.__end_wav = 1750.00
        self.__optical_resolution = 0.5
        self.__sample_points = 161

        # print(self.__resource_list)
        # find OSA (GPIB device) in recource_list:

    def initialize(self):
        """ Initialize the device

        """
        if self.dummy:
            self.logger.info('Dummy device initialized')
        else:
            self.rsc = serial.Serial(port=self._port,
                                     baudrate=self.DEFAULTS['baudrate'],
                                     timeout=self.DEFAULTS['read_timeout'],
                                     write_timeout=self.DEFAULTS['write_timeout'])
            self.logger.info('Initialized device LCC at port {}.'.format(self._port))

        self._is_initialized = True
        time.sleep(0.5)
    def get_osa_device_in_resource_list(self):

        for dev in self.__resource_list:
            if dev[:4] == 'GPIB':
                self.__osa = self.__rm.open_resource(dev)
                if self.__osa.query("*IDN?")[:11] == 'ANDO,AQ6317': break
                self.__osa.close()

        self.__osa.read_termination = '\r\n'

    @property
    def start_wav(self):
        return self.__start_wav

    @start_wav.setter
    def start_wav(self, start_wav):
        # note that OSA works from 600 to 1750 nm
        self.__start_wav = start_wav

    @property
    def end_wav(self):
        return self.__end_wav

    @end_wav.setter
    def end_wav(self, end_wav):
        self.__end_wav = end_wav

    @property
    def optical_resolution(self):
        return self.__optical_resolution

    @optical_resolution.setter
    def optical_resolution(self, optical_resolution):
        # allowed are 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0
        self.__optical_resolution = optical_resolution

    @property
    def sample_points(self):
        return self.__sample_points

    @sample_points.setter
    def sample_points(self, sample_points):
        # recommend at the very least 1 + 2*(end_wav-start_wav)/optical_resolution
        self.__sample_points = sample_points

    def set_settings_for_osa(self):
        #TODO create parameters in self object
        self.__osa.write('RESLN{:1.2f}'.format(self.__optical_resolution))
        self.__osa.write('STAWL{:1.2f}'.format(self.__start_wav))
        self.__osa.write('STpWL{:1.2f}'.format(self.__end_wav))
        self.__osa.write('SMPL{}'.format(self.__sample_points))


    def perform_single_sweep(self):
        self.__osa.write('SGL')

    def get_data(self):
        # wait for OSA to finish before grabbing data

        time.sleep(5)

        wav = self.__osa.query_ascii_values('WDATA')[1:]
        spec = self.__osa.query_ascii_values('LDATA')[1:]
        #TODO install matplotlib or update the dependencies througe setting matplotlib in the dependecies.
        plt.plot(wav, spec, '.-')

if __name__ == "__main__":
    pass

#start_wav = 620.00  # max 2 decimals
#end_wav = 700.00  # max 2 decimals
#optical_resolution = 0.5
#sample_points = 161

#osa.write('RESLN{:1.2f}'.format(optical_resolution))
#osa.write('STAWL{:1.2f}'.format(start_wav))
#osa.write('STpWL{:1.2f}'.format(end_wav))
#osa.write('SMPL{}'.format(sample_points))

# perform a single sweep:
#osa.write('SGL')

# wait for OSA to finish before grabbing data

#time.sleep(5)

#wav = osa.query_ascii_values('WDATA')[1:]
#spec = osa.query_ascii_values('LDATA')[1:]

#plt.plot(wav, spec, '.-')



