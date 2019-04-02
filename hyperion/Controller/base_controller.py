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
    """ General class for controller

    """
    def __init__(self):
        """ Init for the class

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class BaseController created.')
        self.logger.warning('Method used from the BaseController class')

    # the next two methods are needed so the context manager 'with' works.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def initialize(self, port):
        """ Starts the connection to the device in port

        :param port: port name to connect to
        :type port: string
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
    from hyperion import _logger_format
        logging.basicConfig(level=logging.DEBUG, format=_logger_format,
            handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                      logging.StreamHandler()])

    with BaseController() as dev:
        dev.initialize('COM10')
        dev.idn()

