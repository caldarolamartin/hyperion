# -*- coding: utf-8 -*-
"""
    ===============
    AOTF controller
    ===============

    This controller (aa_modd18012.py) supplies one class with several methods to communicate
    with the AOTF driver from AA optoelectronics model: 1MODD18012_0074


"""
import serial
from time import sleep
import logging
from hyperion.controller.base_controller import BaseController
from hyperion.controller.dummy_resource_manager import DummyResourceManager


class AaModd18012(BaseController):
    """
    controller class for the driver aa_mod18012 from AA optoelelectronics.
    This class has all the methods to communicate using serial.

    NOTE: Our model has different ranges of frequency (see data sheet)
            Line 1 to 6: 82-151 MHz (this drives short wavelengths)
            Line 7 to 8: 68-82 MHz  (this drives long wavelengths)
    """

    # here some parameters I need
    DEFAULTS = {'write_termination': '\r',
                'read_termination': '\n',
                'encoding': 'ascii',
                'baudrate': 57600,
                'parity': 'None',
                'write_timeout': 1,
                'read_timeout': 1,
                'frequency': [85, 95, 105, 115, 125, 145, 70, 80]}

    MODES = {'internal': 0, 'external': 1}  # for individual commands

    BLANKING = 0  # channel for blanking

    # limits
    CHANNEL_s = range(1, 7)
    LIM_s = (82, 151)  # in MHz
    LIM_l = (68, 82)  # in MHz
    CHANNEL_l = range(7, 9)
    PW_lim = (0, 22)  # in dBm

    # for dummy
    DUMMY = {'write_response': 'Write dummy response to command: ',
             'read_response': 'Read dummy response.',
             }

    def __init__(self, settings):
        """ INIT of the class

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict
        """
        super().__init__()  # runs the init of the base_controller class.
        self.logger = logging.getLogger(__name__)
        self.name = 'AaModd18012'
        self._port = settings['port']
        self.dummy = settings['dummy']
        self.rsc = None
        self.logger.info('Class Aa_modd18012 init. Created object.')


    def initialize(self):
        """ Initialize the device.

        It actually connects to the device using the default settings.


        """
        if self.dummy:
            self.logger.info('Dummy device initialized')
        else:
            self.rsc = serial.Serial(port=self.port,
                                     baudrate=self.DEFAULTS['baudrate'],
                                     timeout=self.DEFAULTS['read_timeout'],
                                     write_timeout=self.DEFAULTS['write_timeout']
                                     )

            self.logger.info('Initialized device AOTF at port {}.'.format(self.port))

    def finalize(self):
        """ Closes the connection to the device

         """
        if self.rsc is not None:
            self.rsc.close()
            self.logger.info('The connection to aa_modd18012 is closed.')

        self.logger.info('Finalized the class')

    def write(self, message):
        """ Sends the message to the device.

        :param message: message to send to the device.
        :type message: string
        :return: the response from the device.
        :rtype: string

        """
        if self.rsc is None:
            raise Warning('Trying to write to device before initializing')

        msg = message + self.DEFAULTS['write_termination']
        msg = msg.encode(self.DEFAULTS['encoding'])
        self.logger.debug('Writing to the device: {} '.format(msg))
        ans = self.rsc.write(msg)

        self.logger.debug('Ans: {}'.format(ans))
        return ans

    def read(self):
        """ Reads message from the device. It reads until the buffer is clean.

        :return: The messages in the buffer of the device. It removes the end of line characters.
        :rtype: string

        """
        if self.rsc is None:
            raise Warning('Trying to read from device before initializing')

        self.logger.info('Reading from device')

        if self.dummy:
            self.logger.debug('reading from dummy device')
            response = self.rsc.read()
        else:
            reading = True
            msgs = []
            while reading:
                msg = str(self.rsc.readline(), encoding=self.DEFAULTS['encoding'])
                if msg == '':
                    reading = False
                # self.logger.debug('Received message: {}'.format(msg))
                msg = msg.replace("\n", "")  # remove the end of line
                # self.logger.debug('Removed \\n: {}'.format(msg))
                msg = msg.replace("\r", "")  # remove the end of line
                # self.logger.debug('Removed \\r: {}'.format(msg))
                msgs.append(msg)
                self.logger.debug('Received message: {}'.format(msg))
                response = [x for x in msgs if x != '']
        return response

    def query(self, message):
        """ Writes and Reads the answer from the device.
            Basically this method is a write followed by a read with a 10ms wait in the middle.

            :param message: Message to be passed to the serial port.
            :type message: string
            :return: The reply from the device.
            :rtype: string

            """
        if self.rsc is None:
            raise Warning('Trying to query from device before initializing.')

        ans = self.write(message)
        self.logger.debug('Sent message: {}.'.format(message))
        self.logger.debug('Received message: {}'.format(ans))
        sleep(0.01)
        ans = self.read()
        self.logger.debug('Received message: {}.'.format(ans))
        return ans

    def set_frequency(self, channel, freq):
        """This function sets RF frequency for a given channel.
        The device has 8 channels.
        Channels 1-6 work in the range 82-151 MHz
        Channels 7-8 work in the range 68-82 MHz

        :param channel: channel to set the frequency.
        :type channel: int
        :param freq: Frequency to set in MHz (it has accepted ranges that depends on the channel)
        :type freq: float

        """
        self.check_channel(channel)
        channel, value = self.check_freq(channel, freq)
        self.query("L{}F{}".format(channel, value))

    def set_powerdb(self, channel, value):
        """Power for a given channel (in dBm).
        Range: (0,22) dBm

        :param channel: channel to use
        :type channel: int
        :param value: power value in dBm
        :type value: float

        """
        self.check_power(value)
        self.query("L{}D{}".format(channel, value))

    def check_channel(self, channel):
        """ Method to check the key of the channel is correct

        :param channel: channel to use
        :type channel: int
        :return: channel
        :rtype: int

        """
        if channel not in range(1, 9):
            raise Exception('The channel is not supported by the device.')
        return channel

    def check_freq(self, channel, value):
        """ Checks if the frequency asked is valid for the desired channel.
        Specific of our device. If it is not, it gives the right value.

        :param channel: channel to use (can be from 1 to 8 inclusive)
        :type channel: int
        :param value: Frequency value in MHz. If 0 is given,
                      the DEFAULTS['frequency'] value is used for the corresponding channel.
        :type value: float
        :return: The channel and value back unless an error.
        :rtype: int, new_channel

        """
        if value == 0:
            new_value = self.DEFAULTS['frequency'][channel - 1]
            self.logger.debug('Initial Freq 0, setting the default value for channel {}: {}.'.format(value, new_value))
        else:
            new_value = value

        if channel in self.CHANNEL_l:
            if new_value < self.LIM_l[0] or new_value > self.LIM_l[-1]:
                raise Exception('The channel {} does not support the Frequency {} MHz. \n '
                                'The supported range is ({},{}) MHz.'.format(channel, value, self.LIM_l[0],
                                                                             self.LIM_l[1]))
        elif channel in self.CHANNEL_s:
            if new_value < self.LIM_s[0] or new_value > self.LIM_s[-1]:
                raise Exception('The channel {} does not support the Frequency {} MHz. \n '
                                'The supported range is ({},{}) MHz.'.format(channel, value, self.LIM_s[0],
                                                                             self.LIM_s[1]))

        self.logger.debug('The Frequency value {} is OK.'.format(new_value))

        return channel, new_value

    def check_power(self, value):
        """ checks if the power is in the range supported by the device.
        Range = (0 , 22) dBm. Gives an error if value is not in the range

        :param value: power value in dBm
        :type value: float

        """
        if value > self.PW_lim[-1] or value < self.PW_lim[0]:
            raise Exception('The device does not support the power {} dBm. \n '
                            'The supported range is ({},{}) dBm.'.format(value, self.PW_lim[0], self.PW_lim[1]))
        self.logger.debug('The value {} for power in dBm is OK.'.format(value))

    def enable(self, channel, state):
        """Enable single channels.

        :param channel: channel to use (can be from 1 to 8 inclusive)
        :type: channel: int
        :param state: true for on and false for off
        :type state: logical

        :return: state
        :rtype: logical
        """
        self.check_channel(channel)
        if state:
            self.query("L{}O{}".format(channel, 1))
            self.logger.info('Channel {} set on.'.format(channel))
        else:
            self.query("L{}O{}".format(channel, 0))
            self.logger.info('Channel {} set off.'.format(channel))
        return state

    def set_operating_mode(self, channel, mode):
        """Select the operating mode. Can be internal or external.

        :param channel: channel number
        :type channel: int
        :param mode: 'internal' or 'external'
        :type mode: str

        """
        self.logger.debug('Set operating mode: {}'.format(mode))
        self.query("L{}I{}".format(channel, self.MODES[mode]))

    def store(self):
        """ stores in the internal memory the values

        """
        self.logger.info('Stored current configuration in the EPROM of the device at port {}'.format(self.port))
        self.query("E")

    def blanking(self, state, mode):
        """ Define the blanking state. If True (False), all channels are on (off).
        It can also be 'internal' or 'external', where external means that the modulation voltage
        of the channel will be used to define the channel output.

        :param state: State of the blanking
        :type state: logical
        :param mode: external or internal. external is used to follow TTL external modulation
        :type mode: string

        """
        if mode == 'internal':
            if state:
                self.query("L0I1O1")
                self.logger.debug('Blanking set internal and ON.')
            else:
                self.query("L0I1O0")
                self.logger.debug('Blanking set internal and OFF.')
        elif mode == 'external':
            if state:
                self.query("L0I0O1")
                self.logger.debug('Blanking set external and ON.')
            else:
                self.query("L0I0O0")
                self.logger.debug('Blanking set external and OFF.')
        else:
            raise Warning('Blanking type not known.')

    def set_all(self, channel, freq, power, state, mode):
        """ Sets Frequency, power, and state of channel.

        :param channel: channel to use (can be from 1 to 8 inclusive)
        :type channel: int
        :param freq: Frequency value in MHz (range depends on the channel)
        :type freq: float
        :param power: Power to set in dBm (0 to 22 )
        :type power: float
        :param state: true for on and false for off
        :type state: logical
        :param mode: 'internal' or 'external'
        :type mode: string


        """
        if mode == 'internal':
            mode_value = 1
        elif mode == 'external':
            mode_value = 0
        else:
            raise Exception('The mode is not recognized.')

        self.check_channel(channel)
        channel, new_freq = self.check_freq(channel, freq)
        self.check_power(power)

        if state:
            msg = "L{}F{}D{}O1I{}".format(channel, new_freq, power, mode_value)
        else:
            msg = "L{}F{}D{}O0I{}".format(channel, new_freq, power, mode_value)
        self.logger.debug('Message to send: {}'.format(msg))
        ans = self.query(msg)
        return ans

    def get_states(self):
        """ Gets the status of all the channels

        :return: message from the driver describing all channel state
        :rtype: str

        """
        return self.query('S')

    # def interpret_reply(self, msg):
    #     """ This is to interpret the reply of the driver"""
    #     # to do


