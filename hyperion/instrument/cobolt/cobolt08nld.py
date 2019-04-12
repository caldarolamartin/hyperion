# -*- coding: utf-8 -*-
"""
=====================================
Instrument for the cobolt 08NLD laser
=====================================

This class is the instrument layer to control the Cobolt laser model 08-NLD
It ads the use of units with pint
"""
import logging
from lantz.drivers.cobolt.cobolt0601 import Cobolt0601
from hyperion import ur, root_dir
from hyperion.controller.agilent.agilent33522A import Agilent33522A
from hyperion.instrument.base_instrument import BaseInstrument


class Cobolt08NLD(BaseInstrument):
    """ This class is to control the laser.

    """
    def __init__(self, instrument_id, dummy=True):
        """
        Initialize the fun gen class

        :param instrument_id: name of the port where the aotf is connected, like 'COM10'
        :type instrument_id: str
        :param defaults: used to load the default values in the config.ylm
        :type defaults: logical
        :param dummy: logical value to allow testing without connection
        :type logical
        """
        self.logger = logging.getLogger(__name__)
        parser = argparse.ArgumentParser(description='Test Kentech HRI')
        parser.add_argument('-i', '--interactive', action='store_true',
                            default=False, help='Show interactive GUI')
        parser.add_argument('-p', '--port', type=str, default='COM5',
                            help='Serial port to connect to')

        args = parser.parse_args()

        self.dummy = dummy
        self.CHANNELS = [1, 2]
        self.FUN = ['SIN', 'SQU', 'TRI', 'RAMP', 'PULS', 'PRBS', 'NOIS', 'ARB', 'DC']
        self.logger.info('Initializing device Agilent33522A number = {}'.format(instrument_id))
        self.instrument_id = instrument_id
        self.name = 'Cobolt06NLD'
        self.driver = Cobolt0601(instrument_id, dummy=dummy)
        if dummy:
            self.logger.info('Working in dummy mode')

        self.driver.initialize()
        self.DEFAULTS = {}
        self.load_defaults(defaults)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def idn(self):
        """
        Ask for the identification

        :return: message with identification from the device
        :rtype: string
        """
        return self.driver.idn()


if __name__ == '__main__':
    from hyperion import _logger_format

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with FunGen('8967', defaults=False, dummy=True) as d:
        print('Output state for channels = {}'.format(d.output_state()))

        # #### test idn
        print('Identification = {}.'.format(d.idn()))