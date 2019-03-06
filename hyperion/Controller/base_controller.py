"""
===============
Base controller
===============

This is a base class for a controller


"""
import logging

class BaseController():
    """ General class for controller

    """
    def __init__(self):
        """ Init for the class

        """
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s -  %(funcName)2s() - %(message)s',
                            level=logging.INFO)

        self.logger.info('Class BaseController created.')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

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
        return 'Name'


if __name__ == "__main__":

    with BaseController() as dev:

        dev.initialize('COM10')
        dev.idn()

