"""
===========================
Test Cobolt08NLD controller
===========================

This class aims to unit_test the correct behaviour of the controller class: Cobolt08NLD.py

If you have changed something in the controller layer, you should check that the
functionalities of if are still running properly by running this class and adding
a method to unit_test the new methods in the controller, if any.


"""
from hyperion import logging
from time import sleep
from hyperion import Q_
from hyperion.controller.cobolt.cobolt08NLD import Cobolt08NLD


class UTestCobolt08NLD():
    """ Class to unit_test the Cobolt08NLD controller."""
    def __init__(self, settings):
        """ initialize

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Created UTestLcc25 class.')
        self.logger.info('Testing in dummy={}'.format(settings['dummy']))
        self.dummy = settings['dummy']
        port = settings['port'].split('COM')[-1]
        if self.dummy:
            self.dev = LccDummy(settings)
        else:
            self.dev = Cobolt08NLD.via_serial(port)

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



if __name__ == "__main__":
    dummy_mode = [False]  # add false here to also unit_test the real device with connection
    true_port = 'COM5'
    for dummy in dummy_mode:
        print('Running dummy={} tests.'.format(dummy))
        # run the tests
        with UTestCobolt08NLD(settings={'port':true_port, 'dummy':dummy}) as t:

            print('Identification: {}'.format(t.dev.idn))
            print('Enabled = {}'.format(t.dev.enabled))
            print('used hours = {} hs'.format(t.dev.operating_hours))
            print('Laser mode: {}'.format(t.dev.ctl_mode))
            print('Laser interlock state: {}'.format(t.dev.interlock))
            print('Autostart status: {}'.format(t.dev.autostart))
            print('Power setpoint: {}'.format(t.dev.power_sp))
            t.devpower_sp = Q_(150, 'milliwatt')
            print('Power setpoint: {}'.format(t.dev.power_sp))
            t.devpower_sp = 200
            print('Power setpoint: {}'.format(t.dev.power_sp))
            print('Output power now: {}'.format(t.dev.power))

        print('\n\n\n Done with dummy={} tests. \n\n\n NO PROBLEM, you are great!!!! \n\n\n '.format(dummy))




