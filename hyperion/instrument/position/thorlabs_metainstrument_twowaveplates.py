"""
====================================
Thorlabs two waveplates instrument Meta Instrument
====================================

A very simple wrapper of multiple motor stages. This is used in the two waveplates gui and depends on thorabs_motor_instrument.py
"""

import logging
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion.instrument.position.thorlabs_motor_instr import Thorlabsmotor


class Thorlabsmotor_twowp(BaseInstrument):

    def __init__(self, settings):
        """ init of the class"""

        self.logger = logging.getLogger(__name__)

        # properties
        self.logger.info('Initializing Thorlabs motor two waveplates metaintstrument settings: {}'.format(settings))

        self.settings = settings

        wp_onesettings = self.settings['wp_one']
        wp_twosettings = self.settings['wp_two']


        self.wp_one = Thorlabsmotor(settings=wp_onesettings)
        self.wp_two = Thorlabsmotor(settings=wp_twosettings)



if __name__ == '__main__':
    import hyperion

    wp_motorsettings = {'wp_one':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83817715, 'name': 'waveplate 1200 nm'},
              'wp_two':{'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83817710, 'name': 'waveplate 1200 nm'}}


    Thorlabsmotor_twowp(settings=wp_motorsettings)

