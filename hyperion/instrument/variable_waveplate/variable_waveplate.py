"""
======================
LCC25 (thorlabs) model
======================

This class (variable_waveplate_gui.py) is the model to drive the LCC25 variable waveplate controller.

It ads the use of units with pint and the wavelength calibration to obtain make the variable
waveplate a quarter waveplate for a given wavelength.


"""
import logging
import os
import numpy as np
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur, root_dir


class VariableWaveplate(BaseInstrument):
    """ This class is the model for the LCC25 analog voltage generator for the variable waveplate from thorlabs.


    """
    def __init__(self, settings = {'port':'COM8', 'enable': False, 'dummy' : True,
                                   'controller': 'hyperion.controller.thorlabs.lcc25/Lcc'} ):
        """
        Init of the class.

        It needs a settings dictionary that contains the following fields (mandatory)

            * port: COM port name where the LCC25 is connected
            * enable: logical to say if the initialize enables the output
            * dummy: logical to say if the connection is real or dummy (True means dummy)
            * controller: this should point to the controller to use and with / add the name of the class to use

        Note: When you set the setting 'dummy' = True, the controller to be loaded is the dummy one by default,
        i.e. the class will automatically overwrite the 'controller' with 'hyperion.controller.thorlabs.lcc25/LccDummy'

        """
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self._port = settings['port']
        # property
        self._output = False
        self._mode = 0

        self.logger.info('Initializing Variable Waveplate with settings: {}'.format(settings))
        # this is to load the calibration file
        self.calibration = {}
        self.logger.debug('Get the source path')
        cal_file = os.path.join(root_dir, 'instrument', 'variable_waveplate',
                                'lookup_table_qwp_voltage_calibration_2019-03-15.txt')
        self.logger.info('Using Variable Waveplate QWP calibration file: {}'.format(cal_file))
        self.load_calibration(cal_file)

        # initialize
        self.initialize()
        self.output = settings['enable']

    def initialize(self):
        """ initializes the connection with the controller """
        if not self.controller._is_initialized:
            self.logger.debug('Initializing')
            self.controller.initialize()

    def load_calibration(self, cal_file):
        """ This method loads the calibration file cal_file

            :param cal_file: calibration file complete path, including extension (txt expected)
            :type cal_file: string
        """
        self.logger.debug('Trying to load the calibration file: {}'.format(cal_file))
        cal = np.loadtxt(cal_file)
        self.logger.info('Loaded the calibration file: {}'.format(cal_file))
        self.calibration['file'] = cal_file
        self.calibration['original_data'] = cal
        aux = cal[:, 0]
        self.calibration['wavelength'] = cal[aux.argsort(), 0] * ur('nm')
        self.calibration['wavelength_limits'] = (np.min(self.calibration['wavelength']),
                                                 np.max(self.calibration['wavelength']))
        self.calibration['qwp'] = cal[aux.argsort(), 1] * ur('volt')
        self.calibration['qwp error'] = cal[aux.argsort(), 2] * ur('volt')
        #self.logger.debug('Calibration dictionary: {}'.format(self.calibration))
        self.logger.info('Done loading calibration.')

    def idn(self):
        """
        Ask for the identification
        """
        self.logger.info('Asking for identification.')
        return self.controller.idn()

    def get_analog_value(self, channel):
        """
        Gets the analog voltage of the channel.

        :param channel: Port number. Range depends on device
        :type channel: int
        :return: voltage: voltage in use for the channel
        :rtype: pint quantity
        """
        self.logger.debug('Asking for analog value at channel {}.'.format(channel))
        value = self.controller.get_voltage(channel)    # bits has no units
        return value

    def set_analog_value(self, channel, value):
        """
        Sets the analog voltage of the channel.

        :param channel: Port number. Range depends on device
        :type channel: int
        :param value: The input value in Volts between 0 and 25 (Pint type)
        :type value: pint quantity


        """
        self.logger.debug('Setting analog value {} for channel {}.'.format(value, channel))
        self.controller.set_voltage(channel, value)
        return value

    def quarter_waveplate_voltage(self, wavelength, method = 'lookup'):
        """
        This method gives the voltage needed to set on the LCC25 to get a
        quarter waveplate (QWP) behaviour for a given wavelength.
        It is based on the calibration data from date 2018-11-12
        and (so far) uses a linear fit to those data points.

        :param wavelength: The input wavelength
        :type wavelength: pint Quantity
        :param method: method to extrapolate between measured data points
        :type method: string
        :return: the QWP voltage
        :rtype: pint quantity

        """
        self.logger.debug('Getting the quarter waveplate voltage from calibration with method: {}'.format(method))

        if wavelength.m_as('nm') < self.calibration['wavelength_limits'][0].m_as('nm') or \
                wavelength.m_as('nm') > self.calibration['wavelength_limits'][1].m_as('nm'):

            self.logger.warning('The required wavelength is outside the calibration range for bias voltage')
            #todo set some value closer to the value that you should have.

        if method == 'lookup':
            x = self.calibration['wavelength']
            y = self.calibration['qwp']
            v = self.do_interp(wavelength, x, y)
        else:
            raise Warning('The required method to use for the calibration is not implemented.')

        self.logger.debug('The QWP voltage for {} is {}'.format(wavelength, v))
        return v

    def do_interp(self, w, x, y):
        """ This function interpolates the voltage value for the wavelength value w,
        using the calibration data (x,y) where x is wavelength and y is voltage

        :param w: desired wavelength
        :type w: pint quantity
        :param x: wavelength vector from calibration
        :type x: pint quantity
        :param y: calibrated voltage values
        :type y: pint quantity

        :return: the voltage for the desired wavelength
        :rtype: pint quantity

        """
        self.logger.debug('Wavelength to interpolate: {}'.format(w))
        #self.logger.debug('x: {} \n y: {}'.format(x, y))
        value = np.interp(w.m_as('nm'), x.m_as('nm'), y.m_as('volt') )
        self.logger.debug('interpolated value: {}'.format(value))
        return value * ur('volt')

    def set_quarter_waveplate_voltage(self, ch, wavelength):
        """
        This method sets the quarter waveplate (QWP) voltage to the variable waveplate
        for a given wavelength.

        :param ch: channel to use
        :type ch: int
        :param wavelength: The input wavelength
        :type wavelength: pint Quantity
        :return: the voltage set to the controller
        :rtype:  pint quantity

        """
        self.logger.debug('Getting the quarter waveplate voltage')
        v = self.quarter_waveplate_voltage(wavelength)
        self.logger.debug('The QWP voltage for {} is {}'.format(wavelength, v))
        self.logger.debug('Setting the voltage to the QWP voltage on channel {}'.format(ch))
        self.mode = 1
        self.set_analog_value(ch, v)
        self.controller.output = True

        return v

    def finalize(self, state=False):
        """ Closes the connection to the device

        """
        self.logger.info('Finalizing connection with Variable Waveplate')
        self.controller.output = state
        self.controller.finalize()

    @property
    def freq(self):
        """ Modulation frequency when the operation mode is 'modulation' (mode = 0)

        : getter :

        Asks for the current frequency

        :return: The frequency value
        :rtype: pint quantity

        : setter :

        :param F: frequency in Hz. It can be any value between 0.5 and 150Hz.
        :type F: pint Quantity

        """
        self.logger.debug('Ask for the current frequency.')
        ans = self.controller.freq
        self._freq = ans
        return self._freq

    @freq.setter
    def freq(self, F):
        self._freq = F
        self.controller.freq = F
        self.logger.info('Changed frequency to {} '.format(F))

    @property
    def output(self):
        """ Tells if the output is enabled or not.

        :getter:
        :return: output state
        :rtype: logical

        :setter:
        :param state: value for the amplitude to set in Volts
        :type state: logical

        """
        self.logger.debug('Asking for the output state')
        self._output = self.controller.output
        return self._output

    @output.setter
    def output(self, state):
        self.logger.debug('Setting the output state to {}'.format(state))
        self._output = state
        self.controller.output = state
        #return self._output

    @property
    def mode(self):
        """ Operation mode

        The possible modes are:

        1 = 'Voltage1' : sends a 2kHz sin wave with RMS value set by voltage 1

        2 = 'Voltage2' : sends a 2kHz sin wave with RMS value set by voltage 2

        0 = 'Modulation': sends a 2kHz sin wave modulated with a square wave where voltage 1
        is one limit and voltage 2 is the second. the modulation frequency can be
        changed with the command 'freq' in the 0.5-150 Hz range.

        : getter :

        Gets the current mode

        : setter :

        Sets the mode

        :param mode: type of operation.
        :type mode: int

        """
        self.logger.debug('Getting the mode of operation')
        self._mode = self.controller.mode
        return self._mode

    @mode.setter
    def mode(self, mode):
        self.controller.mode = mode
        self.logger.info('Changed to mode "{}" '.format(mode))
        self._mode = mode


