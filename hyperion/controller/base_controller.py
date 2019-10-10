# -*- coding: utf-8 -*-
"""
===============
Base controller
===============

This is a base class for a controller.
The idea is to use this class as the parent class of any driver you are writing by hand.
By doing so, you gain the possibility of using the context manner for the 'with' block
and you how which basic methods you should write.
We strongly recommend you also use the logging, so you can keep track of what is going on
with your program at every step.


"""
import logging

class BaseController():
    """ General class for controller. Use it as parent of your (home-made) controller.

    """
    def __init__(self, settings = {'port':'COM10', 'dummy': True} ):
        """ Init for the class

        """
        self.logger = logging.getLogger(__name__)
        self._is_initialized = False
        self._settings = settings

    # the next two methods are needed so the context manager 'with' works.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug('_is_initialized state: {}'.format(self._is_initialized))
        if self._is_initialized:
            self.finalize()
        else:
            self.logger.warning('Exiting the with before initializing.')

    def initialize(self):
        """ Starts the connection to the device.

        """
        self.logger.warning('Method used from the BaseController class')
        self.logger.info('Opening connection to device.')

    def finalize(self):
        """ This method closes the connection to the device.
        It is ran automatically if you use a with block

        """
        self.logger.warning('Method used from the BaseController class')
        self.logger.info('Closing connection to device.')

    def idn(self):
        """ Identify command

        """
        self.logger.warning('Method used from the BaseController class')
        self.logger.debug('Ask IDN to device.')
        return 'BaseController'

if __name__ == "__main__":
    print('you should not be running this file alone')