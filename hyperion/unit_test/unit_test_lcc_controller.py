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
from hyperion.controller.thorlabs.lcc25 import Lcc25


class UTestLcc():
    """ Class to test the LCC25 controller."""
    def __init__(self):
        """ initialize

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Created UTestLcc25 class.')
        self.dev = Fy6800(port='COM6', dummy=True)
        self.dev.initialize()

        sleep(1)

    # the next two methods are needed so the context manager 'with' works.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def test_voltage(self):
        """ test setter and getter for the voltage1 """
        # # ask current voltage
        dev.get_voltage(1)
        #
        # #### set a new voltage
        V = 2 * ur('volt')
        dev.set_voltage(V, Ch=1)
        Vnew = dev.get_voltage(Ch=1)
        assert V == Vnew

if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with UTestLcc() as t:
        t.test_voltage()



