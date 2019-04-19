"""
=====================
Test LCC25 controller
=====================

This class aims to test the correct behaviour of the controller class: LCC25.py

If you have changed something in the controller layer, you should check that the
functionalities of if are still running properly by running this class and adding
a method to test the new methods in the controller, if any.


"""
import logging
from time import sleep
from hyperion import ur
from hyperion.controller.thorlabs.lcc25 import Lcc


class UTestLcc():
    """ Class to test the LCC25 controller."""
    def __init__(self, dummy=True):
        """ initialize

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Created UTestLcc25 class.')
        self.logger.info('Testing in dummy={}'.format(dummy))
        self.dev = Lcc(port='COM6', dummy=dummy)
        self.dev.initialize()
        sleep(1)
        self.dummy = dummy

    # the next two methods are needed so the context manager 'with' works.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def finalize(self):
        """ closes connection """
        self.dev.finalize()


    def test_voltage(self):
        """ test setter and getter for the voltage1 """
        # # ask current voltage
        self.dev.get_voltage(1)
        #
        # #### set a new voltage
        V = 1 * ur('volt')
        self.logger.info('Voltage to set: {}'.format(V))
        self.dev.set_voltage(V, Ch=1)
        Vnew = self.dev.get_voltage(Ch=1)
        self.logger.info('Voltage read: {}'.format(Vnew))
        assert V == Vnew

if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with UTestLcc() as t:
        t.test_voltage()



