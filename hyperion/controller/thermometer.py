# -*- coding: utf-8 -*-
"""
    ==============
    RS 1316 driver
    ==============

    T

    :copyright: (c)
    :license: , see LICENSE for more details.
"""
import serial
from time import sleep, time
import logging


class Rs1316:
    """
    controller class for the driver aa_mod18012 from AA optoelelectronics.
    This class has all the methods to communicate using serial.

    NOTE: Our model has different ranges of frequency (see data sheet)
            Line 1 to 6: 82-151 MHz (this drives short wavelengths)
            Line 7 to 8: 68-82 MHz  (this drives long wavelengths)
    """

    # here some parameters I need
    DEFAULTS = {'baudrate': 9600,
                'parity': serial.PARITY_NONE,
                'write_timeout': 1,
                'read_timeout': 1}

    # units in order
    _units = ['C', 'F', 'K', 'F']

    # Thermocouple type (what we have at the time of writing is )
    _type = ['K', 'J', 'E', 'T', 'R', 'S', 'N']


    def __init__(self):
        """ This is the init for the controller aa_mod18012.
        It creates the instances of the objects needed to communicate with the device.


        """
        self.port = None
        self.rsc = None
        # logger
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s -  %(funcName)2s() - %(message)s',
                            level=logging.INFO)

        self.logger.info('Class Rs 1316 init. Created object.')

        self.T1 = []
        self.T1_units = []
        self.T2 = []
        self.T2_units = []
        self.Type = []
        self.last_call = []
        self.minimun_interval = 2   # sec

    def initialize(self, port):

        self.rsc = serial.Serial(port=port, baudrate=self.DEFAULTS['baudrate'], parity= self.DEFAULTS['parity'],
                      write_timeout = self.DEFAULTS['write_timeout'],
                      timeout = self.DEFAULTS['read_timeout'])

        self.last_call = time()

    def get_data_point(self):

        while time()-self.last_call < self.minimun_interval:
            pass

        if self.rsc is None:
            raise Warning('trying to read before initializing')

        self.last_call = time()

        r = self.rsc.read()

        if len(r) < 9:
            self.logger.error('The length of the answer is not long enough. Setting output to NaN')
            self.T1 = float('nan')
            self.T1_units = float('nan')
            self.T2 = float('nan')
            self.T2_units = float('nan')
            self.Type = float('nan')

        else:
            self.T1 = (r[2] * 256 + r[3]) / 10
            self.T1_units = self._units[r[1]]
            self.T2 = (r[5] * 256 + r[6]) / 10
            self.T2_units = self._units[r[4]]
            self.Type = self._type[r[7]]

        return [self.T1, self.T1_units, self.T2, self.T2_units]

    def finalize(self):

        self.rsc.close()


if __name__ == "__main__":

    ther = Rs1316()
    ther.initialize('COM12')

    for j in range(10):
        t = time()
        [T1, units1, T2, units2] = ther.get_data_point()
        print([T1, units1, T2, units2])
        print('Elapsed time = {}'.format(time()-t))


    ther.finalize()