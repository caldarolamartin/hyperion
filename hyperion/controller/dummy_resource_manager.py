# -*- coding: utf-8 -*-
"""
Dummy Resource Manager
======================

This is a class to emulate dummy devices. It provides a fake read, write and query to use
when the controllers are in dummy mode.

"""
import logging
import os
import yaml
from hyperion import root_dir


class DummyResourceManager():
    """ This is a dummy class to emulate the visa resource manager and serial.

    """
    def __init__(self, port, name, encoding='ascii', read_termination='\r'):
        """ Init

        :param resource: id or port
        :type resource: str
        :param encoding: sets the encoding for the device
        :type encoding: str
        :param read_termination: character to finish a line
        :type read_termination: str

        """
        self.logger = logging.getLogger(__name__)
        self.encoding = encoding
        self.name = name
        self.read_termination = read_termination
        self.port = port
        self.load_responses()
        self._write_buffer = ['s']
        self._read_buffer = ['s']

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        return 'DummyResourceManager'

    def load_responses(self, filename = None):
        """ This method loads the yml file with the fake responses from devices.

        """
        if filename is None:
            filename = os.path.join(root_dir, 'controller', 'dummy', 'device_response.yml')

        with open(filename, 'r') as f:
            d = yaml.load(f, Loader=yaml.FullLoader)
            self.logger.info('Loaded fake responses from file: {}'.format(filename))

        if self.name in d:
            self.responses = d[self.name]['query']
            self.logger.debug('Responses for device {}: {}'.format(self.name, self.responses))


    def write(self, msg):
        """ Write in the dummy device.

        :param msg: message to write in the dummy device
        :type msg: str
        :return: answer from the device
        :rtype: str

        """
        self.logger.info('Writing to {} message: {}'.format(self.name, msg))
        msg = msg.decode().split(self.read_termination)[0]
        self.logger.debug('Message to compare: {}'.format(msg))
        if msg in self.responses:
            self._write_buffer.append(msg.encode(self.encoding))
            self._read_buffer.append(str(self.responses[msg]))
        else:
            self.logger.warning('This is not a query command.')

        return 'some response'

    def read(self):
        """ Reads from the dummy device

        :return: message received from the device
        :rtype: str

        """
        self.logger.info('Reading from dummy: {}'.format(self.name))
        ans = self._read_buffer[-1] + self.read_termination
        ans = ans.encode(self.encoding)
        self.logger.debug('response: {}'.format(ans))
        return ans

    def readline(self):
        """ reads a line, until a read_termination character is found.

        :return: line read.
        :rtype: str

        """
        ans = self.read()
        return ans

    def query(self, msg):
        """ Write - Read cycle.

        :param msg: message to write
        :type msg: str

        :return: response from the dummy device
        :rtype: str

        """
        self.write(msg)
        ans = self.read()
        return ans

    def close(self):
        """ To close the dummy resource

        :return: OK flag
        :rtype: str

        """
        self.logger.info('Closing dummy resource')
        return 'OK'


if __name__ == "__main__":
    from hyperion import _logger_format

    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with DummyResourceManager('COM8', 'lcc25') as rsc:
        print(rsc.query('volt1?'))
        print(rsc._write_buffer)
        print(rsc._read_buffer)