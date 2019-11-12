# -*- coding: utf-8 -*-
"""
===============
AOTF instrument
===============

This class (aa_aotf.py) is the model to connect to the AOTF using the controller aa_mod18012.py

The model is similar to the controller, but it adds specific functionalities such as units with Pint
and some calibrations.

 * **Wavelength calibration**: you can directly set the desired wavelength. For this it uses
   a look-up table and interpolation.

With this the class knows what voltages should be set when changing the wavelength.

"""
import os
import logging
import numpy as np
from time import sleep
from hyperion import ur, root_dir
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion.controller.aa.aa_modd18012 import AaModd18012


class AaAotf(BaseInstrument):
    """ This class is the instrument class for the AOTF driver.

    It implements another layer in the MVC design, adding calibration and units functionality.

    """
    DEFAULT_SETTINGS = {'frequency': [85, 95, 105, 115, 125, 145, 70, 80],
                        'power': [20, 20, 20, 20, 20, 20, 20, 20],
                        'state': False,
                        'mode': 'internal',
                        }

    def __init__(self, settings = {'port':'COM8', 'enable': False, 'dummy' : False,
                                   'controller': 'hyperion.controller.aa.aa_modd18012/AaModd18012'} ):
        """
        Init of the class.

        It needs a settings dictionary that contains the following fields (mandatory)

            * port: COM port name where the LCC25 is connected
            * enable: logical to say if the initialize enables the output
            * dummy: logical to say if the connection is real or dummy (True means dummy)
            * controller: this should point to the controller to use and with / add the name of the class to use

        Note: When you set the setting 'dummy' = True, the controller to be loaded is the dummy one by default,
        i.e. the class will overwrite the 'controller' with 'hyperion.controller.aa.aa_modd18012/AaModd18012Dummy'

        """
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self._port = settings['port']
        self.dummy = settings['dummy']

        #
        self.channel_in_use = None
        self.logger.info('Initializing device AOTF with Aotf_model at port = {}'.format(self._port))
        self.controller = AaModd18012(settings)
        self.controller.initialize()

        # loads the calibration file to transform freq to wavelength.
        cal_file = os.path.join(root_dir, 'instrument', 'aotf', 'lookup_table_cal_aotf_2019-02-05.txt')
        self.logger.info('Using freq to wavelength calibration for aotf from file {}'.format(cal_file))
        self.load_calibration(cal_file)

    def load_calibration(self, cal_file):
        """ This method loads the calibration file cal_file

            :param cal_file: calibration file complete path, including extension (txt expected)
            :type cal_file: string
        """
        self.logger.debug('Trying to load the calibration file: {}'.format(cal_file))
        cal = np.loadtxt(cal_file)
        self.logger.info('Loaded the calibration file: {}'.format(cal_file))
        self.cal_file = cal_file
        self.cal_data = cal
        aux = cal[:, 1]
        self.cal_freq = cal[aux.argsort(), 0]
        self.cal_wl = cal[aux.argsort(), 1]
        self.wavelength_lims = (np.min(self.cal_wl), np.max(self.cal_wl)) * ur('nanometer')
        self.cal_source_amplitude = cal[aux.argsort(), 2]
        self.cal_wl_width = cal[aux.argsort(), 3]

    def wavelength_to_frequency(self, wl, method='interp'):
        """ uses the calibration file to calculate the frequency needed to get the
        wavelength wl.

        :param wl: Wavelength (distance)
        :type wl: pint Quantity
        :param method: interpolation method ('interp' by default)
        :type method: string
        :return: Frequency value
        :rtype: pint Quantity
        """

        if wl.m_as('nanometer') < self.wavelength_lims[0].m_as('nanometers') \
                or wl.m_as('nanometer') > self.wavelength_lims[1].m_as('nanometers'):
            raise Exception('The required wavelength it is outside the calibration range')

        if method == 'interp':
            inter = np.interp(wl.m_as('nanometer'), self.cal_wl, self.cal_freq)
            F = np.round(inter, 3) * ur('megahertz')  # added the round
            self.logger.debug('Wavelength={} transforms to  Freq= {}, according to calibration file.'.format(wl, F))
        else:
            raise Exception("The called method for interpolation is not known.")
        return F

    def choose_channel(self, freq):
        """ This function selects an appropriated channel for a given frequency in the range
            supported by the device.

            It returns channel 1 or 7 depending on the desired frequency.

                - Channel 1 range: 82-151 MHz.
                - Channel 7 range: 68-82 MHz.

            :param freq: Frequency
            :type freq: pint Quantity
            :return: Channel number needed for the Frequency requested
            :rtype: int
            """
        self.logger.debug('Choosing channel for frequency {}.'.format(freq))
        if freq.m_as('megahertz') >= 82 and freq.m_as('megahertz') <= 151:
            ans = 1
        elif freq.m_as('megahertz') >= 68 and freq.m_as('megahertz') < 82:
            ans = 7
        else:
            raise Exception("The frequency {} is out of the range for the aotf driver. ".format(freq))

        self.logger.debug('Channel to use: {}.'.format(ans))

        return ans

    def set_all_values(self, channel, freq, power, state=True, mode='internal'):
        """ Sets the values for freq, power, state and mode for channel.
        It can be used to turn in to or off, with state.

        :param channel: channel to use (can be from 1 to 8 inclusive)
        :type channel: int
        :param freq: Frequency. Channels 1-6 supports(82,151)MHz and Channels 7 and 8, (68,82)MHz
        :type freq: float
        :param power: Power to set in dBm (0 to 22 )
        :type power: float
        :param state: True for on and False for off
        :type state: logical
        :param mode: 'internal' or 'external'
        :type mode: string
        :return: Response from the driver
        :rtype: string
    """
        self.logger.debug('Setting all parameters.')
        ans = self.controller.set_all(channel, freq.m_as('megahertz'), power, state, mode)
        return ans

    def set_defaults(self, channel):
        """ Sets channel to default values given in the dictionary
        at the beginning of the class.

        :param channel: channel value to put to default settings.
        :type channel: int
        """

        self.logger.info('Setting defaults for channel {}'.format(channel))
        self.logger.debug('Frequency: {}'.format(self.DEFAULT_SETTINGS['frequency'][channel - 1]))
        self.logger.debug('Power: {}'.format(self.DEFAULT_SETTINGS['power'][channel - 1]))
        self.logger.debug('State: {}'.format(self.DEFAULT_SETTINGS['state']))
        self.logger.debug('Mode: {}'.format(self.DEFAULT_SETTINGS['mode']))

        self.controller.set_all(channel, self.DEFAULT_SETTINGS['frequency'][channel - 1],
                            self.DEFAULT_SETTINGS['power'][channel - 1],
                            self.DEFAULT_SETTINGS['state'], self.DEFAULT_SETTINGS['mode'])

    def set_frequency_all_range(self, freq, power, state=True, mode='internal'):
        """ Automatically chooses channel 1 or 7 depending on the frequency requested and sets it.

            :param freq: Frequency. Supported range (68,151) MHz
            :type freq: pint Quantity
            :param power: Power to set in dBm (0 to 22 )
            :type power: float
            :param state: True for on and False for off
            :type state: logical
            :param mode: 'internal' or 'external'
            :type mode: string

        """
        # select the channel to turn on based on the frequency.
        ch = self.choose_channel(freq)
        if self.channel_in_use == ch:
            self.logger.debug('Continue with the same channel.')
        else:
            self.logger.info('Changed from channel {} to channel {}.'.format(self.channel_in_use, ch))
            self.logger.debug('Turn off channel {}.'.format(self.channel_in_use))
            if self.channel_in_use is not None:
                self.controller.enable(self.channel_in_use, False)
                sleep(1)
                self.controller.enable(ch, True)

        ans = self.set_all_values(ch, freq, power, state, mode)
        self.channel_in_use = ch
        return ans

    def set_wavelength(self, wl, power, state=True, mode='internal'):
        """ This sets the wavelength wl by using the calibration file.

        :param wl: This is the wavelength to set (it has to be in the range supported by the calibration file)
        :type wl: pint Quantity
        :param power: Power for the RF in the AOTF, in dBm. range = (0,22) dBm
        :type power: float
        :param state: to turn the output on or off
        :type state: logical
        :param mode: 'internal' or 'external'
        :type mode: string

        :return: output from the driver.
        :rtype: string
        """
        self.logger.debug('Get the frequency for the the wavelength: {}'.format(wl))
        F = self.wavelength_to_frequency(wl)
        self.logger.debug('Frequency for {} is = {}'.format(wl, F))
        self.logger.info(
            'Setting all parameters to get the wavelength={}, power={}, state={}, mode={}'.format(wl, power, state,
                                                                                                  mode))
        ans = self.set_frequency_all_range(F, power, state, mode)
        return ans

    def finalize(self):
        """ To close the connection to the device

        """
        self.controller.finalize()

    def blanking(self, state, mode='internal'):
        """ Define the blanking state. If True (False), all channels are on (off).
        It can be set to 'internal' or 'external', where external means that the modulation voltage
        of the channel will be used to define the channel output.

        :param state: State of the blanking
        :type state: logical
        :param mode: external or internal. external is used to follow TTL external modulation
        :type mode: string
        """
        self.controller.blanking(state, mode)

    def get_status(self):
        """ Gets the status of all channels in the controller

        """
        ans = self.controller.get_states()
        self.logger.info('Current state: {}'.format(ans))
        return ans


