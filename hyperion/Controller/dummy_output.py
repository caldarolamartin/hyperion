"""
================
Dummy controller
================

This is a dummy device, simulated for developing and testing the code

"""
import logging
from base_controller import BaseController

class DummyOutput(BaseController):
    """ Dummy output device

    """
    def __init__(self):
        """ init of the class"""
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s -  %(funcName)2s() - %(message)s',
                            level=logging.DEBUG)

        self.logger.info('Class BaseController created.')
        self._amplitude = []

    def initialize(self, port):
        """ Starts the connection to the device in port

        :param port: port name to connect to
        :type port: string
        """
        self.logger.info('Opening connection to device.')

    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.info('Closing connection to device.')

    def idn(self):
        """ Identify command

        """
        self.logger.debug('Ask IDN to device.')
        return 'Dummy Output'

    def query(self, msg):
        """ writes into the device"""
        self.logger.debug('Writing into the device:{}'.format(msg))
        return 'Answer to: {}'.format(msg)

    def write(self, msg):
        """ writes into the device"""
        self.logger.debug('Writing into the device:{}'.format(msg))


    @property
    def amplitude(self):
        """ Gets the amplitude value"""
        self.logger.debug('Getting the amplitude.')
        return self._amplitude

    @amplitude.setter
    def amplitude(self, value):
        """ This method is to set the amplitude"""
        # would be nice to add a way to check that the value is within the limits of the device.
        if self._amplitude != value:
            self.logger.info('Setting the amplitude to {}'.format(value))
            self._amplitude = value
            self.write('A{}'.format(value))
        else:
            self.logger.info('The amplitude is already={}'.format(value))


if __name__ == "__main__":

    with DummyOutput() as dev:
        dev.initialize('COM10')
        print(dev.amplitude)
        dev.amplitude = 5
        print(dev.amplitude)


