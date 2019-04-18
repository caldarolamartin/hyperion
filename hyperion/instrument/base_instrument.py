"""
===============
Base instrument
===============

This is a base class for an instrument (named model in PythonForTheLab book).
At this level we add more complex functionalities and some not-build in behaviour for the
device you are controlling.
The idea is to use this class as the parent class of any other instrument for which
you wrote the driver by hand (not using other library but the communication).


"""
import logging
import importlib
import yaml
from hyperion.controller.base_controller import BaseController

class BaseInstrument():
    """ General class for Instrument

    """
    def __init__(self):
        """ Init for the class

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class BaseInstrument created.')
        self.logger.warning('Method used from the BaseInstrument class')
        self.controller = BaseController()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def initialize(self, port):
        """ Starts the connection to the device in port

        :param port: port name to connect to
        :type port: string
        """
        self.logger.warning('Method used from the BaseInstrument class')
        self.logger.info('Opening connection to device using driver.')
        self.controller.initialize(port)

    def load_config(self, filename):
        """Loads the configuration file for the instrument. Needs a field called controller
        to know which controller to load

        :param filename: Path to the filename.
        :type filename: string
        """
        self.logger.debug('Loading configuration file: {}'.format(filename))

        with open(filename, 'r') as f:
            d = yaml.load(f)
            self.logger.info('Using configuration file: {}'.format(filename))

        self.config = d

    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.warning('Method used from the BaseInstrument class')
        self.logger.info('Closing connection to device.')
        self.controller.finalize()

    def idn(self):
        """ Identify command

        """
        self.logger.warning('Method used from the BaseInstrument class')
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn()

    def load_controller(self, controller_string):
        """ Loads controller

        :param controller_string: dictionary with the field controller
        :type controller_string: dict
        """
        self.logger.debug('Loading the controller: {}'.format(controller_string))
        controller_name, class_name = controller_string.split('/')
        self.logger.debug('Controller name: {}. Class name: {}'.format(controller_name, class_name))
        my_class = getattr(importlib.import_module(controller_name), class_name)
        instance = my_class()
        return instance


if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with BaseInstrument() as dev:
        dev.initialize('COM10')
        dev.idn()

