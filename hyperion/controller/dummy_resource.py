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
    def __init__(self, resource, encoding='ascii', read_termination='\r'):
        """ Init

        :param resource: id or port
        :type resource: str
        :param encoding: sets the encoding for the device
        :type encoding: str
        :param read_termination: character to finish a line
        :type read_termination: str

        """
        self.encoding = encoding
        self.read_termination = read_termination
        self.name = resource
        self.device_name = None
        if resource == 'COM6':
            self.device_name = 'lcc25'

        self.logger = logging.getLogger(__name__)
        self.responses = {}
        self.load_responses()
        self._write_buffer = []
        self._read_buffer = []

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
            d = yaml.load(f)
            self.logger.info('Loaded fake responses: {}'.format(filename))

        self.logger.debug('Loaded all responses: {}'.format(d))
        if self.device_name is not None:
            self.responses = d[self.device_name]
            self.logger.debug('Responses for device {}: {}'.format(self.device_name, self.responses))


    def write(self, msg):
        """ Write in the dummy device.

        :param msg: message to write in the dummy device
        :type msg: str
        :return: answer from the device
        :rtype: str

        """
        self.logger.info('Writing to {} message: {}'.format(self.name, msg))
        self._write_buffer.append(msg)
        return 'some response'

    def read(self):
        """ Reads from the dummy device

        :return: message received from the device
        :rtype: str

        """
        self.logger.info('Reading from: {}'.format(self.name))
        if self._write_buffer[-1] in self.responses:
            ans = self.responses[self._write_buffer[-1]]
        else:
            ans = 'Inteligent response not implemented: this is dummy general response!'
        return ans

    def readline(self):
        """ reads a line, until a read_termination character is found.

        :return: line read.
        :rtype: str

        """
        self.logger.info('Reading from: {}'.format(self.name))
        ans = self.read_termination + 'Line dummy response' + self.read_termination
        ans = ans.encode(self.encoding)

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

    with DummyResourceManager('COM6') as rsc:
        print(rsc.responses)
        print(rsc.query('volt1?'))