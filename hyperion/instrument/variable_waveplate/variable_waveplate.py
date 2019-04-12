"""
======================
LCC25 (thorlabs) model
======================

This class (variable_waveplate.py) is the model to drive the LCC25 variable waveplate controller.

It ads the use of units with pint and the wavelength calibration to obtain CPL


"""
import logging
import sys
import os
import numpy as np
from hyperion.controller.thorlabs.lcc25 import Lcc
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur, root_dir


class VariableWaveplate(BaseInstrument):
    """ This class is the model for the LCC25 analog voltage generator for the variable waveplate from thorlabs.

    """
    def __init__(self, port, enable = True, dummy = True):
        """
        Initialize
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing Variable Waveplate on port {}'.format(port))

        # this is to load the calibration file
        self.calibration = {}
        self.logger.debug('Get the source path')

        cal_file = os.path.join(root_dir, 'instrument', 'variable_waveplate',
                                'lookup_table_qwp_voltage_calibration_2019-03-15.txt')
        self.logger.info('Using Variable Waveplate QWP calibration file: {}'.format(cal_file))
        self.load_calibration(cal_file)

        # initialize
        self.dummy = dummy
        self.driver = Lcc(port, dummy = dummy)
        self.driver.initialize()
        if enable:
            self.driver.enable_output(True)
        else:
            self.driver.enable_output(False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

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
        self.logger.debug('Calibration dictionary: {}'.format(self.calibration))
        self.logger.info('Done loading calibration.')

    def idn(self):
        """
        Ask for the identification
        """
        self.logger.info('Asking for identification.')
        return self.driver.idn()

    def get_analog_value(self, channel):
        """
        Gets the analog voltage of the channel.

        :param channel: Port number. Range depends on device
        :type channel: int
        :return: voltage: voltage in use for the channel
        :rtype: pint quantity
        """
        self.logger.debug('Asking for analog value at channel {}.'.format(channel))
        value = self.driver.get_voltage(channel)    # bits has no units
        return value

    def set_analog_value(self, channel, value):
        """
        Sets the analog voltage of the channel.

        :param channel: Port number. Range depends on device
        :type channel: int
        :param value: The input value in Volts (Pint type)
        :type value: pint quantity


        """
        self.logger.debug('Setting analog value {} for channel {}.'.format(value, channel))
        self.driver.set_voltage(value, channel)
        return value

    def enable_output(self, state):
        """ Enables the output to the device

        :param state: type to set the output on and off (True and False, respectively)
        :type state: logical
         """
        self.logger.debug('Changing the output state to {}.'.format(state))
        self.driver.enable_output(state)

    def output_state(self):
        """ Gets the current state of the output

         Returns a logical value, True for on and False for off.

         """
        self.logger.debug('Getting the output state')
        ans = self.driver.output_status()
        return ans

    def set_mode(self, mode):
        """
        This method can set the mode of operation for the driver.

        The following modes are available

            * 1 = 'Voltage1' : sends a 2kHz sin wave with RMS value set by voltage 1
            * 2 = 'Voltage2' : sends a 2kHz sin wave with RMS value set by voltage 2
            * 0 = 'Modulation': sends a 2kHz sin wave modulated with a square wave where
              voltage 1 is one limit and voltage 2 is the second.
              The modulation frequency can be changed with the command 'freq' in the 0.5-150 Hz range.


        :param mode: working mode for the driver
        :type mode: int


        """
        self.logger.debug('Setting mode to {}.'.format(mode))
        self.driver.set_mode(mode)

    def finalize(self, state=False):
        """ Closes the connection to the device

        """
        self.logger.info('Finalizing connection with Variable Waveplate')
        self.driver.enable_output(state)
        self.driver.finalize()

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
            raise Warning('The required wavelength is outside the calibration range for bias voltage')

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
        self.logger.debug('x: {} \n y: {}'.format(x, y))
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
        :return: the voltage set to the driver
        :rtype:  pint quantity

        """
        self.logger.debug('Getting the quarter waveplate voltage')
        v = self.quarter_waveplate_voltage(wavelength)
        self.logger.debug('The QWP voltage for {} is {}'.format(wavelength, v))
        self.logger.debug('Setting the voltage to the QWP voltage on channel {}'.format(ch))
        self.set_analog_value(v, ch)

        return v


if __name__ == '__main__':
    from hyperion import _logger_format
    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with VariableWaveplate('COM8', dummy = True) as d:
        # test idn
        # print(d.idn())
        # test output_state
        print(d.output_state())
        # test analog value
        print(d.get_analog_value(1))
        # test enable output
        #d.enable_output(True)
        print(d.output_state())

        # d.set_analog_value(2.5*ur('volt'),1)

        # print(d.get_analog_value(1))

        wavelength = 700* ur('nanometer')
        print('The QWP voltage for {} is {}'.format(wavelength, d.quarter_waveplate_voltage(wavelength)))
        # d.set_quarter_waveplate_voltage(1, wavelength)
        # d.enable_output(False)
        # print(d.output_state())