if __name__ == '__main__':
    from hyperion import _logger_format, _logger_settings

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])


    dummy_mode = [False] # add here false to unit_test the code with the real device

    for dummy in dummy_mode:
        print('Running in dummy = {}'.format(dummy))
        with VariableWaveplate(settings = {'port':'COM8', 'enable': False, 'dummy' : dummy,
                                       'controller': 'hyperion.controller.thorlabs.lcc25/Lcc'}) as dev:
            # output status and set
            # logging.info('The output is: {}'.format(dev.output))
            # dev.output = True
            # logging.info('The output is: {}'.format(dev.output))
            #
            # # mode
            # logging.info('The mode is: {}'.format(dev.output))
            # for m in range(3):
            #     dev.mode = m
            #     logging.info('The mode is: {}'.format(dev.output))
            #
            # # set voltage for both channels
            # for ch in range(1, 2):
            #     logging.info('Current voltage for channel {} is {}'.format(ch, dev.get_analog_value(ch)))
            #     dev.set_analog_value(ch, 1 * ur('volts'))
            #     logging.info('Current voltage for channel {} is {}'.format(ch, dev.get_analog_value(ch)))
            #
            # # unit_test freq
            # logging.info('Current freq: {}'.format(dev.freq))
            # Freqs = [1, 10, 20, 60, 100] * ur('Hz')
            # for f in Freqs:
            #     dev.freq = f
            #     logging.info('Current freq: {}'.format(dev.freq))

            # set the quater waveplate voltage in voltage1
            wavelength = 633* ur('nanometer')
            dev.set_quarter_waveplate_voltage(1, wavelength)


        print('Done with dummy={}'.format(dummy))





