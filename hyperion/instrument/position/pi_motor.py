"""
====================================
Thorlabs thorlabs_motor Instrument
====================================

Connects to the pi_motorcontroller controller, which is just a wrapper for the core underneath that we installed.

"""
from hyperion import logging
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur
import time

class PImotor(BaseInstrument):
    """ Thorlabsmotor instrument
    """
    def __init__(self, settings):
        """ init of the class"""

        super().__init__(settings)
        self.logger = logging.getLogger(__name__)

        # properties
        self._output = False
        self._mode = 0
        self.logger.info('Initializing PI motor settings: {}'.format(settings))

        self.settings = settings
        self._name = self.settings['name']

        self.initialize()



    def initialize(self):

        self.logger.info('Initializing your {} and checking some basic things.'.format(self._name))

        self.real_controller=self.controller.initialize()



    def finalize(self):
        """ This would have been to close connection to the device, but that method does not exist in the core controller.
        """
        self.logger.info('Should close connection to cube: {}'.format(self._name))

    def position(self):
        """| Asks the position to the controller and returns that.

        """
        pos = self.real_controller.qPOS()
        position=float(pos['A'])
        position=ur(str(position)+"mm")
        return position

    def move_absolute(self,target):
        value=target.m
        unit=target.u
        if unit=='micrometer':
            value_real=value*1e-3
        if unit=='millimeter':
            value_real=value*1e1
        if unit=='nanometer':
            value_real=value*1e-6
        self.real_controller.MOV(self.real_controller.axes, value_real)#in mm

    def move_relative(self,shift):
        value=shift.m
        unit=shift.u
        if unit=='micrometer':
            value_real=value*1e-3
        if unit=='millimeter':
            value_real=value*1
        if unit=='nanometer':
            value_real=value*1e-6
        target=self.position().m+value_real
        self.real_controller.MOV(self.real_controller.axes, target)

if __name__ == "__main__":

    settings = {'controller': 'hyperion.controller.pi.pi_motorcontroller/PI_motorcontroller', 'name': 'Delaystage775','controllername': "C-836.10",'stages':'M-404.6PD','refmode':'MNL'}

    with PImotor(settings = settings) as sampleX:
        sampleX.position()