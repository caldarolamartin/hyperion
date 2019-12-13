# -*- coding: utf-8 -*-
"""
=====================================
Instrument for the function generator
=====================================

This class (fun_gen.py) is the model to control the function generator agilent33522A
It ads the use of units with pint.

"""
import os
import yaml
from time import sleep
from hyperion import ur, root_dir
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import logging

class FunGen(BaseInstrument):
    """ This class is to control the function generator.

    :param settings: to parse the settings needed. Some keys are needed: 'controller' and 'instrument_id'
    :type settings: dict
    """
    def __init__(self, settings):
        """
         It needs a settings dictionary that contains the following fields (mandatory)

            * instrument_id: COM port name where the LCC25 is connected
            * dummy: logical to say if the connection is real or dummy (True means dummy)
            * controller: this should point to the controller to use and with / add the name of the class to use

        Note: When you set the setting 'dummy' = True, the controller to be loaded is the dummy one by default,
        i.e. the class will overwrite the 'controller' with 'hyperion.controller.agilent.agilent33522a/agilent33522aDummy'

        """
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.apply_defaults = settings['apply_defaults']
        self.logger.debug('Apply defaults: {}'.format(self.apply_defaults))

        if self.apply_defaults:
            self.defaults_file = settings['defaults_file']
        else:
            self.defaults_file = None
            self.logger.debug('No file is loaded since we do not apply default settings.')

        self.dummy = settings['dummy']
        if self.dummy:
            self.logger.info('Working in dummy mode')

        self.instrument_id = settings['instrument_id']
        self.name = 'Agilent Fun Gen'


        self.logger.info('Initializing device Agilent33522A number = {}'.format(self.instrument_id))

        self.controller.initialize()
        self.CHANNELS = self.controller.CHANNELS
        self.FUN = self.controller.FUNCTIONS
        self.DEFAULTS = {}
        self.load_defaults(self.apply_defaults, self.defaults_file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def idn(self):
        """
        Ask for the identification

        :return: message with identification from the device
        :rtype: string
        """
        return self.controller.idn()

    def load_defaults(self, apply, filename=None):
        """ This loads the default configuration and applies it, depending on the
         apply parameter. The information is kept in the variable self.DEFAULTS

        :param apply: decides weather to apply this settings or not
        :type apply: logical
        :param filename: location for the config_agilent33522A.yml to use. If not given uses
        :param filename: location for the config_agilent33522A.yml to use. If not given uses
        the default config file in the model/function_generator folder
        """
        if filename is None:
            filename = os.path.join(root_dir, 'instrument', 'function_generator', 'config_agilent33522A.yml')

        with open(filename, 'r') as f:
            d = yaml.load(f, Loader=yaml.FullLoader)
            self.logger.info('Loaded fun_gen configuration file: {}'.format(filename))

        self.DEFAULTS = d

        if apply:
            self.logger.info('Applying defaults from the configuration file.')
            self.logger.debug('Dict to use: {}'.format(self.DEFAULTS['defaults']))

            for di in self.DEFAULTS['defaults']:
                ch = di['channel']
                self.logger.info('Applying defaults to channel {}'.format(ch))

                if ch not in self.CHANNELS:
                    raise Warning('The channel "{}" is not recognized by this instrument.'.format(ch))

                self.logger.debug('Applying waveform = {}'.format(di['waveform']))
                self.set_waveform(ch, di['waveform']['function'])
                sleep(0.1)

                self.logger.debug('Applying Frequency = {}'.format(di['waveform']['frequency']))
                self.set_frequency(ch, ur(di['waveform']['frequency']))
                sleep(0.1)

                self.logger.debug('Applying Voltage limit high={} and low={}'.format(di['limit_high'],
                                                                                     di['limit_low']))
                self.set_voltage_limits(ch, ur(di['limit_high']), ur(di['limit_low']))
                self.logger.debug('Turning on voltage limits')
                self.enable_voltage_limits(ch, True)
                sleep(0.1)

                self.logger.debug('Applying High Voltage {}'.format(di['waveform']['high']))
                self.set_voltage_high(ch, ur(di['waveform']['high']))
                sleep(0.1)

                self.logger.debug('Applying Low Voltage {}'.format(di['waveform']['low']))
                self.set_voltage_low(ch, ur(di['waveform']['low']))
                sleep(0.1)

                self.logger.debug('Setting status {} for channel.'.format(di['output']))
                self.enable_output(ch, di['output'])
                sleep(0.1)

                self.logger.info('Error info: {}.'.format(self.get_system_error()))
        else:
            self.logger.info('The default settings were not applied.')

    def get_system_error(self):
        """ This functions returns the error message

        :return: error message
        :rtype: string

        """
        error = self.controller.get_system_error()
        return error

    def get_voltage_vpp(self, channel):
        """
        Gets the peak-to-peak voltage of the channel.

        :param channel: Channel number. Range depends on device
        :type channel: int

        :return: current peak to peak voltage
        :rtype: pint quantity
        """
        value = self.controller.get_voltage(channel)
        value = value * ur('volt')
        return value

    def set_voltage_vpp(self, channel, value):
        """
        Sets the peak-to-peak voltage of the channel.

        :param channel: Port number. Range depends on device
        :type channel: int
        :param value: peak to peak voltage to set
        :type value: pint quantity

        :return: current peak to peak voltage
        :rtype: pint quantity

        """

        self.controller.set_voltage(channel, value.m_as('volt'))
        return value

    def get_voltage_offset(self, channel):
        """
        Gets the peak-to-peak voltage of the channel.

        :param int channel: Channel number. Range depends on device
        :type channel: int

        :return: current offset for the channel
        :rtype: pint quantity
        """
        value = self.controller.get_voltage_offset(channel)
        value = value * ur('volt')
        return value

    def set_voltage_offset(self, channel, value):
        """
        Sets the DC offset voltage of the channel.

        :param channel: Channel number. Range depends on device
        :type channel: int
        :param value: The input value in Volts
        :type pint quantity
        :return: current offset for the channel
        :rtype: pint quantity
        """
        self.controller.set_voltage_offset(channel, value.m_as('volt'))
        return value

    def get_voltage_high(self, channel):
        """
        Gets the high voltage value of the channel.

        :param channel: Channel number. Range depends on device
        :type channel: int

        :return: current high voltage for the channel
        :rtype: pint quantity
        """
        value = self.controller.get_voltage_high(channel)
        return value

    def set_voltage_high(self, channel, value):
        """
        Sets the high voltage value for the channel.

        :param channel: Channel number. (list in self.CHANNELS)
        :type channel: int
        :param value: The input value in Volts
        :type value: pint quantity

        :return: current high voltage for the channel
        :rtype: pint quantity
        """

        self.controller.set_voltage_high(channel, value.m_as('volt'))
        return value

    def get_voltage_low(self, channel):
        """
        Gets the low voltage value of the channel.

        :param channel: Channel number. Range depends on device
        :type channel: int

        :return: current low voltage for the channel
        :rtype: pint quantity
        """
        value = self.controller.get_voltage_low(channel)
        value = value * ur('volt')
        return value

    def set_voltage_low(self, channel, value):
        """
        Sets the low voltage value for the channel.

        :param channel: Channel number. (list in self.CHANNELS)
        :type channel: int
        :param value: voltage low to set to channel
        :type value: pint quantity

        :return: voltage set
        :rtype: pint quantity


        """
        self.controller.set_voltage_low(channel, value.m_as('volt'))
        return value

    def enable_output(self, ch, state):
        """ Enables the output to the device

        :param ch: channel to use
        :type ch: int
        :param state: type to set the output on and off (True and False, respectively)
        :type state: logical

        """
        self.logger.debug('Setting output state {} for channel {}'.format(state, ch))
        self.controller.enable_output(ch, state)

    def output_state(self):
        """ Gets the current state of the output

         :return: A list of with the state of all channels.
         :rtype: list of logical

         """
        ans = []
        for ch in self.CHANNELS:
            ans.append(self.controller.get_enable_output(ch))
        return ans

    def set_waveform(self, channel, fun):
        """ Sets the waveform to be generated. The functions available are
        FUNCTIONS = ['SIN','SQU','TRI','RAMP','PULS','PRBS','NOIS','ARB','DC']

        :param channel: channel to use
        :type channel: int
        :param fun: function to generate
        :type fun: string

        """
        self.logger.debug('trying to apply to channel {} the waveform: "{}". '.format(channel, fun))

        if fun not in self.FUN:
            raise Warning('The waveform {} is not in the supported waveforms of the fun gen. Supported'
                          'waveforms are: {}'.format(fun, self.FUN))

        self.controller.set_waveform(channel, fun)

    def get_waveform(self, channel):
        """ Sets the waveform to be generated. The functions available are
        FUNCTIONS = ['SIN','SQU','TRI','RAMP','PULS','PRBS','NOIS','ARB','DC']

        :param channel: Channel number
        :type channel: int
        :return: One of the FUNCTIONS

        """
        return self.controller.get_waveform(channel)

    def finalize(self, state=True):
        """ Closes the connection to the device

        """
        self.logger.info('Finalizing connection with fun_gen at port {}.'.format(self.instrument_id))

        if not state:
            self.logger.info('The output will be turned off for both channels.')
            for ch in self.CHANNELS:
                self.controller.enable_output(ch, False)
                sleep(0.1)
        else:
            self.logger.info('The output will be kept on.')

        self.controller.finalize()
        self.logger.info('Connection to fun_gen finalized.')

    def set_frequency(self, channel, freq):
        """ This functions sets the frequency output for the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param freq: Frequency to set
        :type freq: pint quantity

        """
        self.controller.set_frequency(channel, freq.m_as('hertz'))

    def get_frequency(self, channel):
        """ This functions gets the frequency output for the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int

        :return: frequency in the channel
        :rtype: pint quantity

        """
        f = self.controller.get_frequency(channel)
        f = f * ur('hertz')
        return f

    def set_voltage_limits(self, channel, high, low):
        """ This function generator can set a minimum and maximum voltage value that will not be exceeded
        to protect the device that is being feed.
        This function sets the values high and low as voltage limits. If this option is activated then the
        output will not exceed the given values.
        NOTE: setting the values does not activate this feature. To enable/disable it use the function


        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param high: upper voltage limit
        :type high: pint quantity
        :param low: lower voltage limit
        :type low: pint quantity
        """
        self.controller.set_voltage_limits(channel, high.m_as('volt'), low.m_as('volt'))

    def get_voltage_limits(self, channel):
        """ Gets the set values for the voltage limits, high and low.

        :param channel:  number of channel. it can be 1 or 2 for this model
        :type channel: int

        :return: array with [high_value, low_value]
        :rtype: pint quantity array

        """
        values = self.controller.get_voltage_limits(channel)
        self.logger.debug('Received value from the controller: {}'.format(values))

        if not self.dummy:
            value = values * ur('volt')
        else:
            value = 10000 * ur('volt')
            self.logger.warning('The voltage is invented since your are in dummy mode')

        return value

    def enable_voltage_limits(self, channel, state):
        """ This function enables the limits for the maximum and minimum voltage
            output that can be generated by each channel. Those values are set with
            the method set_voltage_limits(channel, high, low).

            This function enables this setting by putting state = true and disables
            it by putting state = false. When enable, setting a voltage outside the permitted
            values will give an error (not in python)

            :param channel: number of channel. it can be 1 or 2 for this model
            :type channel: int
            :param state: True to turn on, False to turn of
            :type state: logical
        """
        self.controller.enable_voltage_limits(channel, state)

    def get_voltage_limits_state(self, channel):
        """ This function gets the state of the voltage limits for the
        required channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int

        :return: current state of the channel voltage limits
        :rtype: logical

        """

        return self.controller.get_voltage_limits_state(channel)


if __name__ == '__main__':

    with FunGen(settings = {'instrument_id' : '8967', 'dummy' : False,
                            'controller' : 'hyperion.controller.agilent.agilent33522A/Agilent33522A',
                            'apply_defaults' : True, 'defaults_file' : None}) as d:

        print('Output state for channels = {}'.format(d.output_state()))

        # #### unit_test idn
        print('Identification = {}.'.format(d.idn()))
        # ####   unit_test output_state
        print('Output state = {}'.format(d.output_state()))

        # #### unit_test High and low voltage
        ch = 1
        V = 2.1*ur('volt')
        Vlow = -1.1 * ur('mvolt')
        print('High voltage value = {}.'.format(d.get_voltage_high(ch)))
        d.set_voltage_high(ch, V)
        print('High voltage value = {}.'.format(d.get_voltage_high(ch)))
        # #### unit_test Low voltage
        print('Low voltage value = {}. '.format(d.get_voltage_low(ch)))
        d.set_voltage_low(ch, Vlow)
        print('Low voltage value = {}. '.format(d.get_voltage_low(ch)))

        # #### unit_test vpp and offset voltage

        V = 0.25 * ur('volt')
        DC = 0.5 * ur('mvolt')
        # #### vpp and offset read
        print('Vpp voltage value = {}. '.format(d.get_voltage_vpp(ch)))
        print('DC offset voltage value = {}. '.format(d.get_voltage_offset(ch)))
        # set
        d.set_voltage_vpp(ch, V)
        d.set_voltage_low(ch, DC)
        # read again
        print('Vpp voltage value = {}. '.format(d.get_voltage_vpp(ch)))
        print('DC offset voltage value = {}. '.format(d.get_voltage_offset(ch)))
        # unit_test enable output
        # d.enable_output(ch,True)
        print('Output state = {}'.format(d.output_state()))

        # #### unit_test frequency

        F = 1 * ur('khertz')
        # read freq
        print('Freq = {}.'.format(d.get_frequency(ch)))
        # set
        d.set_frequency(ch, F)
        # read again
        print('Freq = {}.'.format(d.get_frequency(ch)))
        # #### unit_test wavefunction change
        ch = 1
        print(d.get_waveform(ch))
        d.set_waveform(ch, 'SQU')
        print(d.get_waveform(ch))
        # unit_test limit voltage functions
        ch = 1
        d.enable_voltage_limits(ch, False)
        # #### read state and values
        print('Limit voltage state = {}'.format(d.get_voltage_limits_state(ch)))
        print(d.get_voltage_limits(ch))
        # ####### set values and state
        print('SETTING limits')
        Vmax = 2*ur('volt')
        Vmin = -2*ur('volt')
        d.set_voltage_limits(ch, Vmax, Vmin)
        d.enable_voltage_limits(ch, True)
        ######## get state
        print(d.get_voltage_limits_state(ch))
        print(d.get_voltage_limits(ch))
        sleep(1)

    print(' \n \n Done ! \n \n')


