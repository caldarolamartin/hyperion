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
from hyperion.controller.thorlabs.lcc25 import Lcc, LccDummy


class UTestLcc():
    """ Class to test the LCC25 controller."""
    def __init__(self, port='COM8', dummy=True):
        """ initialize

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Created UTestLcc25 class.')
        self.logger.info('Testing in dummy={}'.format(dummy))
        self.dummy = dummy
        if dummy:
            self.dev = LccDummy(port)
        else:
            self.dev = Lcc(port=port, dummy=dummy)

        self.dev.initialize()
        sleep(1)

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
        self.logger.debug('Set and get voltage for both channels into test.')
        CH = [1,2]
        for ch in CH:
            # # ask current voltage
            self.dev.get_voltage(ch)
            # #### set a new voltage
            V = 3.1459 * ur('volt')
            self.logger.info('Voltage to set: {}'.format(V))
            self.dev.set_voltage(ch, V)
            Vnew = self.dev.get_voltage(ch)
            self.logger.info('Voltage read: {}'.format(Vnew))
            assert V == Vnew
            self.logger.info('Voltage assertion passed for channel: {}'.format(ch))
        self.logger.info('Voltage set and read test passed.')

    def test_output(self):
        """ Test the output state"""
        self.logger.debug('Starting test on output state')
        for out in [True, False]:
            self.dev.output = out
            assert out == self.dev.output
            self.logger.info('Output assertion passed for state: {}'.format(out))
        self.logger.info('Test output passed.')

    def test_freq(self):
        """ Test the freq command"""
        self.logger.debug('Starting test on freq')
        for F in [10*ur('Hz'), 3.1416*ur('Hz')]:
            self.dev.freq = F
            assert F == self.dev.freq
            self.logger.info('Freq assertion passed for freq: {}'.format(F))
        self.logger.info('Test Freq passed.')


if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    dummy_mode = [True]  # add false here to also test the real device with connection
    true_port = 'COM8'
    for dummy in dummy_mode:
        print('Running dummy={} tests.'.format(dummy))
        # run the tests
        with UTestLcc(port=true_port, dummy=dummy) as t:
            t.test_voltage()
            t.test_output()
            t.test_freq()

        print('done with dummy={} tests.'.format(dummy))




