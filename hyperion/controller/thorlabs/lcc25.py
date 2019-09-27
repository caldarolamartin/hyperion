# -*- coding: utf-8 -*-
"""
=======================
LCC25 (thorlabs) driver
=======================
This controller supplies one class with several functions to communicate with the thorlabs
LCC25 liquid crystal controller.

Note that this controller also implements units.


"""
import os
import serial
import yaml
import logging
from time import sleep, time
from hyperion import ur, root_dir
from hyperion.controller.base_controller import BaseController


class Lcc(BaseController):
    """ This class is to controls the LCC25 thorlabs driver for a liquid crystal variable waveplate.


    """

    DEFAULTS = {'write_termination': '\r',
                'read_termination': '\r',
                'encoding': 'ascii',
                'baudrate': 115200,
                'write_timeout': 2,
                'read_timeout': 3}

    OUTPUT_MODE = {'Voltage1': 1,
                   'Voltage2': 2,
                   'Modulation': 0}

    def __init__(self, settings):
        """ INIT of the class

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict

        """
        super().__init__()  # runs the init of the base_controller class.
        self.logger = logging.getLogger(__name__)
        self.name = 'lcc25'
        self._port = settings['port']
        self.dummy = settings['dummy']
        self.rsc = None
        self.logger.debug('Created object for the LCC. ')

        # these are variables for the @property methods
        self._freq = 0
        self._mode = 0
        self._output = False

    def initialize(self):
        """ Initialize the device

        """
        if self.dummy:
            self.logger.info('Dummy device initialized')
        else:
            self.rsc = serial.Serial()
            self.rsc.port = self._port
            self.rsc.baudrate = self.DEFAULTS['baudrate']
            self.rsc.timeout = self.DEFAULTS['read_timeout']
            self.rsc.write_timeout = self.DEFAULTS['write_timeout']
            self.logger.info('Initialized device LCC at port {}.'.format(self._port))


        # try to initi

        self._is_initialized
        count = 0
        while not self._is_initialized:
            try:
                self.rsc.open()
                self._is_initialized = True

            except:
                #self.logger.debug('Initialization Failed')
                count  += 1

            sleep(0.05)
        self.logger.debug('Initialization succeded after {} failed attempts'.format(count))

    def idn(self):
        """ Gets the identification for  the device

        :return: answer
        :rtype: string

        """

        if self.rsc is None:
            raise Warning('Trying to write to device before initializing')

        ans = self.query('*idn?')
        return ans

    def write(self, message):
        """ Sends the message to the device.

        :param message: the message to write into the device buffer
        :type message: string

        """
        if not self._is_initialized:
            raise Warning('Trying to write to device before initializing')

        msg = message + self.DEFAULTS['write_termination']
        msg = msg.encode(self.DEFAULTS['encoding'])
        self.rsc.write(msg)

    def read_serial_buffer_in(self):
        """
        Reads everything the device has sent. By default it waits until a line
        is terminated by a termination character (\n or \r), but that check can
        be disabled using the input parameter.

        :param untill_at_least_one_termination_char: defaults to True
        :type untill_at_least_one_termination_char: bool
        :return: complete serial buffer from the device
        :rtype: bytes

        """
        if not self._is_initialized:
            raise Warning('Trying to read from {} before initializing'.format(self.name))

        raw = b''
        # Keep checking
        to = time()
        expire_time = time() + self.DEFAULTS['read_timeout'] + 0.00001 # in case _read_timeout is null

        while (time() < expire_time):
            raw += self.rsc.read(1)
            if raw[-2:] == '> '.encode(self.DEFAULTS['encoding']):
                break
        self.logger.debug('Elapsed time: {} s'.format(time()-to))
        self.logger.debug('{} bytes received'.format(len(raw)))
        return raw

    def read(self):
        """ Reads message from the device

        :return: answer from the device (one line)
        :type: str

        """
        if not self._is_initialized:
            raise Warning('Trying to read from device before initializing')
        #response = self.rsc.readline()
        response = self.read_serial_buffer_in()
        self.logger.debug('Response: {}'.format(response))
        msg = str(response, encoding=self.DEFAULTS['encoding'])
        #self.logger.debug('Response after decode: {}'.format(msg))
        list = msg.split(self.DEFAULTS['read_termination'])
        self.logger.debug('Split: {}'.format(list))
        return list[-2]

    def query(self, message):
        """ Writes in the buffer and Reads the response.

        :param message: command to send to the device
        :type message: str
        :return: response from the device
        :rtype: str
        """
        if not self._is_initialized:
            raise Warning('Trying to query from device before initializing.')

        self.rsc.reset_input_buffer()
        buf_size = self.rsc.in_waiting
        self.logger.debug('The buffer size before query is: {}'.format(buf_size))
        self.write(message)
        self.logger.debug('Sent message: {}.'.format(message))
        self.logger.debug('The buffer size after writing, before reading is: {}'.format(self.rsc.in_waiting))
        ans = self.read()
        self.logger.debug('Received message: {}.'.format(ans))

        return ans

    def finalize(self):
        """ Closes the connection to the device """
        if self._is_initialized:
            if self.rsc is not None:
                self.logger.debug('Is open? = {}'.format(self.rsc.is_open))
                self.rsc.close()
                self.logger.info('Resource connection closed.')
                self.logger.debug('Is open? = {}'.format(self.rsc.is_open))
        else:
            self.logger.warning('Finalizing before initializing the LCC25')

    def set_voltage(self, Ch, V):
        """ Sets the voltage value for Ch where Ch = 1 or 2 for Voltage1 or Voltage2

        :param Ch: channel to use (default =1)
        :type Ch: int
        :param V: voltage to set in Volts
        :type V: pint quantity
        """
        if V.m_as('volts') > 25 or V.m_as('volts') < 0:
            raise NameError('Required Voltage outside limits (0,25)V')

        if Ch > 2:
            raise NameError('Ch can only be 1 or 2')

        V = round(V,3) # round to the max precision of the device
        msg = 'volt' + str(Ch) + '=' + str(V.m_as('volt'))
        self.query(msg)
        self.logger.info('Changed "voltage{}" to {} volt'.format(Ch, V.m_as('volt')))

    def get_voltage(self, Ch=1):
        """ Gets the voltage value for VoltageCh where Ch = 1 or 2 for Voltage1 or Voltage2

        :param Ch: The channel to use, can be 1 or 2
        :type Ch: int

        :return: The method returns the voltage value present in the device in volts.
        :rtype: pint quantity
        """
        if Ch > 2:
            raise NameError('Ch can only be 1 or 2')

        self.logger.debug('getting for channel {}'.format(Ch))
        msg = 'volt' + str(Ch) + '?'
        ans = self.query(msg)
        self.logger.debug('"voltage{}"={} Volt'.format(Ch, ans))
        voltage = float(ans) * ur('volt')
        return voltage

    @property
    def freq(self):
        """ Modulation frequency when the operation mode is 'modulation' (mode = 0)

        : getter : Asks for the current frequency

        :return: The frequency value
        :rtype: pint quantity

        : setter :

        :param F: frequency in Hz. It can be any value between 0.5 and 150Hz.
        :type F: pint Quantity

        """
        self.logger.debug('Ask for the current frequency.')
        ans = self.query('freq?')
        self._freq = float(ans) * ur('hertz')
        return self._freq

    @freq.setter
    def freq(self, F):
        if F.m_as('hertz') > 150 or F.m_as('hertz') < 0.5:
            raise NameError('Required Frequency outside limits (0.5, 150) Hz')
        if self._freq != F:
            self._freq = F
            msg = 'freq=' + str(F.m_as('hertz'))
            self.query(msg)
            self.logger.debug('Changed frequency to {} '.format(F))
        else:
            self.logger.debug('Tried to set freq, but it was already set to that value.')


    def get_commands(self):
        """ Gives a list of all the commands available
        :return: list with the commands available
        :rtype: str
        """
        return self.query('?')

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
        ans = float(self.query('enable?'))
        if ans == 1:
            self._output = True
        elif ans == 0:
            self._output = False

        self.logger.debug('The output state is: {}'.format(self._output))
        return self._output

    @output.setter
    def output(self, state):
        self.logger.debug('Setting the output state to {}'.format(state))
        if state:
            self.query('enable=1')
        else:
            self.query('enable=0')

        return self._output

    @property
    def mode(self):
        """| Operation mode
        | The possible modes are:
        | 1 = 'Voltage1' : sends a 2kHz sin wave with RMS value set by voltage 1
        | 2 = 'Voltage2' : sends a 2kHz sin wave with RMS value set by voltage 2
        | 0 = 'Modulation': sends a 2kHz sin wave modulated with a square wave where voltage 1 is one limit and voltage 2 is the second.
        | The modulation frequency can be changed with the command 'freq' in the 0.5-150 Hz range.

        : getter : Gets the current mode
        : setter : Sets the mode

        :param mode: type of operation.
        :type mode: int
        """
        self.logger.debug('Getting the mode of operation')
        self._mode = int(self.query('mode?'))
        return self._mode

    @mode.setter
    def mode(self, mode):
        self.query('mode={}'.format(mode))
        self.logger.info('Changed to mode "{}" '.format(mode))
        self._mode = mode


