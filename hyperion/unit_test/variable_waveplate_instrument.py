"""
=====================
Test LCC25 instrument
=====================

This class aims to unit_test the correct behaviour of the instrument class: variable_waveplate

If you have changed something in the controller and or instrument layer, you should check that the
functionalities of if are still running properly by running this class and adding
a method to unit_test the new methods in the instrument, if any.


"""
import logging
from time import sleep
from hyperion import ur
from hyperion.instrument.variable_waveplate.variable_waveplate import VariableWaveplate

class UTestVariableWaveplate():
    """ Class to unit_test the LCC25 controller."""
    def __init__(self, settings = {'port':'COM8', 'enable': False, 'dummy' : True,
                                       'controller': 'hyperion.controller.thorlabs.lcc25/Lcc'}):
        """ initialize the unit_test class

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Created UTestVariableWaveplate class.')
        self.logger.info('Testing in dummy={}'.format(dummy))
        self.dummy = dummy
        self.inst = VariableWaveplate(settings)
        sleep(1)

    # the next two methods are needed so the context manager 'with' works.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def finalize(self):
        """ closes connection """
        self.inst.finalize()


    def test_voltage(self):
        """ unit_test setter and getter for the voltage1 """
        self.logger.debug('Set and get voltage for both channels into unit_test.')
        CH = [1,2]
        for ch in CH:
            # #### set a new voltage
            V = 3.146 * ur('volt')
            self.logger.info('Voltage to set: {} in channel {}'.format(V, ch))
            self.inst.set_analog_value(ch, V)
            Vnew = self.inst.get_analog_value(ch)
            self.logger.info('Voltage read: {}'.format(Vnew))
            assert V == Vnew
            self.logger.info('Voltage assertion passed for channel: {}'.format(ch))

        self.logger.info('Voltage set and read unit_test passed.')

    def test_output(self):
        """ Test the output state"""
        self.logger.debug('Starting unit_test on output state')
        for out in [True, False]:
            self.inst.output = out
            assert out == self.inst.output
            self.logger.info('Output assertion passed for state: {}'.format(out))

        self.logger.info('Test output passed.')

    def test_freq(self):
        """ Test the freq command"""
        self.logger.debug('Starting unit_test on freq')
        for F in [10*ur('Hz'), 10.50*ur('Hz')]:
            self.inst.freq = F
            assert F == self.inst.freq
            self.logger.info('Freq assertion passed for freq: {}'.format(F))

        self.logger.info('Test Freq passed.')

    def test_mode(self):
        """ Test the mode methods"""
        self.logger.debug('Starting unit_test on mode mode')
        for m in [0, 1, 2]:
            self.inst.mode = m
            assert m == self.inst.mode
            self.logger.info('Mode assertion passed for mode: {}'.format(m))

        self.logger.info('Mode unit_test passed')

if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    dummy_mode = [False]  # add false here to also unit_test the real device with connection
    true_port = 'COM8'
    for dummy in dummy_mode:
        print('Running dummy={} tests.'.format(dummy))
        # run the tests
        with UTestVariableWaveplate(settings = {'port':'COM8', 'enable': False, 'dummy' : dummy,
                                       'controller': 'hyperion.controller.thorlabs.lcc25/Lcc'}) as t:
            t.test_voltage()
            t.test_output()
            t.test_freq()
            t.test_mode()

        print('done with dummy={} tests.'.format(dummy))




