"""
=============================
Test Agilent33522A controller
=============================

This class aims to unit_test the correct behaviour of the controller class: agilent33522A.py

If you have changed something in the controller layer, you should check that the
functionalities of if are still running properly by running this class and adding
a method to unit_test the new methods in the controller, if any.


"""
import logging
from time import sleep
from hyperion import ur
from hyperion.controller.agilent.agilent33522A import Agilent33522A, Agilent33522ADummy


class UTestAgilent33522A():
    """ Class to unit_test the LCC25 controller."""

    CHANNELS = [1,2]

    def __init__(self, settings):
        """ initialize

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Created UTestAgilent33522A class.')
        self.logger.info('Testing in dummy={}'.format(settings['dummy']))
        self.dummy = settings['dummy']
        if self.dummy:
            self.dev = Agilent33522ADummy(settings)
        else:
            self.dev = Agilent33522A(settings)

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

    def test_all_amplitudes(self):
        """ To test all the amplitude related setters and getters"""

        setters = [self.dev.set_voltage, self.dev.set_voltage_offset, self.dev.set_voltage_high, self.dev.set_voltage_low]
        getters = [self.dev.get_voltage, self.dev.get_voltage_offset, self.dev.get_voltage_high, self.dev.get_voltage_low]
        values = [0.1, 0.5, 0.9, 0]
        for i in range(len(setters)):
            value = values[i]
            setter = setters[i]
            getter = getters[i]
            self.logger.info('Now testing the functions: {}, {}'.format(setter, getter))

            for ch in self.CHANNELS:
                self.logger.info('Voltage to set: {} in channel {}'.format(value, ch))
                setter(ch, value)
                Vnew = float(getter(ch))
                self.logger.info('Voltage read: {} in channel {}'.format(Vnew, ch))
                assert value == Vnew
                self.logger.info('Voltage assertion passed for channel: {}'.format(ch))
                self.logger.info('waiting 100ms')
                sleep(0.1)

        self.logger.info('Amplitude-related commands (setter and getters) unit_test passed.')

        return True

    def test_amplitude(self):
        """ unit_test setter and getter for the amplitude (Vpp) """
        self.logger.debug('Set and get voltage for both channels into unit_test.')

        for ch in self.CHANNELS:
            # # ask current voltage
            self.dev.get_voltage(ch)
            # #### set a new voltage
            V = 1.16
            self.logger.info('Voltage to set: {}'.format(V))
            self.dev.set_voltage(ch, V)
            Vnew = float(self.dev.get_voltage(ch))
            self.logger.info('Voltage read: {}'.format(Vnew))
            assert V == Vnew
            self.logger.info('Voltage assertion passed for channel: {}'.format(ch))

        self.logger.info('Amplitude (Vpp) set and read unit_test passed.')

    def test_enable_output(self):
        """ Test the enable output getter and setter """
        self.logger.debug('Starting unit_test on enable output')
        for ch in self.CHANNELS:
            for out in [True, False]:
                self.dev.enable_output(ch, out)
                ans = self.dev.get_enable_output(ch)
                self.logger.info('Read enable_output state: {}'.format(ans))
                assert out == ans
                self.logger.info('Output enable assertion passed for state: {}'.format(out))

        self.logger.info('Test enable output passed.')

    def test_freq(self):
        """ Test the getter and setter for the frequency command"""
        self.logger.debug('Starting unit_test on frequency')
        for ch in self.CHANNELS:
            for F in [10, 10.5e3]:
                self.logger.info('Freq to set: {} Hz'.format(F))
                self.dev.set_frequency(ch, F)
                ans = float(self.dev.get_frequency(ch))
                self.logger.info('read freq: {} Hz'.format(ans))
                assert F == ans
                self.logger.info('Freq assertion passed for freq: {}'.format(F))

        self.logger.info('Test Freq passed.')

    def test_mode(self):
        """ Test the mode methods"""
        self.logger.debug('Starting unit_test on mode mode')
        for m in [0, 1, 2]:
            self.dev.mode = m
            assert m == self.dev.mode
            self.logger.info('Mode assertion passed for mode: {}'.format(m))

        self.logger.info('Mode unit_test passed')

if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    dummy_mode = [False]  # add false here to also unit_test the real device with connection
    id = '8967'
    for dummy in dummy_mode:
        print('Running dummy={} tests.'.format(dummy))
        # run the tests
        with UTestAgilent33522A(settings = {'instrument_id':'8967', 'dummy': False}) as t:
            t.test_enable_output()
            sleep(0.1)
            t.test_freq()
            sleep(0.1)
            t.test_all_amplitudes()
            sleep(0.1)

        print('done with dummy={} tests.'.format(dummy))