class LccDummy(Lcc):
    """
    =========
    LCC Dummy
    =========

    This is the dummy controller for the LCC25. The idea is to load this class instead of the real one
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

    CHAR = {'ask' : '?', 'set' : '='}

    def __init__(self, settings = {'port':'COM00', 'dummy':True}):
        """ init for the dummy LCC

        :param port: fake port name
        :type port: str

        :param dummy: indicates the dummy mode. keept for compatibility
        :type dummy: logical
        """
        super().__init__(settings=settings)
        self.logger = logging.getLogger(__name__)
        self.name = 'Dummy LCC25'
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
        filename = os.path.join(root_dir,'controller', 'dummy', 'lcc25.yml')
        self.logger.debug('Loading LCC defaults file: {}'.format(filename))

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
    from hyperion import _logger_format, _logger_settings

    import serial.tools.list_ports

    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])



    comports = serial.tools.list_ports.comports()
    for port, desc, hwid in comports:
        print((port, desc, hwid))

    # part_of_name = 'rduino'
    # usb_dev = next(serial.tools.list_ports.grep(part_of_name))
    # print(usb_dev.description)
    # print(usb_dev.hwid)
    # print(usb_dev.device)



    dummy = False  # change this to false to work with the real device in the COM specified below.

    if dummy:
        my_class = LccDummy
    else:
        my_class = Lcc

    with my_class(settings={'port':'COM8', 'dummy':dummy}) as dev:
        dev.initialize()
        print(dev.get_voltage(1))
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

        # set voltage for both channels
        for ch in range(1,2):
            logging.info('Current voltage for channel {} is {}'.format(ch,dev.get_voltage(ch)))
            dev.set_voltage(ch, 1*ur('volts'))
            #print( dev.read_serial_buffer_in() )
            logging.info('Current voltage for channel {} is {}'.format(ch,dev.get_voltage(ch)))

        # unit_test freq
        # logging.info('Current freq: {}'.format(dev.freq))
        # Freqs = [1, 10, 20, 60, 100]*ur('Hz')
        # for f in Freqs:
        #     dev.freq = f
        #     logging.info('Current freq: {}'.format(dev.freq))



    print('Done')
