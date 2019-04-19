# -*- coding: utf-8 -*-
"""
=======================
LCC25 (thorlabs) driver
=======================
This controller supplies one class with several functions to communicate with the thorlabs
LCC25 liquid crystal controller.

Note that this controller also implements units.


"""
import serial
import yaml
import logging
from time import sleep
from hyperion import ur
from hyperion.controller.base_controller import BaseController
from hyperion.controller.dummy_resource_manager import DummyResourceManager


class Lcc(BaseController):
    """ This class is to controls the LCC25 thorlabs driver for a liquid crystal variable wavelpate.


    """

    DEFAULTS = {'write_termination': '\r',
                'read_termination': '\r',
                'encoding': 'ascii',
                'baudrate': 115200,
                'write_timeout': 2,
                'read_timeout': 2}

    OUTPUT_MODE = {'Voltage1': 1,
                   'Voltage2': 2,
                   'Modulation': 0}

    def __init__(self, port, dummy=False):
        """ INIT of the class

        :param port: name of the port where the device is connected. Ex: 'COM5'
        :type port: str
        :param dummy: to work in dummy mode
        :type dummy: logical

        """
        self.logger = logging.getLogger(__name__)
        self.name = 'lcc25'
        self.port = port
        self.dummy = dummy
        self.rsc = None
        self._is_initialized = False
        self._output = None
        self.logger.debug('Created object for the LCC. ')

    def initialize(self):
        """ Initialize the device

        """
        if self.dummy:
            self.rsc = DummyResourceManager(self.port, self.name)
            self.logger.info('Initialized device dummy LCC at port {}.'.format(self.port))
        else:
            self.rsc = serial.Serial(port=self.port,
                                     baudrate=self.DEFAULTS['baudrate'],
                                     timeout=self.DEFAULTS['read_timeout'],
                                     write_timeout=self.DEFAULTS['write_timeout'])
            self.logger.info('Initialized device LCC at port {}.'.format(self.port))
            sleep(0.5)
        self._is_initialized = True



    def idn(self):
        """ Gets the identification for  the device

        :return: answer
        :rtype: string

        """

        if self.rsc is None:
            raise Warning('Trying to write to device before initializing')

        ans = self.query('*idn?')
        sleep(0.1)
        return ans

    def write(self, message):
        """ Sends the message to the device.

        :param message: the message to write into the device buffer
        :type message: string

        """
        if self.rsc is None:
            raise Warning('Trying to write to device before initializing')

        msg = message + self.DEFAULTS['write_termination']
        msg = msg.encode(self.DEFAULTS['encoding'])
        self.rsc.write(msg)

    def read(self):
        """ Reads message from the device

        :return: answer from the device (one line)
        :type: str

        """
        if self.rsc is None:
            raise Warning('Trying to read from device before initializing')
        response = self.rsc.readline()
        self.logger.debug('Response from readline: {}'.format(response))
        msg = str(response, encoding=self.DEFAULTS['encoding'])
        self.logger.debug('Response after decode: {}'.format(msg))
        return msg.split(self.DEFAULTS['read_termination'])[1]

    def query(self, message):
        """ Writes in the buffer and Reads the response.

        :param message: command to send to the device
        :type message: str
        :return: response from the device
        :rtype: str
        """
        if self.rsc is None:
            raise Warning('Trying to query from device before initializing.')

        self.write(message)
        self.logger.debug('Sent message: {}.'.format(message))
        sleep(0.2)
        ans = self.read()
        self.logger.debug('Received message: {}.'.format(ans))
        return ans

    def finalize(self):
        """ Closes the connection to the device """
        if self.rsc is not None:
            self.rsc.close()
            self.logger.info('Resource connection closed.')

    def set_mode(self, mode):
        """ Sets the modes of operation:

        1 = 'Voltage1' : sends a 2kHz sin wave with RMS value set by voltage 1

        2 = 'Voltage2' : sends a 2kHz sin wave with RMS value set by voltage 2

        0 = 'Modulation': sends a 2kHz sin wave modulated with a square wave where voltage 1
        is one limit and voltage 2 is the second. the modulation frequency can be
        changed with the command 'freq' in the 0.5-150 Hz range.

        :param mode: type of operation.
        :type mode: int
        """
        self.query('mode={}'.format(self.OUTPUT_MODE[mode]))
        self.logger.info('Changed to mode "{}" '.format(mode))

    def set_voltage(self, V, Ch=1):
        """ Sets the voltage value for Ch where Ch = 1 or 2 for Voltage1 or Voltage2

        :param V: voltage to set in Volts
        :type V: pint quantity
        :param Ch: channel to use (default =1)
        :type Ch: int

        """
        if V.m_as('volts') > 25 or V.m_as('volts') < 0:
            raise NameError('Required Voltage outside limits (0,25)V')

        if Ch > 2:
            raise NameError('Ch can only be 1 or 2')

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

        msg = 'volt' + str(Ch) + '?'
        ans = self.query(msg)
        self.logger.debug('"voltage{}"={} Volt'.format(Ch, ans))
        voltage = float(ans) * ur('volt')
        return voltage

    def set_freq(self, F):
        """ Sets the frequency to modulate in the modulation mode.

        :param F: frequency in Hz. It can be any value between 0.5 and 150Hz.
        :type F: pint Quantity

        """
        if F.m_as('hetz') > 150 or F.m_as('hetz') < 0.5:
            raise NameError('Required Frequency outside limits (0.5,150)Hz')

        msg = 'freq=' + str(F.m_as('hetz'))
        self.query(msg)

        self.logger.debug('Changed frequency to {} Hz'.format(F.m_as('hertz')))

    def get_freq(self):
        """ Gets the frequency of (slow) modulation

        :return: The frequency value
        :rtype: pint quantity
        """
        msg = 'freq?'
        ans = self.query(msg)
        self.logger.debug('Current frequency = {} Hz'.format(ans))
        f = float(ans) * ur('hertz')
        return f

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

        self.logger.info('The output state is: {}'.format(self._output))
        return self._output

    @output.setter
    def output(self, state):
        self.logger.debug('Setting the output state to {}'.format(state))
        if state:
            self.query('enable=1')
        else:
            self.query('enable=0')

        return self._output


    def enable_output(self, state):
        """ This allows to control if the output to the Variable waveplate is
        enabled or not.
        :param state: enable or disable the output
        :type state: logical

        """

        if state:
            self.query('enable=1')
            self.logger.info('Output enabled.')
        elif state is False:
            self.query('enable=0')
            self.logger.info('Output disabled.')
        else:
            raise ErrorName('The state can be True or False')

    def output_status(self):
        """ Gives the status of the output to the variable waveplate

        :return: State: true if it is on and false if it is off
        :rtype: logical

        """
        ans = float(self.query('enable?'))

        if ans == 1:
            return True
        elif ans == 0:
            return False



