# -*- coding: utf-8 -*-
"""
==================
Example controller
==================

This is an example of a controller with a fake (invented) device. It should help to gide
developers to create new controllers for real devices.


"""
import logging
from hyperion.controller.base_controller import BaseController

class ExampleController(BaseController):
    """ Example output device that does not connect to anything"""

    FAKE_RESPONSES = {'A': 1,
                     }

    def __init__(self, port, dummy=True):
        """ Init of the class.

        :param port: connection port to use
        :type port: str
        :param dummy: if the device connects to the real or not. in this case is useless, this is a dummy inivented device
        :type dummy: logical

        NOTE: this device is only dummy but the setting is here to emulate a real device.
        """
        super().__init__()
        self._port = port
        self.dummy = dummy
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class ExampleController created.')
        self._amplitude = []

    def initialize(self):
        """ Starts the connection to the device in port """
        self.logger.info('Opening connection to device in port {}.'.format(self._port))
        self._amplitude = self.query('A?')
        self._is_initialized = True     # this is to prevent you to close the device connection if you
                                        # have not initialized it inside a with statement

    def finalize(self):
        """ This method closes the connection to the device.
        It is ran automatically if you use a with block

        """
        self.logger.info('Closing connection to device.')

    def idn(self):
        """ Identify command

        :return: identification for the device
        :rtype: string
        """
        self.logger.debug('Ask IDN to device.')
        return 'Dummy Output controller'

    def query(self, msg):
        """ writes into the device msg

        :param msg: command to write into the device port
        :type msg: string
        """
        self.logger.info('Writing into the example device:{}'.format(msg))
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


class ExampleControllerDummy(ExampleController):
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
        ans = 'dummy answer'
        return ans



if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with ExampleController() as dev:
        dev.initialize('COM10')
        print(dev.amplitude)
        dev.amplitude = 5
        print(dev.amplitude)


