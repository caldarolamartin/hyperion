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

class BaseInstrument():
    """ General class for Instrument

    """
    def __init__(self, settings = {'port':'COM10', 'dummy': True}):
        """ Init for the class

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class BaseInstrument created with settings: {}'.format(settings))

        if 'dummy' in settings and settings['dummy']==True:
            if 'controller' in settings:
                if len(settings['controller']) < 5 or settings['controller'][-4]!='Dummy':
                    settings['controller'] += 'Dummy'

        self.controller_class = self.load_controller(settings)

        if 'via_serial' in settings:
            port = settings['via_serial'].split('COM')[-1]
            self.controller = self.controller_class.via_serial(port)
        elif 'via_gpib' in settings:
            self.logger.warning('NOT TESTED')
            port = settings['via_gpib'].split('COM')[-1]
            self.controller = self.controller_class.via_gpib(port) # to do
        elif 'via_usb' in settings:
            self.logger.warning('NOT TESTED')
            port = settings['via_usb'].split('COM')[-1]
            self.controller = self.controller_class.via_usb(port)  # to do
        else:
            self.controller = self.controller_class(settings)

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

    def load_controller(self, settings):
        """ Loads controller

        :param settings: dictionary with the field controller
        :type settings: dict

        :return: controller class
        :rtype: class
        """
        if 'controller' not in settings:
            raise NameError('The input dictionary needs to have a key called "controller" with a string pointing to the'
                            'right controller and the name of the class to use. ')
        else:
            self.logger.debug('Loading the controller: {}'.format(settings['controller']))
            controller_name, class_name = settings['controller'].split('/')
            self.logger.debug('Controller name: {}. Class name: {}'.format(controller_name, class_name))
            my_class = getattr(importlib.import_module(controller_name), class_name)
            return my_class


if __name__ == "__main__":
    print('you should not be running this file alone')


