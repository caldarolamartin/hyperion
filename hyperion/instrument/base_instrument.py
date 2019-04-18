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


class BaseInstrument():
    """ General class for Instrument

    """
    def __init__(self, settings = {'port':'COM10', 'dummy': True,
                                   'controller': 'hyperion.controller.base_controller/BaseController'}):
        """ Init for the class

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class BaseInstrument created.')
        self.logger.warning('Method used from the BaseInstrument class')
        self._port = settings['port']
        self.dummy = settings['dummy']
        self.controller_class = self.load_controller(settings['controller'])
        self.controller = self.controller_class()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def initialize(self):
        """ Starts the connection to the device """
        self.logger.warning('Method used from the BaseInstrument class')
        self.logger.info('Opening connection to device using driver.')
        self.controller.initialize(self._port)

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

        :return: controller class
        :rtype: class
        """
        self.logger.debug('Loading the controller: {}'.format(controller_string))
        controller_name, class_name = controller_string.split('/')
        self.logger.debug('Controller name: {}. Class name: {}'.format(controller_name, class_name))
        my_class = getattr(importlib.import_module(controller_name), class_name)
        return my_class


if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with BaseInstrument() as dev:
        dev.initialize()
        dev.idn()

