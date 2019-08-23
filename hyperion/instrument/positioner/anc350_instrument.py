"""
====================
ANC350 Attocube Instrument
====================

This is the instrument level of the positioner ANC350 from Attocube (in the Montana)

"""

import logging
import yaml           #for the configuration file
import os             #for playing with files in operation system
import sys
import time
from hyperion import root_dir

from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur
ureg = ur

class Anc350Instrument(BaseInstrument):
    def __init__(self, settings):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)

        self.logger.info('1. welcome to the instrument level')
        self.logger.debug('Creating the instance of the controller')

    def initialize(self):
        """ Starts the connection to the device
        """        
        self.logger.info('Opening connection to anc350.')
        self.controller.initialize()
        #self.controller.calibrate()
        #self.configurate()

    def configurate(self):
        #load the actor file
        #put the required settings
        pass

    def move_to(self,position):
        #move to a position
        #tell it when you arrive
        pass

    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.info('Closing connection to device.')
        self.controller.finalize()


if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with Anc350Instrument('controller': 'hyperion.controller.attocube.anc350/Anc350'}) as q:
        q.initialize()

        q.configurate()

        q.move_to()



        q.finalize()


