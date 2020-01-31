"""
====================================
Thorlabs thorlabs_motor xyz Meta Instrument
====================================

A very simple wrapper of multiple motor stages. This is used in the xyz_motor gui and depends on thorabs_motor_instrument.py
"""

import logging
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion.instrument.position.thorlabs_motor_instr import Thorlabsmotor

class Thorlabsmotor_xyz(BaseInstrument):

    def __init__(self, settings,zstage=False):
        """ init of the class"""

        self.logger = logging.getLogger(__name__)

        # properties
        self.logger.info('Initializing Thorlabs motor_xyz settings: {}'.format(settings))

        self.settings = settings

        motorxsettings = self.settings['x']
        motorysettings = self.settings['y']
        if zstage==True:
            motorzsettings = self.settings['z']

        self.motorx = Thorlabsmotor(settings=motorxsettings)
        self.motory = Thorlabsmotor(settings=motorysettings)
        self.zstage=False
        if zstage==True:
            self.zstage=True
            self.motorz = Thorlabsmotor(settings=motorzsettings)


if __name__ == '__main__':
    import hyperion

    xyz_motorsettings = {'x':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850121, 'name': 'xMotor'},
              'y':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850122, 'name': 'yMotor'},
              'z':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850123, 'name': 'zMotor'}
              }

    Thorlabsmotor_xyz(settings=xyz_motorsettings)

