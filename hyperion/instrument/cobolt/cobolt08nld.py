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


class CoboltLaser(BaseInstrument):
    """ This class is to control the laser.

    """
    def __init__(self, settings={'port': 'COM5', 'dummy': False,
                                 'controller': 'hyperion.controller.cobolt.cobolt08NLD/Cobolt08NLD',
                                 'via': 'via_serial'}):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class ExampleInstrument created.')

        self.controller.initialize()
        self.DEFAULTS = {}
        #self.load_defaults(defaults)

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
        return self.controller.idn()



if __name__ == '__main__':
    from hyperion import _logger_format

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with CoboltLaser(settings={'port': 'COM5', 'dummy': False,
                                 'controller': 'hyperion.controller.cobolt.cobolt08NLD/Cobolt08NLD'}) as d:

        # #### test idn
        print('Identification = {}.'.format(d.idn()))