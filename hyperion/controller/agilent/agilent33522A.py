# -*- coding: utf-8 -*-
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
from hyperion.controller.base_controller import BaseController


class Agilent33522A(BaseController):
    """Agilent 33522A arbitrary waveform generator, 30MHz, 2 channels.

    """
    DEFAULTS = {'instrument_id': '8967'
                }

    CHANNELS = [1,2]
    FUNCTIONS = ['SIN', 'SQU', 'TRI', 'RAMP', 'PULS', 'PRBS', 'NOIS', 'ARB', 'DC']

    def __init__(self, settings = {'instrument_id':'8967', 'dummy': True}):
        """ Init for the class. It takes a dictionary that passes the settings needed. In this case
        it needs

        instrument_id : '8967' # instrument id for the device you have
        dummy : False


        """
        super().__init__()
        self.rsc = None
        self.instrument_id = settings['instrument_id']
        self.dummy = settings['dummy']
        self.logger.info('Created controller class for Agilent33522A with id: {}'.format(self.instrument_id))
        self.logger.info('Dummy mode: {}'.format(self.dummy))

    def initialize(self):
        """ This method opens the communication with the device.

        """
        self.resource_name = 'USB0::2391::' + str(self.instrument_id) + '::MY50003703::INSTR'
        self.logger.info('Initializing device: {}'.format(self.resource_name))
        if self.dummy:
            self.logger.info('Dummy device initialized')
        else:
            rm = visa.ResourceManager()
            self.rsc = rm.open_resource(self.resource_name)
            time.sleep(0.5)

        self._is_initialized = True

    def finalize(self):
        """ This methods closes the visa connection

        """
        if self._is_initialized:
            if self.rsc is not None:
                if self.dummy:
                    self.logger.debug('Close dummy connection.')

                else:
                    self.logger.debug('Close real connection')
                    self.rsc.close()
            self.logger.info('Connection closed.')

    def write(self, msg):
        """ Write in the device buffer
        :param msg: message to write to the device
        :type msg: string
        """
        self.logger.debug('Writing to device: {}'.format(msg))
        self.rsc.write(msg)

    def read(self):
        """ Read buffer

        """
        self.logger.debug('Reading from device')
        ans = self.rsc.read()
        self.logger.debug('Response: {}'.format(ans))
        return ans

    def query(self, msg):
        """ Sequential read and write
        :param msg: message to write to the device
        :type msg: string
        """
        self.logger.debug('Query: {}'.format(msg))
        ans = self.rsc.query(msg)
        self.logger.debug('Answer from device: {}'.format(ans))
        return ans

    def idn(self):
        """Ask the device for its identification

        :return: identification of the fun gen
        :rtype: string


        """
        ans = self.query('*IDN?')
        time.sleep(0.1)
        return ans

    def get_enable_output(self, channel):
        """ Get the status of the output. 0 is off, 1 is on.

        :param channel: can be 1 or 2 for this model
        :type channel: int
        :return: Status of the output
        :rtype: logical
        """
        self.check_channel(channel)
        ans = self.query('OUTPUT{}?'.format(channel))

        if not self.dummy:
            if int(ans) == 0:
                self.logger.debug('Channel {} output is OFF'.format(channel))
                ans = False
            elif int(ans) == 1:
                self.logger.debug('Channel {} output is ON'.format(channel))
                ans = True

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
            self.write('OUTPUT{} ON'.format(channel))
            self.logger.debug('Channel {} set on.'.format(channel))
        else:
            self.write('OUTPUT{} OFF'.format(channel))
            self.logger.debug('Channel {} set off.'.format(channel))

    def get_waveform(self, channel):
        """ Get the function set for the output.
        The available functions are stored at FUNCTIONS = ['SIN','SQU','TRI','RAMP','PULS','PRBS','NOIS','ARB','DC']

        :param channel: number of channel. it can be 1 or 2 for this model
         the expected output is on of the items in FUNCTIONS
        :type channel: int
        :return: type of function in use
        :rtype: string

        """
        self.check_channel(channel)
        ans = self.query('SOUR{}:FUNC?'.format(channel))
        self.logger.debug('The function for channel {} is {}'.format(channel, ans))
        return ans

    def set_waveform(self, channel, fun):
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

        self.write('SOUR{}:FUNC {}'.format(channel, fun))
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
        self.write('SOUR{}:VOLTage:HIGH {:+f}'.format(channel, voltage))

    def get_voltage_high(self, channel):
        """ This functions sets the high voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: High voltage value
        :rtype: string
        """
        self.check_channel(channel)
        return self.query('SOUR{}:VOLTage:HIGH?'.format(channel))[:-1]

    def set_voltage_low(self, channel, voltage):
        """ This functions sets the low voltage (in volts) to the channel.

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param voltage: voltage value for the low voltage in volts (with sign)
        :type voltage: float

        """
        self.check_channel(channel)
        self.write('SOUR{}:VOLTage:LOW {:+f}'.format(channel, voltage))

    def get_voltage_low(self, channel):
        """ This functions sets the low voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: Low voltage set on the device
        :rtype: string
        """
        self.check_channel(channel)
        return self.query('SOUR{}:VOLTage:LOW?'.format(channel))[:-1]

    def set_voltage(self, channel, voltage):
        """ This functions sets the Vpp voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param voltage: voltage value for the high voltage in volts (with sign)
        :type voltage: float

        """
        self.check_channel(channel)
        self.write('SOUR{}:VOLTage {:+f}'.format(channel, voltage))

    def set_voltage_offset(self, channel, voltage):
        """ This functions sets the DC offset voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :param voltage: voltage value for the DC offset voltage in volts (with sign)
        :type voltage: float

        """
        self.check_channel(channel)
        self.write('SOUR{}:VOLTage:OFFset {:+f}'.format(channel, voltage))

    def get_voltage_offset(self, channel):
        """ This functions gets the DC offset voltage to the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: current offset in the device
        :rtype: string


        """
        self.check_channel(channel)
        ans = self.query('SOUR{}:VOLTage:OFFset?'.format(channel))
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
        return self.query('SOUR{}:VOLTage?'.format(channel))[:-1]

    def get_system_error(self):
        """ This functions returns the error message

        :return: error message
        :rtype: string
        """
        return self.query('SYSTem:ERRor?')[:-1]

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
        self.write('SOUR{}:VOLT:LIM:HIGH {}'.format(channel, high))
        self.logger.info('Set the voltage limit HIGH to {} V.'.format(high))
        self.write('SOUR{}:VOLT:LIM:LOW {}'.format(channel, low))
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
        ans.append(float(self.query('SOUR{}:VOLT:LIM:HIGH?'.format(channel))[:-1]))
        ans.append(float(self.query('SOUR{}:VOLT:LIM:LOW?'.format(channel))[:-1]))
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
            self.write('SOUR{}:VOLT:LIM:STATe 1'.format(channel))
            self.logger.info('Turned on the voltage limit setting for channel {}.'.format(channel))
        else:
            self.write('SOUR{}:VOLT:LIM:STATe 0'.format(channel))
            self.logger.info('Turned off the voltage limit setting for channel {}.'.format(channel))

    def get_voltage_limits_state(self, channel):
        """ Checks the status of the voltage limits. It can be on or off

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: voltage limit state (logical)
        :rtype: string


        """

        self.check_channel(channel)
        return self.query('SOUR{}:VOLT:LIM:STATe?'.format(channel))[:-1]

    def get_state_voltage_limits(self, channel):
        """ This function generator can set a minimum and maximum voltage value that will not be exceeded
        to protect the device that is being feed.

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: voltage limits
        :rtype: string

        """
        self.check_channel(channel)
        ans = self.query('SOUR{}:VOLT:LIM:STATe?'.format(channel))
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
        self.write('SOUR{}:FREQ {:+f}'.format(channel, freq))

    def get_frequency(self, channel):
        """ This functions reads the frequency output for the channel

        :param channel: number of channel. it can be 1 or 2 for this model
        :type channel: int
        :return: Frequency value currently in the device in Hz
        :rtype: string

        """
        self.check_channel(channel)
        ans = self.query('SOUR{}:FREQ?'.format(channel))
        self.logger.info('Frequency for channel {} is {} Hz. '.format(channel, ans[:-1]))
        return ans[:-1]



