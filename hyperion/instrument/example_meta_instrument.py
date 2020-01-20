# -*- coding: utf-8 -*-
"""
==================
Example Instrument
==================

This is an example instrument, created to give developers a canvas to start their own instruments
for real devices. This is only a dummy device.

"""
from hyperion.core import logman as logging # another way to do it
from hyperion.instrument.base_instrument import BaseMetaInstrument
from hyperion.instrument.example_instrument import ExampleInstrument
from hyperion import ur
import numpy as np

class ExampleMetaInstrument(BaseMetaInstrument):
    """ Example instrument. it is a fake instrument

    """
    def __init__(self, settings, sub_instruments):
        """ init of the class"""
        super().__init__(settings, sub_instruments)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class ExampleMetaInstrument created.')

        self.x = sub_instruments['x']
        self.y = sub_instruments['y']
        self.z = sub_instruments['z']

    def circle(self):
        for angle in np.linspace(0, 2, 9):
            self.x.amplitude = np.cos(angle * np.pi) * ur('volts')
            self.y.amplitude = np.sin(angle * np.pi) * ur('volts')
            print('angle={:1.2f} pi    x={:.4f}    y={:.4f}'.format(angle, np.round(self.x.amplitude, 4), np.round(self.y.amplitude, 4)))

if __name__ == "__main__":

    logging.stream_level = logging.WARNING

    dummy = True

    x_instr = ExampleInstrument(settings = {'port':'COM8', 'dummy' : dummy,
                                   'controller': 'hyperion.controller.example_controller/ExampleController'})
    y_instr = ExampleInstrument(settings={'port': 'COM9', 'dummy': dummy,
                                          'controller': 'hyperion.controller.example_controller/ExampleController'})
    z_instr = ExampleInstrument(settings={'port': 'COM10', 'dummy': dummy,
                                          'controller': 'hyperion.controller.example_controller/ExampleController'})


    meta_instr = ExampleMetaInstrument(settings = {'dummy' : dummy}, sub_instruments={'x': x_instr, 'y': y_instr, 'z': z_instr})
    meta_instr.circle()

    print('done')