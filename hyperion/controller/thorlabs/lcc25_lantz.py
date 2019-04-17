# -*- coding: utf-8 -*-
# not reviewed for hyperion
"""
LCC 25
======

This is the controller for the LCC25 variable waveplate driver from Thorlabs.

"""
from lantz.core import MessageBasedDriver
from lantz import Feat, DictFeat
from lantz.log import log_to_screen, DEBUG


class Lcc25(MessageBasedDriver):
    """ This is the LCC25 driver class using Lantz

    """

    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\n'},
                'ARSL': {'encoding': 'ascii',
                         'baudrate': 115200,
                         'write_timeout': 1,
                         'read_timeout': 1}
                }

    @Feat()
    def idn(self):
        """ Identification of the device
        """
        return self.query('*idn?')

    @DictFeat(keys=list(range(1, 3)), units='V', limits=(0, 25))
    def voltage(self, key):
        """ Voltage value for channel given by key.

        :param key: channel to read. can be 1 or 2
        :type key: int
        """
        return self.query('volt{}?'.format(key))

    @voltage.setter
    def voltage(self, channel, v):
        """ Sets the voltage for the channel to the voltage value v.

        :param channel: channel to use, can be 1 or 2
        :type channel: int
        :param v: voltage to set
        :type v: pint quantity

        """
        self.write('volt{}={}'.format(channel, v))

    @DictFeat(values={True: 1, False: 0})
    def output_enabled(self):
        """Asks if the analog output is enabled.
        """
        return int(self.query('enable?'))

    @output_enabled.setter
    def output_enabled(self, bool):
        """ Sets the state of the analog output. """
        self.query('enable={}'.format(bool))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-p', '--port', type=str, default='6',
                        help='Serial port to connect to')
    args = parser.parse_args()

    log_to_screen(DEBUG)

    v = Q_(1, 'volts')

    with Lcc25.via_serial(args.port) as inst:
        print(inst.idn)

        inst.voltage[0] = v
        inst.output[1] = 2 * v
        print(inst.output[0])
        print(inst.output[1])