class LccDummy(Lcc):
    """ This is the dummy controller for the LCC25 """
    COMMANDS = {'enable?' : [0,1], 'enable=0' : [], 'enable=1' : []

                }

    def __init__(self, port, dummy = True):
        """ init for the dummy LCC
        :param port: fake port name
        :type port: str
        :param dummy: indicates the dummy mode. keept for compatibility
        :type dummy: logical
        """
        self.logger = logging.getLogger(__name__)
        self.dummy = dummy
        self.name = 'Dummy LCC25'
        self.port = port
        self._buffer = []
        self._response = []
        self._is_initialized = False
        self.logger.debug('Implemented commands: {}'.format(self.COMMANDS))
        self.properties = {}

    def load_properties(self):
        """ This method loads a yaml file with a dictionary with the available properties for the
        LCC25 and some defaults values. This dictionary is saved in properties and will be modified
        when a variable is writen, so the dummy device will respond with the previously set value.

        """

    def write(self, msg):
        """Dummy write. It will compare the msg with the COMMANDS

        :param msg: Message to write
        :type msg: str

        """
        self.logger.debug('Writing to dummy LCC25: {}'.format(msg))
        if msg in self.COMMANDS:
            self._buffer.append(msg)
            self._response.append(self.COMMANDS[msg][-1])
        else:
            self.logger.error('The command "{}" is not listed as a valid command for LCC25'.format(msg))

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

    dummy = True

    if dummy:
        with LccDummy('COM00') as dev:
            dev.initialize()
            print(dev.output)

    else:
        with Lcc('COM8', dummy=True) as dev:
            dev.initialize()
            sleep(0.5)
            # dev.write('mode?')
            # sleep(0.5)
            # print(dev.rsc.read())

            # ask mode
            dev.query('mode?')
            # set mode
            dev.set_mode('Voltage1')
            # # ask current voltage
            dev.get_voltage(1)
            #
            # #### set a new voltage
            V = 2 * ur('volt')
            dev.set_voltage(V, Ch=1)
            #
            # ##### get the frequency of modulation (slow)
            # dev.get_freq()
            #
            # # enable or disable the output.
            #
            # # print('Output status:{}'.format(dev.output_status()))
            #
            # # dev.enable_output(False)
            # # sleep(0.1)
            # # dev.output_status()
            # # dev.enable_output(True)
            # # dev.output_status()

    print('Done')
