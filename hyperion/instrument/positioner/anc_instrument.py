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
import numpy as np
from hyperion import root_dir

from hyperion.instrument.base_instrument import BaseInstrument
from hyperion.experiment.base_experiment import BaseExperiment
from hyperion import ur

class Anc350Instrument(BaseInstrument):
    def __init__(self, settings):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.attocube_piezo_dict = {}

        self.logger.info('1. welcome to the instrument level')
        self.logger.debug('Creating the instance of the controller')

    def initialize(self):
        """ Starts the connection to the device
        """
        self.logger.info('Opening connection to anc350.')
        self.controller.initialize()
        #self.configurate()

    def initialize_available_motors(self):
        experiment = BaseExperiment()
        experiment.load_config("D:\\labsoftware\\hyperion\\examples\\example_experiment_config.yml")

        for instrument in experiment.properties["Instruments"]:
            if "Piezo" in instrument:
                self.attocube_piezo_dict[instrument] = experiment.properties["Instruments"][instrument]["axis_number"]

    def list_devices(self):
        #if the device is on, all its piezo's should be working
        #in any case, there is no way of checking whether one is not working
        print(len(self.attocube_piezo_dict),' piezos found')

    def configurate_stepper(self, axis, amplitude, frequency):
        print('capacitances:')
        print(str(axis)+': ' + str(self.controller.capMeasure(self.attocube_piezo_dict[axis])*ur('mF')))

        # for closed loop positioning the Amplitude Control needs to be set in Step Width mode, nr. 2
        self.controller.amplitudeControl(self.attocube_piezo_dict[axis],2)
        #you need to set the amplitude, max 60V
        #at room temperature you need 30V for x and y and 40V for z
        #at low temperature that is higher, 40V or even 50V
        #higher amplitude influences step size though
        #self.controller.sync_offset(self.settings['sync_offset'].m_as('ps'))
        self.controller.amplitude(self.attocube_piezo_dict[axis],amplitude.m_as('mV'))      #30V
        print('amplitude is ',self.controller.getAmplitude(self.attocube_piezo_dict[axis])*ur('mV'))
        print('so the step width is ',self.controller.getStepwidth(self.attocube_piezo_dict[axis])*ur('nm'))
        # #you also need to set the frequency
        # #higher means more noise and faster (= less precise?)
        self.controller.frequency(self.attocube_piezo_dict[axis],frequency.m_as('Hz'))
        print('frequency is ',self.controller.getFrequency(self.attocube_piezo_dict[axis])*ur('Hz'))
        print('so the speed is ',self.controller.getSpeed(self.attocube_piezo_dict[axis])*ur('nm/s'))


    def configurate_scanner(self,axis):
        print('now we start with the SCANNER')
        print('capacitances:')
        print(str(axis) + ': ' + str(self.controller.capMeasure(self.attocube_piezo_dict[axis]) * ur('mF')))
        # self.controller.load(axis,filename=default)
        #you need to set the mode to INT
        #this means you can apply a voltage of 0-140V to the piezo
        self.controller.intEnable(self.attocube_piezo_dict[axis],True)
        print('is the scanner on INT mode? ',self.controller.getIntEnable(self.attocube_piezo_dict[axis]))

    def move_to(self,axis,position):
        #move to an absolute position with the stepper
        #tell it when you arrive
        print('moving to x = ',position)
        self.controller.moveAbsolute(self.attocube_piezo_dict[axis], position.m_as('nm'))

        # check what's happening
        time.sleep(0.5)
        state = 1
        while state == 1:
            newstate = self.controller.getStatus(self.attocube_piezo_dict[axis])  # find bitmask of status
            if newstate == 1:
                print('axis moving, currently at', self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm'))
            elif newstate == 0:
                arrival = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')
                print('axis arrived at', arrival)
                print('difference is ',position - arrival)
            else:
                print('axis has value', newstate)
            state = newstate
            time.sleep(0.5)

    def move_relative(self, axis, step):
        begin = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')

        print('moving to a relative position, 5um back')
        self.controller.moveRelative(self.attocube_piezo_dict[axis],step.m_as('nm'))

        time.sleep(1)
        state = 1
        while state == 1:
            newstate = self.controller.getStatus(self.attocube_piezo_dict[axis])  # find bitmask of status
            if newstate == 1:
                print('axis moving, currently at', self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm'))
            elif newstate == 0:
                end = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')
                print('axis arrived at', end)
                print('has moved ',begin-end)
            else:
                print('axis has value', newstate)
            state = newstate
            time.sleep(1)


    def given_step(self,axis,direction,amount):
        """

        :param axis:
        :param direction:
        :param amount:
        """
        Steps = []
        print('moving ',amount ,' single steps of stepwidth, determined by set amplitude and frequency')

        #forward 0, backward 1
        #but you have to give it time, because it won't tell you that it's not finished moving yet
        for ii in range(amount):
            self.controller.moveSingleStep(self.attocube_piezo_dict[axis],direction)
            time.sleep(0.5)
            position = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')
            print(ii,': we are now at ',position)
            Steps.append(position.m_as('nm'))

        Steps = np.asarray(Steps)
        Stepsize = np.diff(Steps)
        av_steps = np.mean(Stepsize)
        print('average step size is ',round(av_steps)*ur('nm'))

    def move_scanner(self,axis,voltage):
        print('moving something by putting ',voltage)
        self.controller.dcLevel(self.attocube_piezo_dict[axis],voltage.m_as('mV'))
        print('put a DC level of ',self.controller.getDcLevel(self.attocube_piezo_dict[axis])*ur('mV'))
        print('no way of knowing when and if we ever arrive')

    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.info('Closing connection to device.')
        self.controller.finalize()


if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350'}) as q:
        q.initialize()

        axis = 'XPiezoStepper'       #x van stepper
        ampl = 40000*ur('mV')   #30V
        freq = 1000*ur('Hz')    #Hz

        q.initialize_available_motors()

        q.list_devices()

        q.configurate_stepper(axis,ampl,freq)

        q.move_to(axis,2_000_000*ur('nm'))

        q.move_relative(axis, -5000 * ur('nm'))

        direct = 0  #forward
        steps = 10  #amount of steps

        q.given_step(axis,direct,steps)

        # axis = 'Xscan'
        #
        # q.configurate_scanner(axis)
        #
        # volts = 30000*ur('mV')
        # q.move_scanner(axis,volts)

