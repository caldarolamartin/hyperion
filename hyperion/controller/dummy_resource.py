"""
Dummy Resource Manager
======================

This is a class to emulate dummy devices. It provides a fake read, write and query to use
when the controllers are in dummy mode.

"""
import logging


class DummyResourceManager():
    """ This is a dummy class to emulate the visa resource manager and serial."""

    def __init__(self, resource, encoding = 'ascii', read_termination = '\r'):
        """ Init"""
        self.encoding = encoding
        self.read_termination = read_termination
        self.name = resource
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        return 'DummyResourceManager'

    def write(self, msg):
        self.logger.info('Writing to {} message: {}'.format(self.name, msg))

    def read(self):
        self.logger.info('Reading from: {}'.format(self.name))
        ans = 'dummy response!'
        return ans

    def readline(self):
        self.logger.info('Reading from: {}'.format(self.name))
        ans = self.read_termination + 'Line dummy response' + self.read_termination
        ans = ans.encode(self.encoding)

        return ans

    def query(self, msg):
        self.write(msg)
        ans = self.read()
        return ans

    def close(self):

        self.logger.info('Closing dummy resource')
        return 'OK'