class Agilent33522ADummy(Agilent33522A):
    """
    ===================
    Agilent33522A Dummy
    ===================

    This is the dummy controller for the Agilent33522A.

    The idea is to load this class instead of the real one
    to do testing of higher level functions without the need of the real device to be connected or working.

    The logic is that this dummy device will respond as the real device would, with the correct type
    and size of information is expected.

    This class inherits from the real device and the idea is to re-write only the init, the write
    and the read, so all the other functions remain the same and functioning.

    The specific way to achieve this will be different for every device, so it has to be done separately.

    To do so, we use a yaml file that tells the dummy class what are the properties of the device. For example,
    one property for the LCC25 is voltage1, which is the voltage for channel 1. Then from this you can build 2
    commands: voltage1? to ask what is the value and voltage1=1 to set it to the value 1. So we build a command
    list using the CHAR ? and = for each of this properties.

    """
    ask = '?'
    write = ' '

    def __init__(self, settings):
        """ init for the dummy Agilent33522A
        :param port: fake port name
        :type port: str
        :param dummy: indicates the dummy mode. keept for compatibility
        :type dummy: logical
        """
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.name = 'Dummy Agilent33522A'
        self._buffer = []
        self._response = []
        self._properties = {}
        self._all = {}
        self._commands = []
        self.load_properties()

    def load_properties(self):
        """ This method loads a yaml file with a dictionary with the available properties for the
        LCC25 and some defaults values. This dictionary is saved in properties and will be modified
        when a variable is writen, so the dummy device will respond with the previously set value.

        """
        filename = os.path.join(root_dir,'controller', 'dummy', 'agilent33522A.yml')
        self.logger.debug('Loading Agilent33522A defaults file: {}'.format(filename))

        with open(filename, 'r') as f:
            d = yaml.load(f, Loader=yaml.FullLoader)

        self._properties = d
        self.logger.debug('_properties dict: {}'.format(self._properties))

        for key in d:
            self.logger.debug('Adding key: {}'.format(key))
            self._all[key] = d[key]['default']
            for command_key in self.CHAR:
                new_command = key + self.CHAR[command_key]
                self.logger.debug('Adding to the command list: {}'.format(new_command))
                self._commands. append(new_command)

        self.logger.debug('_all dict: {}'.format(self._all))
        self._properties['dummy_yaml_file'] = filename  # add to the class the name of the Config file used.
        self.logger.debug('Commands list: {}'.format(self._commands))


    def write(self, msg):
        """Dummy write. It will compare the msg with the COMMANDS

        :param msg: Message to write
        :type msg: str

        """
        self.logger.debug('Writing to dummy LCC25: {}'.format(msg))

        # next is to check that the command exists in the device and to give the proper response
        if '=' in msg:
            prop = msg.split('=')[0]
            value = msg.split('=')[1]
            command = prop + '='
        elif msg[-1] == '?':
            prop = msg[:-1]
            value = None
            command = msg

        self.logger.debug('prop: {}, value: {}'.format(prop, value))
        if command in self._commands:
            if value is None:
                self.logger.debug('Reading the property: {}'.format(prop))
                response = self._all[prop]
            else:
                response = 'Setting property: {} to {}'.format(prop, value)
                self.logger.debug(response)
                self._buffer.append(msg)
                self._all[prop] = value
        else:
            self.logger.error('The command "{}" is not listed as a valid command for LCC25'.format(msg))

        self.logger.debug('The response is: {}'.format(response))
        self._response.append(response)


    def read(self):
        """ Dummy read. Reads the response buffer"""
        self.logger.debug('Reading from the dummy device')
        return self._response[-1]



