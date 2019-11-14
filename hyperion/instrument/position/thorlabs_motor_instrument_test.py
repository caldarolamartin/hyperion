"""
====================================
Thorlabs thorlabs_motor Instrument
====================================

"""

import logging
from hyperion.instrument.base_instrument import BaseInstrument

from hyperion import ur


class Thorlabsmotor(BaseInstrument):
    """ Thorlabsmotor instrument

    """
    
    def __init__(self, settings):
        """ init of the class"""
        
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)

        # properties
        self._output = False
        self._mode = 0
        self.logger.info('Initializing Thorlabs motor settings: {}'.format(settings))

        # if 'serial' in settings:
        #     self._serial_number = settings['serial']
        #     self.initialize()



if __name__ == "__main__":
    import hyperion

    xMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850129}

    yMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850123}

    with Thorlabsmotor(settings = xMotor) as sampleX, Thorlabsmotor(settings = yMotor) as sampleY:
        # dev.initialize()

        print(type(sampleX.controller._serial_number))

        print(sampleX.controller.get_stage_axis_info())

        print(sampleX.controller.position)



