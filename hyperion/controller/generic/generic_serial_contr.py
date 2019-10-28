# -*- coding: utf-8 -*-
"""
=========================
Generic Serial Controller
=========================

This is a generic controller for Serial devices (like Arduino).
It includes serial write and query methods.
Higher level stuff could (should?) be done at Instrument level.
Extra methods could however also be added to this controller,
as long as they don't break the existing functionality.

This controller is however intended to be agnostic of what code/firmware/sketch
is running on the device. I suggest to keep it that way and put device
specific functionality in a dedicated instrument.
This also means Dummy mode needs to be implemented mostly at Instrument level.

Development note:
I've added the experimental decorator _wait_while_busy_and_after.
If it turns out not to work desirably it can be removed:
remove the application of the decorator on methods initialize, write and read_serial_buffer_in
remove the decorator function itself
remove self._busy and self._additional_timeout from the __init__
"""

import serial
import serial.tools.list_ports
import time
import logging
from hyperion.controller.base_controller import BaseController

class GenericSerialController(BaseController):
    """ Generic Serial Controller """

    def __init__(self, settings):
        """ Init of the class.

        :param settings: This includes all the settings needed to connect to the device in question.
        :type settings: dict
        """
        super().__init__(settings)  # mandatory line
        self.logger = logging.getLogger(__name__)
        self.rsc = None
        self.logger.debug('Generic Serial Controller created.')
        self.name = 'Generic Serial Controller'

        # Storing the settings in internal variables.
        # If they're not specified, default values are used.

        if 'dummy' in settings:
            self.dummy = settings['dummy']
        else:
            self.dummy = False
            
        if 'port' in settings:
            self._port = settings['port']
        else:
            self._port = None
            self.logger.warning('Port not specified in settings. This is mandatory')
        
        if 'baudrate' in settings:
            self._baud = settings['baudrate']
        else:
            self._baud = 9600
            self.logger.debug('Baudrate not specified in settings. Using: {}'.format(self._baud))
            
        if 'write_termination' in settings:
            self._write_termination = settings['write_termination']
        else:
            self._write_termination = '\n'
            self.logger.debug('Write termination not specified in settings. Using: \\n')

        # The code should be able to deal with different read terminations automatically.
        if 'read_termination' in settings:
            self._read_termination = settings['read_termination']
        else:
            self._read_termination = '\n'

        # Write timeout is not really used, I think.
        if 'write_timeout' in settings:
            self._write_timeout = settings['write_timeout']
        else:
            self._write_timeout = 0.1
            
        if 'read_timeout' in settings:
            self._read_timeout = settings['read_timeout']
        else:
            self._read_timeout = 0.5        # in seconds
            self.logger.debug('Read timeout not specified in settings. Using: {}s'.format(self._read_timeout))
            
        if 'encoding' in settings:
            self._encoding = settings['encoding']
        else:
            self._encoding = 'ascii'
            self.logger.debug('Encoding not specified in settings. Using: {}'.format(self._encoding))
            
        if 'name' in settings:
            self.name = settings['name']
        else:
            self.name = 'Serial Device'

        # "global" variables for decorator function _wait_while_busy_and_after
        self._busy = False
        self._additional_timeout = time.time()

    # define a decorator function to
    def _wait_while_busy_and_after(additional_timeout=0):
        """
        This decorator prevents any method that it is applied to from running simultaneously.
        Applying this decorator to a method, sets the _busy flag of the object and makes any method
        that has this decorator wait until the _busy flag is set to false after the previous method
        has finished. This blocking functionality of a method can be extended by setting the
        additional_timeout argument > 0. This is useful for the initialize method e.g..
        """
        def decorator(fn):
            def wrapper(*args, **kwargs):
                while args[0]._busy or time.time() < args[0]._additional_timeout:
                    pass
                args[0]._busy = True            # set self._busy True
                result = fn(*args, **kwargs)    # run the function
                args[0]._additional_timeout = time.time() + additional_timeout
                args[0]._busy = False           # set self._busy False
                return result
            return wrapper
        return decorator

    @_wait_while_busy_and_after(additional_timeout=1.5)
    def initialize(self):
        """ Starts the connection to the device using the specified port."""

        self.rsc = serial.Serial(port=self._port,
                                     baudrate=self._baud,
                                     timeout=self._read_timeout,
                                     write_timeout=self._write_timeout)
        self.logger.debug('Initialized Serial connection to {} on port {}.'.format(self.name, self._port))
        self._is_initialized = True     # THIS IS MANDATORY!!
                                        # this is to prevent you to close the device connection if you
                                        # have not initialized it inside a with statement


    def finalize(self):
        """
        This method closes the connection to the device.
        It is ran automatically if you use a with block.
        """
        
        if self._is_initialized:
            if self.rsc is not None:
                self.rsc.close()
                self.logger.debug('The Serial connection to {} is closed.'.format(self.name))
        else:
            self.logger.warning('Finalizing before initializing connection to {}'.format(self.name))

        self._is_initialized = False

    def idn(self):
        """
        Identify command

        :return: identification for the device
        :rtype: string
        """
        self.logger.debug('Ask *IDN? to device.')
        return self.query('*IDN?')[-1]

    @_wait_while_busy_and_after(additional_timeout=0)
    def write(self, message):
        """
        Sends the message to the device.

        :param message: the message to write to the device
        :type message: string
        """
        if not self._is_initialized:
            raise Warning('Trying to write to {} before initializing'.format(self.name))

        message += self._write_termination
        self.logger.debug('Sending to device: {}'.format(message))
        self.rsc.write( message.encode(self._encoding) )

    @_wait_while_busy_and_after(additional_timeout=0)
    def read_serial_buffer_in(self, wait_for_termination_char = True):
        """
        Reads everything the device has sent. By default it waits until a line
        is terminated by a termination character (\n or \r), but that check can
        be disabled using the input parameter.

        :param wait_for_termination_char: defaults to True
        :type wait_for_termination_char: bool
        :return: complete serial buffer from the device
        :rtype: bytes
        """
        if not self._is_initialized:
            raise Warning('Trying to read from {} before initializing'.format(self.name))
        
        # At least for Arduino, it appears the buffer is filled in chuncks of max 32 bytes
        byte_time = 1/self.rsc.baudrate * (self.rsc.bytesize + self.rsc.stopbits + (self.rsc.parity != 'N'))
        raw = b''
        in_buffer = 0
        new_in_buffer = 0
        term_chars = '\n\r'.encode(self._encoding)
        ends_at_term_char = False
        #start_time = time.time() + 0.0001
        # Keep checking 
        expire_time = time.time() +  self._read_timeout + .0000000001
        while (not ends_at_term_char) and (time.time() < expire_time):
            time.sleep(byte_time*20)
            new_in_buffer = self.rsc.in_waiting
            if new_in_buffer > in_buffer:
                # if the buffer has grown make sure the expire_time is at least long enough to read in another 32 bytes
                expire_time = max(expire_time, time.time()+byte_time*32)
                in_buffer = new_in_buffer
            
            raw += self.rsc.read( self.rsc.in_waiting )
            if not wait_for_termination_char or (len(raw) and (raw[-1] in term_chars)):
                ends_at_term_char = True
            
        self.logger.debug('{} bytes received'.format(len(raw)))
        return raw
           
    def read_lines(self, remove_leading_trailing_empty_line=True):
        """
        Reads all lines the device has sent and returns list of strings.
        It interprets both \r \n and combinations as a newline character.

        :param remove_leading_trailing_empty_line: defaults to True
        :type remove_leading_trailing_empty_line: bool
        :return: list of lines received from the device
        :rtype: list of strings
        """
        
        response = str(self.read_serial_buffer_in(), encoding=self._encoding)
        response = response.replace('\n\r','\n')
        response = response.replace('\r\n','\n')
        response = response.replace('\r','\n')
        response_list = response.split('\n')
        if remove_leading_trailing_empty_line:
            if len(response_list) and response_list[-1]=='':
                del response_list[-1]
            if len(response_list) and response_list[0]=='':
                del response_list[0]
        return response_list
    
    def query(self, message):
        """
        Writes message in the device Serial buffer and Reads the response.
        Note, it clears the input buffer before sending out the query.

        :param message: command to send to the device
        :type message: str
        :return: list of responses received from the device
        :rtype: list of strings
        """
        if not self._is_initialized:
            raise Warning('Trying to query {} before initializing.'.format(self.name))

        self.rsc.reset_output_buffer()
        self.rsc.reset_input_buffer()
        self.write(message)
        self.logger.debug('Sent message: {}.'.format(message))
        ans = self.read_lines()
        self.logger.debug('Received message: {}.'.format(ans))
        return ans
    


