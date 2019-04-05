"""
=========================
Agilent 33522A controller
=========================

This is the controller class for the Agilent 33522A function generator.
Based on pyvisa to send commands to the USB.


"""
import visa
import time
import logging
from hyperion.controller.base_controller import  BaseController

class Agilent33522A(BaseController):
    """Agilent 33522A arbitrary waveform generator, 30MHz, 2 channels.

    """
    rsc = None
    DEFAULTS = {'instrument_id': '8967'
                }

    FUNCTIONS = ['SIN', 'SQU', 'TRI', 'RAMP', 'PULS', 'PRBS', 'NOIS', 'ARB', 'DC']

    def __init__(self, instrument_id, dummy = False):
        """ Init for the class

        """
        self.logger = logging.getLogger(__name__)
        self.instrument_id = instrument_id
        self.dummy = dummy
        self.logger.info('Created controller class for Agilent33522A with id: {}'.format(instrument_id))
        self.logger.info('Dummy mode: {}'.format(dummy))

    def initialize(self):
        """ This method opens the communication with the device.

        """
        self.resource_name = 'USB0::2391::' + self.instrument_id + '::MY50003703::INSTR'
        self.logger.info('Initializing device: {}'.format(self.resource_name))
        if self.dummy:
            self.logger.debug('Dummy mode: on')
            self.rsc = DummyResourceManager(self.resource_name)
        else:
            rm = visa.ResourceManager()
            self.rsc = rm.open_resource(self.resource_name)
            time.sleep(0.5)

    def finalize(self):
        """ This methods closes the visa connection

        """
        if self.rsc is not None:
            if self.dummy:
                self.logger.debug('Close dummy connection.')

            else:
                self.logger.debug('Close real connection')
                self.rsc.close()
        self.logger.info('Connection closed.')

    def idn(self):
        """Ask the device for its identification

        :return: identification of the fun gen
        :rtype: string


        """
        ans = self.rsc.query('*IDN?')
        time.sleep(0.1)
        return ans

    def get_enable_output(self, channel):
        """ Get the status of the output. 0 is off, 1 is on.

        :param channel: can be 1 or 2 for this model
        :type channel: int
        :return: Status of the output
        :rtype: string
        """
        self.check_channel(channel)
        ans = self.rsc.query('OUTPUT{}?'.format(channel))

        if not self.dummy:
            if int(ans) == 0:
                self.logger.debug('Channel {} output is OFF'.format(channel))
            elif int(ans) == 1:
                self.logger.debug('Channel {} output is ON'.format(channel))

        return ans

    def enable_output(self, channel, state):
        """ Enable the output of channel 1 or 2

        :param channel: To activate or deactivate
        :type channel: int
        :param state: logical state. True sets the output on and false off.
        :type state: logical

        """
        self.check_channel(channel)
        if state:
            self.rsc.write('OUTPUT{} ON'.format(channel))
            self.logger.debug('Channel {} set on.'.format(channel))
        else:
            self.rsc.write('OUTPUT{} OFF'.format(channel))
            self.logger.debug('Channel {} set off.'.format(channel))

    def get_function(self, channel):
        """ Get the function set for the output.
        The available functions are stored at FUNCTIONS = ['SIN','SQU','TRI','RAMP','PULS','PRBS','NOIS','ARB','DC']

        :param channel: number of channel. it can be 1 or 2 for this model
         the expected output is on of the items in FUNCTIONS
        :type channel: int
        :return: type of function in use
        :rtype: string

        """
        self.check_channel(channel)
        ans = self.rsc.query('SOUR{}:FUNC?'.format(channel))
        self.logger.debug('The function for channel {} is {}'.format(channel, ans))
        return ans

    def set_function(self, channel, fun):
        """ Get the function set for the output. The available functions are stored at
        FUNCTIONS = ['SIN','SQU','TRI','RAMP','PULS','PRBS','NOIS','ARB','DC']

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param fun:  One of the functions defined in FUNCTIONS. Ex: 'SIN"
        :type fun: string

        """
        self.check_channel(channel)
        if fun not in self.FUNCTIONS:
            raise NameError('The function specified is not supported by this model of fun gen. ')

        self.rsc.write('SOUR{}:FUNC {}'.format(channel, fun))
        self.logger.debug('Set for channel {} the function {}'.format(channel, fun))

    def check_channel(self, channel):
        """ Function to check if the channel is present in the system.

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: The number of the channel
        :rtype: string
        """
        if (channel == 1) or (channel == 2):
            return channel
        else:
            raise NameError('Channel number not supported. Only 2 channels available.')

    # ## VOLTAGE

    def set_voltage_high(self, channel, voltage):
        """ This functions sets the high voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param voltage: voltage value for the high voltage in volts (with sign)
        :type voltage: float

        """
        self.check_channel(channel)
        self.rsc.write('SOUR{}:VOLTage:HIGH {:+f}'.format(channel, voltage))

    def get_voltage_high(self, channel):
        """ This functions sets the high voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: High voltage value
        :rtype: string
        """
        self.check_channel(channel)
        return self.rsc.query('SOUR{}:VOLTage:HIGH?'.format(channel))[:-1]

    def set_voltage_low(self, channel, voltage):
        """ This functions sets the low voltage (in volts) to the channel.

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param voltage: voltage value for the low voltage in volts (with sign)
        :type voltage: float

        """
        self.check_channel(channel)
        self.rsc.write('SOUR{}:VOLTage:LOW {:+f}'.format(channel, voltage))

    def get_voltage_low(self, channel):
        """ This functions sets the low voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: Low voltage set on the device
        :rtype: string
        """
        self.check_channel(channel)
        return self.rsc.query('SOUR{}:VOLTage:LOW?'.format(channel))[:-1]

    def set_voltage(self, channel, voltage):
        """ This functions sets the Vpp voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param voltage: voltage value for the high voltage in volts (with sign)
        :type voltage: float

        """
        self.check_channel(channel)
        self.rsc.write('SOUR{}:VOLTage {:+f}'.format(channel, voltage))

    def set_voltage_offset(self, channel, voltage):
        """ This functions sets the DC offset voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param voltage: voltage value for the DC offset voltage in volts (with sign)
        :type voltage: float

        """
        self.check_channel(channel)
        self.rsc.write('SOUR{}:VOLTage:OFFset {:+f}'.format(channel, voltage))

    def get_voltage_offset(self, channel):
        """ This functions gets the DC offset voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: current offset in the device
        :rtype: string


        """
        self.check_channel(channel)
        ans = self.rsc.query('SOUR{}:VOLTage:OFFset?'.format(channel))
        self.logger.debug('The offset for channel {} is {} V.'.format(channel, ans))
        return ans[:-1]

    def get_voltage(self, channel):
        """ This functions gets the voltage in the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: current voltage Vpp  in the device
        :rtype: string
        """
        self.check_channel(channel)
        return self.rsc.query('SOUR{}:VOLTage?'.format(channel))[:-1]

    def get_system_error(self):
        """ This functions returns the error message

        :return: error message
        :rtype: string
        """
        return self.rsc.query('SYSTem:ERRor?')[:-1]

    def set_voltage_limits(self, channel, high, low):
        """ Set a limit to the output values

        For this function generator you can set a minimum and maximum voltage
        value that will not be exceeded to protect the device that is being feed.

        NOTE: setting the values does not activate this feature. To enable/disable it use the function
        enable_voltage_limits(channel,state)

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param high: High maximum voltage value for the output in Volts
        :type high: float
        :param low: High maximum voltage value for the output in VOlts
        :type low: float


        """
        self.check_channel(channel)
        self.rsc.write('SOUR{}:VOLT:LIM:HIGH {}'.format(channel, high))
        self.logger.info('Set the voltage limit HIGH to {} V.'.format(high))
        self.rsc.write('SOUR{}:VOLT:LIM:LOW {}'.format(channel, low))
        self.logger.info('Set the voltage limit LOW to {} V.'.format(low))

    def get_voltage_limits(self, channel):
        """ Gets the set values for the voltage limits, high and low.

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: array with [high_value, low_value] in volts
        :rtype: array of strings

        """

        self.check_channel(channel)
        ans = []
        ans.append(self.rsc.query('SOUR{}:VOLT:LIM:HIGH?'.format(channel))[:-1])
        ans.append(self.rsc.query('SOUR{}:VOLT:LIM:LOW?'.format(channel))[:-1])
        return ans

    def enable_voltage_limits(self, channel, state):
        """ This function enables the limits for the maximum and minimum voltage
         output that can be generated by each channel. Those values are set with
         the method set_voltage_limits(channel, high, low).

         This function enables this setting by putting state = true and disables
         it by putting state = false. When enable, setting a voltage outside the permitted
         values will give an error (not in python, in the device)

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param state: True to turn on, False to turn off
        :type state: logical

        """

        self.check_channel(channel)
        if state:
            self.rsc.write('SOUR{}:VOLT:LIM:STATe 1'.format(channel))
            self.logger.info('Turned on the voltage limit setting for channel {}.'.format(channel))
        else:
            self.rsc.write('SOUR{}:VOLT:LIM:STATe 0'.format(channel))
            self.logger.info('Turned off the voltage limit setting for channel {}.'.format(channel))

    def get_voltage_limits_state(self, channel):
        """ Checks the status of the voltage limits. It can be on or off

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: voltage limit state (logical)
        :rtype: string


        """

        self.check_channel(channel)
        return self.rsc.query('SOUR{}:VOLT:LIM:STATe?'.format(channel))[:-1]

    def get_state_voltage_limits(self, channel):
        """ This function generator can set a minimum and maximum voltage value that will not be exceeded
        to protect the device that is being feed.

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: voltage limits
        :rtype: string

        """
        self.check_channel(channel)
        ans = self.rsc.query('SOUR{}:VOLT:LIM:STATe?'.format(channel))
        # print('The "LIMITS" settings for channel {} is = {}'.format(channel,ans))
        return ans[:-1]

    def set_frequency(self, channel, freq):
        """ This functions sets the frequency output for the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param freq: desired frequency in Hz
        :type freq: float

        """
        self.check_channel(channel)
        self.rsc.write('SOUR{}:FREQ {:+f}'.format(channel, freq))

    def get_frequency(self, channel):
        """ This functions reads the frequency output for the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: Frequency value currently in the device in Hz
        :rtype: string

        """
        self.check_channel(channel)
        ans = self.rsc.query('SOUR{}:FREQ?'.format(channel))
        self.logger.info('Frequency for channel {} is {} Hz. '.format(channel, ans[:-1]))
        return ans[:-1]

