# -*- coding: utf-8 -*-
"""
=====================================
Instrument for the cobolt 08NLD laser
=====================================

This class is the instrument layer to control the Cobolt laser model 08-NLD
It ads the use of units with pint
"""
import logging
from hyperion.instrument.base_instrument import BaseInstrument


class CoboltLaser(BaseInstrument):
    """ This class is to control the laser.

    """
    def __init__(self, settings={'dummy': False,
                                 'controller': 'hyperion.controller.cobolt.cobolt08NLD/Cobolt08NLD',
                                 'via_serial': 'COM5'}):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class CoboltLaser Instrument created.')

        self.controller.initialize()
        self.DEFAULTS = {}
        #self.load_defaults(defaults)

    def idn(self):
        """
        Ask for the identification

        :return: message with identification from the device
        :rtype: string
        """
        return self.controller.idn

    @property
    def power_sp(self):
        """ o handle output power set point (mW) in constant power mode
        """
        ans = self.controller.power_sp
        return ans * ur('mW')

    @power_sp.setter
    def power_sp(self, value):
        self.query('p {:.5f}'.format(value / 1000))

    power_setpoint = power_sp

if __name__ == '__main__':
    from hyperion import _logger_format

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with CoboltLaser(settings={'dummy': False,
                               'controller': 'hyperion.controller.cobolt.cobolt08NLD/Cobolt08NLD',
                               'via_serial': 'COM5'}) as d:

        # #### test idn
        print('Identification = {}.'.format(d.idn()))