class AaModd18012Dummy(AaModd18012):
    """
    =================
    AaModd18012 Dummy
    =================

    This is the dummy controller for the AaModd18012. The idea is to load this class instead of the real one
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
        AaModd18012 and some defaults values. This dictionary is saved in properties and will be modified
        when a variable is writen, so the dummy device will respond with the previously set value.

        """
        self.logger.warning('NOT IMPLEMENTED YET')
        # filename = os.path.join(root_dir,'controller', 'dummy', 'lcc25.yml')
        # with open(filename, 'r') as f:
        #     d = yaml.load(f, Loader=yaml.FullLoader)
        #
        # self._properties = d
        # self.logger.debug('_properties dict: {}'.format(self._properties))
        #
        # for key in d:
        #     self.logger.debug('Adding key: {}'.format(key))
        #     self._all[key] = d[key]['default']
        #     for command_key in self.CHAR:
        #         new_command = key + self.CHAR[command_key]
        #         self.logger.debug('Adding to the command list: {}'.format(new_command))
        #         self._commands. append(new_command)
        #
        # self.logger.debug('_all dict: {}'.format(self._all))
        # self._properties['dummy_yaml_file'] = filename  # add to the class the name of the Config file used.
        # self.logger.debug('Commands list: {}'.format(self._commands))


    def write(self, msg):
        """Dummy write. It will compare the msg with the COMMANDS

        :param msg: Message to write
        :type msg: str

        """
        self.logger.warning('NOT IMPLEMENTED YET')
        #
        # self.logger.debug('Writing to dummy LCC25: {}'.format(msg))
        #
        # # next is to check that the command exists in the device and to give the proper response
        # if '=' in msg:
        #     prop = msg.split('=')[0]
        #     value = msg.split('=')[1]
        #     command = prop + '='
        # elif msg[-1] == '?':
        #     prop = msg[:-1]
        #     value = None
        #     command = msg
        #
        # self.logger.debug('prop: {}, value: {}'.format(prop, value))
        # if command in self._commands:
        #     if value is None:
        #         self.logger.debug('Reading the property: {}'.format(prop))
        #         response = self._all[prop]
        #     else:
        #         response = 'Setting property: {} to {}'.format(prop, value)
        #         self.logger.debug(response)
        #         self._buffer.append(msg)
        #         self._all[prop] = value
        # else:
        #     self.logger.error('The command "{}" is not listed as a valid command for LCC25'.format(msg))
        #
        # self.logger.debug('The response is: {}'.format(response))
        # self._response.append(response)


    def read(self):
        """ Dummy read. Reads the response buffer"""
        self.logger.debug('Reading from the dummy device')
        return self._response[-1]


if __name__ == "__main__":
    from hyperion import _logger_format

    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5),
                                                                 backupCount=7),
                            logging.StreamHandler()])

    with AaModd18012(settings={'port':'COM10', 'dummy': True}) as dev:
        dev.initialize()

        # unit_test basic for dummy device
        # dev.write('TESTING WRITE')
        # print(dev.read())
        # print(dev.query('hola'))

        # unit_test set all
        for ch in range(1, 9):
            print(dev.set_all(ch, 0, 22, False, 'internal'))
            sleep(0.1)
        dev.store()
        print(dev.get_states())

        print('DONE.')