class DummyResourceManager():
    """ This is a dummy class to emulate the visa resource manager"""

    def __init__(self, resource):
        """ Init"""
        self.name = resource
        self.logger = logging.getLogger(__name__)

    def write(self, msg):
        self.logger.info('Writing to {} message: {}'.format(self.name, msg))

    def read(self):
        self.logger.info('Reading from: {}'.format(self.name))
        ans = 'dummy response!'
        return ans

    def query(self, msg):
        self.write(msg)
        ans = self.read()
        return ans


if __name__ == "__main__":
    from hyperion import _logger_format

    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])


    with Agilent33522A('8967', dummy = True) as gen:

        # initialize
        gen.initialize()
        # test idn
        print('Identification: {}'.format(gen.idn()))
        print(gen.get_system_error())

        # list of tests of the avove functions

        ## to test output enable for channel ch
        ch = 1
        gen.get_enable_output(ch)
        time.sleep(0.1)
        gen.enable_output(ch, False)
        time.sleep(0.1)
        gen.get_enable_output(ch)

        # to test FUNCTION waveform
        ch = 1
        gen.get_function(ch)
        gen.set_function(ch,'SQU')
        gen.get_function(ch)

        ## check error
        time.sleep(0.1)
        print(gen.rsc.query('SYST:ERR?'))

        # check voltage high
        ch = 2
        print(gen.get_voltage_high(ch))
        gen.set_voltage_high(ch,+1.54)
        print(gen.get_voltage_high(ch))

        # check voltage low
        ch = 1
        print('The low voltage for channel {} is = {}'.format(ch,gen.get_voltage_low(ch)))
        gen.set_voltage_low(ch,0)
        print('The low voltage for channel {}  is = {}'.format(ch,gen.get_voltage_low(ch)))

        # check voltage (vpp) and offset
        ch = 1
        # read
        print('The voltage for channel {} is = {} V.'.format(ch,gen.get_voltage(ch)))
        print('The ofset for channel {}  is = {} V. '.format(ch, gen.get_voltage_offset(ch)))
        # set and then read
        gen.set_voltage(ch,4)
        print('The voltage for channel {}  is = {} V.'.format(ch, gen.get_voltage(ch)))
        gen.set_voltage_offset(ch,1)
        print('The voltage offset for channel {}  is = {} V.'.format(ch, gen.get_voltage_offset(ch)))

        ## check voltage limit
        ch=1
        print(gen.get_state_voltage_limits(ch))
        time.sleep(0.1)
        gen.set_voltage_limits(ch,+5,-5)
        time.sleep(0.1)
        gen.enable_voltage_limits(ch,True)

        gen.set_voltage_high(ch,4.5) # it gives an error if I ask more than the limit.

        # check output enable
        ch = 1
        gen.get_enable_output(ch)
        gen.enable_output(ch,True)
        gen.get_enable_output(ch)

        # check the frequency settings
        ch =1
        gen.get_frequency(ch)
        gen.set_frequency(ch,989.65)
        gen.get_frequency(ch)