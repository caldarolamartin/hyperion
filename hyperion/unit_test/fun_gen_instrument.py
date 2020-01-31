"""
======================
Test FunGen instrument
======================

This class aims to unit_test the correct behaviour of the instrument class: fun_gen

If you have changed something in the controller and or instrument layer, you should check that the
functionalities of if are still running properly by running this class and adding
a method to unit_test the new methods in the instrument, if any.


NOTE: This is still not implemented as a class, it just runs commands using the instrument. The assertion
part has to be done, still.

:copyright: by Hyperion Authors, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.

"""
from hyperion import logging
from time import sleep
from hyperion import ur
from hyperion.instrument.function_generator.fun_gen import FunGen

class UTestFunGen():
    """ Class to unit_test the FunGen instrument."""

    def __init__(self, settings):
        """ initialize the unit_test class

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Created UTestFunGen class.')
        self.logger.info('UTesting in dummy = {}'.format(settings['dummy']))
        self.dummy = settings['dummy']
        self.inst = FunGen(settings)
        sleep(1)

    # the next two methods are needed so the context manager 'with' works.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def finalize(self):
        """ closes connection """
        self.inst.finalize()




if __name__ == "__main__":

    dummy_mode = [False]  # add false here to also unit_test the real device with connection
    id = '8967'
    for dummy in dummy_mode:
        print('Running dummy={} tests.'.format(dummy))
        # run the tests
        with UTestFunGen(settings = {'instrument_id' : '8967', 'dummy' : False,
                            'controller' : 'hyperion.controller.agilent.agilent33522A/Agilent33522A',
                            'apply_defaults' : True, 'defaults_file' : None}) as t:

            print('Identification = {}.'.format(t.inst.idn()))
            # #### unit_test High and low voltage
            ch = 1
            V = 2.1 * ur('volt')
            Vlow = -1.1 * ur('mvolt')
            print('High voltage value = {}.'.format(t.inst.get_voltage_high(ch)))
            t.inst.set_voltage_high(ch, V)
            print('High voltage value = {}.'.format(t.inst.get_voltage_high(ch)))
            # #### unit_test Low voltage
            print('Low voltage value = {}. '.format(t.inst.get_voltage_low(ch)))
            t.inst.set_voltage_low(ch, Vlow)
            print('Low voltage value = {}. '.format(t.inst.get_voltage_low(ch)))

            # #### unit_test vpp and offset voltage

            V = 0.25 * ur('volt')
            DC = 0.5 * ur('mvolt')
            # #### vpp and offset read
            print('Vpp voltage value = {}. '.format(t.inst.get_voltage_vpp(ch)))
            print('DC offset voltage value = {}. '.format(t.inst.get_voltage_offset(ch)))
            # set
            t.inst.set_voltage_vpp(ch, V)
            t.inst.set_voltage_low(ch, DC)
            # read again
            print('Vpp voltage value = {}. '.format(t.inst.get_voltage_vpp(ch)))
            print('DC offset voltage value = {}. '.format(t.inst.get_voltage_offset(ch)))
            # unit_test enable output
            # t.inst.enable_output(ch,True)
            print('Output state = {}'.format(t.inst.output_state()))

            # #### unit_test frequency

            F = 1 * ur('khertz')
            # read freq
            print('Freq = {}.'.format(t.inst.get_frequency(ch)))
            # set
            t.inst.set_frequency(ch, F)
            # read again
            print('Freq = {}.'.format(t.inst.get_frequency(ch)))
            # #### unit_test wavefunction change
            ch = 1
            print(t.inst.get_waveform(ch))
            t.inst.set_waveform(ch, 'SQU')
            print(t.inst.get_waveform(ch))
            # unit_test limit voltage functions
            ch = 1
            t.inst.enable_voltage_limits(ch, False)
            # #### read state and values
            print('Limit voltage state = {}'.format(t.inst.get_voltage_limits_state(ch)))
            print(t.inst.get_voltage_limits(ch))
            # ####### set values and state
            print('SETTING limits')
            Vmax = 2 * ur('volt')
            Vmin = -2 * ur('volt')
            t.inst.set_voltage_limits(ch, Vmax, Vmin)
            t.inst.enable_voltage_limits(ch, True)
            ######## get state
            print(t.inst.get_voltage_limits_state(ch))
            print(t.inst.get_voltage_limits(ch))
            sleep(1)

        print('\n\n\n Done with dummy={} tests. \n\n\n NO PROBLEM, you are great!!!! \n\n\n '.format(dummy))