class GenericSerialControllerDummy(GenericSerialController):
    """
    Generic Serial Controller Dummy
    ===============================

    A dummy version of the Generic Serial Controller.

    Note that because Generic Serial Controller is supposed to be device agnostic
    this dummy can't simulate every device. For devices using this Controller,
    simulation has to be done at Instrument level.
    This Dummy only stores write messages in a buffer and returns this buffer with
    the read_serial_buffer_in method.

    All other methods are are kept from GenericSerialController.
    """

    def _empty_buffer(self):
        self._buffer = ''.encode(self._encoding)

    def initialize(self):
        """ Initializes Generic Serial Controller Dummy device."""
        self.logger.debug('Dummy Generic Serial Controller device initialized')
        self._empty_buffer()
        self._is_initialized = True

    def finalize(self):
        """ Finalizes Generic Serial Controller Dummy device."""
        self.logger.debug('Finalizing Dummy Generic Serial Controller device')
        self._is_initialized = False

    def write(self, message):
        """Simulates write to dummy device (adds message to an internal buffer).
        :param message: message to write
        :type message: string
        """
        if not self._is_initialized:
            raise Warning('Trying to write to DUMMY {} before initializing'.format(self.name))
        self.logger.debug('Adding message to internal buffer:')
        self.logger.debug(message)
        self._buffer.append(message.encode(self._encoding))

    def read_serial_buffer_in(self, wait_for_termination_char=True):
        """Simulates read from dummy device (returns internal buffer).
        """
        if not self._is_initialized:
            raise Warning('Trying to read from DUMMY {} before initializing'.format(self.name))
        self.logger.debug('Returning internal buffer')
        ans = self._buffer
        self._empty_buffer()
        return ans

    def query(self, message):
        """
        Simulates query to dummy device.
        Clears the internal buffer. Performs a write, followed by a read_lines()
        Note, it clears the input buffer before sending out the query.

        :param message: command to send to the device
        :type message: str
        :return: response from the device
        :rtype: str
        """
        if not self._is_initialized:
            raise Warning('Trying to query DUMMY {} before initializing.'.format(self.name))
        self._empty_buffer()
        self.write(message)
        return self.read_lines()


    def wait_if_busy(fn):
        def wrapper(*args, **kwargs):
            print('before')
            return fn(*args, **kwargs)
            print(after)
        return wrapper

