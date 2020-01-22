# -*- coding: utf-8 -*-
"""
==================
Example Instrument
==================

This is an example instrument, created to give developers a canvas to start their own instruments
for real devices. This is only a dummy device.

"""
from hyperion.core import logman as logging # another way to do it
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur
import numpy as np
from time import sleep

class ExampleInstrument(BaseInstrument):
    """ Example instrument. it is a fake instrument

    """
    def __init__(self, settings):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class ExampleInstrument created.')
        self.initialize()   # An Instrument should initialize at instantiation
                            # However it is recommended to place initializaton in a separate method. That way after
                            # instantiation it can still reconnect to a controller with finalize() and initialize()

    def initialize(self):
        """ Starts the connection to the device"
        """
        self.logger.info('Opening connection to device.')
        self.controller.initialize()

    def finalize(self):
        """
        This is to close connection to the device.
        Note that the B
        """
        self.logger.info('Closing connection to device.')
        self.controller.finalize()

    def idn(self):
        """ Identify command

        :return: identification for the device
        :rtype: string

        """
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn()

    # Several

    def return_fake_voltage_datapoint(self):
        sleep(0.02)
        return np.random.random()*ur('V')

    def return_fake_datapoint(self):
        sleep(0.02)
        return np.random.random()

    def return_fake_1D_data(self, width=200):
        sleep(0.05)
        return np.random.random(width)

    def return_fake_2D_data(self, width=64, height=48):
        sleep(0.1)
        return np.random.random((height, width))

    def return_fake_3D_data(self, width=32, height=24, depth=8):
        sleep(0.2)
        return np.random.random((height, width, depth))

    @property
    def amplitude(self):
        """ Gets the amplitude value
        :return: voltage amplitude value
        :rtype: pint quantity
        """
        self.logger.debug('Getting the amplitude.')
        return self.controller.amplitude * ur('volts')

    @amplitude.setter
    def amplitude(self, value):
        """ This method is to set the amplitude
        :param value: voltage value to set for the amplitude
        :type value: pint quantity
        """
        self.controller.amplitude = value.m_as('volts')


if __name__ == "__main__":

    dummy = [True, False]
    for d in dummy:
        with ExampleInstrument(settings = {'port':'COM8', 'dummy' : d,
                                   'controller': 'hyperion.controller.example_controller/ExampleController'}) as dev:
            print(dev.amplitude)
            # v = 2 * ur('volts')
            # dev.amplitude = v
            # print(dev.amplitude)
            # dev.amplitude = v
            # print(dev.amplitude)

    print('done')