if __name__ == '__main__':
    from hyperion import _logger_format, _logger_settings

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    with  AaAotf(settings={'port':'COM10', 'dummy':False,
                           'controller': 'hyperion.controller.aa.aa_modd18012/AaModd18012'}) as d:

        d.blanking(True, mode='internal')

        # get status
        # d.get_states())

        # set default settings
        # d.set_defaults(1)
        # d.set_defaults(7)
        # print(d.driver.get_states())

        # turn off all channels and set default frequency
        # for ch in range(1,9):
        #   d.set_all_values(ch,0*ur('megahertz'),22,False,'internal')

        # print(d.driver.get_states())

        # ## freq scan in channel 1 with the driver function.
        # F = [90, 100, 150]*ur('megahertz')
        # for value in F:
        #     d.driver.set_all(1,value.m_as('megahertz'),22,True,'internal')

        # freq scan in channel 1 with the model method.
        # F = [90, 100, 110] * ur('megahertz')
        # for value in F:
        #     #d.set_all(1, value, 22, True, 'internal') # all input
        #     d.set_all(1, value, 22)  # all input

        # freq scan all range
        # F = [70, 80, 90, 105] * ur('megahertz')
        # for value in F:
        #     d.set_frequency_all_range(value, 22, True, 'internal') # all input
        # #     d.set_all(1, value, 22)  # all input
        # print(d.driver.get_states())

        # # check set wavelength
        # wl = np.linspace(500,700,4)* ur('nanometer')
        # print(wl)
        # for value in wl:
        #     print('This wavelength: {}'.format(value))
        #     # d.set_frequency_all_range(d.wavelength_to_frequency(value), 22, True, 'internal')
        #     d.set_wavelength(value, 22, True, 'internal')
        #
        # print('done')


        # to do a manual-saving wavelength scan with photothermal
        wl = np.linspace(625,700,4)* ur('nanometer')
        print(wl)
        for value in wl:
            print('This wavelength: {}'.format(value))
            # d.set_frequency_all_range(d.wavelength_to_frequency(value), 22, True, 'internal')
            d.set_wavelength(value, 22, True, 'external')
            ans = input('The wavelength is {}. Press enter for the next or press q for quiting... '.format(value))
            if ans=='q':
                print('Quiting')
                break

        print('done')