if __name__ == "__main__":
    from hyperion import _logger_format, _logger_settings
    logging.basicConfig(level=logging.WARNING, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    dummy = False  # change this to False to work with the real device in the COM specified below.

    if dummy:
        my_class = GenericSerialControllerDummy
    else:
        my_class = GenericSerialController

    example_settings = {'port': 'COM4', 'baudrate': 9600, 'write_termination': '\n'}

    # some test code for my arduino testing device:
    with my_class(settings = example_settings) as dev:
        dev.initialize()
        print('Start:')
        # print the startup message in the buffer
        [print(line) for line in dev.read_lines()]

       # for x in range(2):
       #     time.sleep(.3)
       #     dev.write('2r')
       #     time.sleep(.3)
       #     dev.write('2g')

        print('ch1: {}'.format( dev.query('1?')[-1] ))
        print('ch2: {}'.format( dev.query('2?')[-1] ))
        print('idn: {}'.format( dev.idn() ))
        print('done')


""" Tip:
    Useful features of pyserial are
    
    To list all devices:
    
    comports = serial.tools.list_ports.comports()
    for port, desc, hwid in comports:
        print((port,desc,hwid))
        
    To find a specific device by part of the name

    part_of_name = 'rduino'
    usb_dev = next(serial.tools.list_ports.grep(part_of_name))
    print( usb_dev.description )
    print( usb_dev.hwid )
    print( usb_dev.device )
"""