if __name__ == "__main__":
    from hyperion import _logger_format

    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with Agilent33522A(settings = {'instrument_id':'8967', 'dummy': False}) as gen:
        # initialize
        gen.initialize()
        # unit_test idn
        print('Identification: {}'.format(gen.idn()))
        print(gen.get_system_error())

        # list of tests of the above functions

        ## to unit_test output enable for channel ch
        ch = 1
        gen.get_enable_output(ch)
        time.sleep(0.1)
        gen.enable_output(ch, False)
        time.sleep(0.1)
        gen.get_enable_output(ch)

        # to unit_test FUNCTION waveform
        ch = 1
        gen.get_waveform(ch)
        gen.set_waveform(ch, 'SQU')
        gen.get_waveform(ch)

        ## check error
        time.sleep(0.1)
        print(gen.query('SYST:ERR?'))

        # check voltage high
        ch = 2
        print(gen.get_voltage_high(ch))
        gen.set_voltage_high(ch, +1.54)
        print(gen.get_voltage_high(ch))

        # check voltage low
        ch = 1
        print('The low voltage for channel {} is = {}'.format(ch, gen.get_voltage_low(ch)))
        gen.set_voltage_low(ch, 0)
        print('The low voltage for channel {}  is = {}'.format(ch, gen.get_voltage_low(ch)))

        # check voltage (vpp) and offset
        ch = 1
        # read
        print('The voltage for channel {} is = {} V.'.format(ch, gen.get_voltage(ch)))
        print('The ofset for channel {}  is = {} V. '.format(ch, gen.get_voltage_offset(ch)))
        # set and then read
        gen.set_voltage(ch, 4)
        print('The voltage for channel {}  is = {} V.'.format(ch, gen.get_voltage(ch)))
        gen.set_voltage_offset(ch, 1)
        print('The voltage offset for channel {}  is = {} V.'.format(ch, gen.get_voltage_offset(ch)))

        ## check voltage limit
        ch = 1
        print(gen.get_state_voltage_limits(ch))
        time.sleep(0.1)
        gen.set_voltage_limits(ch, +5, -5)
        time.sleep(0.1)
        gen.enable_voltage_limits(ch, True)

        gen.set_voltage_high(ch, 4.5)  # it gives an error if I ask more than the limit.

        # check output enable
        ch = 1
        gen.get_enable_output(ch)
        gen.enable_output(ch, True)
        gen.get_enable_output(ch)

        # check the frequency settings
        ch = 1
        gen.get_frequency(ch)
        gen.set_frequency(ch, 989.65)
        gen.get_frequency(ch)
    print('Done')
