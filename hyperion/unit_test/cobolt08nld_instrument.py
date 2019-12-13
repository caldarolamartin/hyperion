"""
===========================
Test cobolt08NLD controller
===========================

This class aims to unit_test the correct behaviour of the instrument class: cobolt08NLD

If you have changed something in the controller and or instrument layer, you should check that the
functionalities of if are still running properly by running this class and adding
a method to unit_test the new methods in the instrument, if any.


"""
from hyperion import logging
from time import sleep
from hyperion import Q_
from hyperion.instrument.laser.cobolt08nld import CoboltLaser

class UTestCobolt08NLD():
    """ Class to unit_test the Cobolt08NLD  controller."""
    def __init__(self, settings):
        """ initialize the unit_test class

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Created UTestVariableWaveplate class.')
        self.logger.info('Testing in dummy={}'.format(settings['dummy']))
        self.dummy = settings['dummy']
        self.inst = CoboltLaser(settings)
        sleep(1)

    # the next two methods are needed so the context manager 'with' works.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def finalize(self):
        """ closes connection """
        self.inst.finalize()

    def test_idn(self):
        """ Test the IDN function

        """
        print(self.inst.idn())

    def test_power_setpoint(self):
        """ Test the set and get for the power setpoint value

        """
        print('Curent power {}'.format(self.inst.power_sp))
        power_to_set =  Q_(110, 'mW')
        self.inst.power_sp = power_to_set
        assert power_to_set == self.inst.power_sp
        self.logger.info('Power setpoint assertion passed')


if __name__ == "__main__":

    dummy_mode = [False]  # add false here to also unit_test the real device with connection
    true_port = 'COM5'
    for dummy in dummy_mode:
        print('Running dummy={} tests.'.format(dummy))
        # run the tests
        with UTestCobolt08NLD(settings = {'dummy': dummy,
                                   'controller': 'hyperion.controller.cobolt.cobolt08NLD/Cobolt08NLD',
                                   'via_serial': true_port}) as t:
            t.test_idn()
            t.test_power_setpoint()


        print('\n\n\n Done with dummy={} tests. \n\n\n NO PROBLEM, you are great!!!! \n\n\n '.format(dummy))