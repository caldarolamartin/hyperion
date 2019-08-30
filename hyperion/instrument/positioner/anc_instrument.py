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
        self.Amplitude = np.zeros(3)     #here we will remember which amplitudes are set on the steppers
        self.Stepwidth = np.zeros(3)     #here we will remember what the amplitudes means in terms of stepsize
        self.Frequency = np.zeros(3)
        self.Speed = np.zeros(3)

        self.logger.info('1. welcome to the instrument of the Attocube')
        self.logger.debug('Creating the instance of the controller')

    def initialize(self):
        """ Starts the connection to the device
        """
        self.logger.info('Opening connection to anc350.')
        self.controller.initialize()
        #self.configurate()

    def initialize_available_motors(self):
        """ | Start the connection to the device
        | Makes a dictionary of axis names based on the example_experiment_config.yml file
        """
        experiment = BaseExperiment()
        experiment.load_config("D:\\labsoftware\\hyperion\\examples\\example_experiment_config.yml")

        for instrument in experiment.properties["Instruments"]:
            if "Piezo" in instrument:
                self.attocube_piezo_dict[instrument] = experiment.properties["Instruments"][instrument]["axis_number"]

        self.logger.info('Started the connection to the device and loaded the yml file')

    def list_devices(self):
        """ | Gives a list of the connected piezo's
        | If the device is on, all its piezo's should be working
        | **There is no way of checking whether one is not working**
        | So just gives the dictionary created in initialize_available_motors
        """
        devices = len(self.attocube_piezo_dict)
        self.logger.info(str(devices)+ ' piezos found')

    def configurate_stepper(self, axis, amplitude, frequency):
        """ - Does the necessary configuration of the Stepper:
        - for closed loop positioning the Amplitude Control needs to be set in Step Width mode, nr. 2
        - **loads the actor file, now it's the file called q**
        - measures the capacitance of the Stepper; **not clear whether it is needed**
        - sets the amplitude and frequency
        - the amplitude influences the step width, the frequency influences the speed
        - *for closed loop positioning the Amplitude Control needs to be set in Step Width mode, nr. 2*

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param amplitude: amplitude voltage; at room temperature you need 30V-40V, at low temperatures 40V-50V, max 60V; high amplitude is large stepwidth
        :type axis: pint quantity

        :param frequency: frequency to be set; higher means more noise but faster; between 1Hz and 2kHz
        :type axis: pint quantity
        """

        self.logger.info('Loading Stepper actor file, measuring capacitances')

        capacitance = self.controller.capMeasure(self.attocube_piezo_dict[axis])*ur('mF')
        capacitance = round(capacitance.to('F'),3)
        self.logger.info(axis+': ' + str(capacitance))

        #self.controller.load(axis,filename=default)
        self.controller.amplitudeControl(self.attocube_piezo_dict[axis],2)
        self.logger.debug('Stepper Amplitude Control put in StepWidth mode')

        if 0 <= amplitude.m_as('V') <= 60:
            self.controller.amplitude(self.attocube_piezo_dict[axis], int(amplitude.m_as('mV')))  # put the amplitude on the controller, it needs to be an int

            self.Amplitude[self.attocube_piezo_dict[axis]] = amplitude.m_as('V')   #remember that amplitude in V

            step = self.controller.getStepwidth(self.attocube_piezo_dict[axis])
            #huh, 0 makes no sense!!!!
            self.Stepwidth[self.attocube_piezo_dict[axis]] = step                   #remember the associated step width

            ampl = self.controller.getAmplitude(self.attocube_piezo_dict[axis]) * ur('mV')
            self.logger.info('amplitude is now ' + str(ampl.to('V')))
            self.logger.info('so the step width is ' + str(step * ur('nm')))
        else:
            raise Exception('The required amplitude needs to be between 0V and 60V')

        if 1 <= frequency.m_as('Hz') <= 2000:
            self.controller.frequency(self.attocube_piezo_dict[axis], frequency.m_as('Hz'))     #put the frequency on the controller

            self.Frequency[self.attocube_piezo_dict[axis]] = frequency.m_as('Hz')           #remember that frequency

            speed = self.controller.getSpeed(self.attocube_piezo_dict[axis]) *ur('nm/s')               #remember the associated speed
            self.Speed[self.attocube_piezo_dict[axis]] = speed.m_as('nm/s')

            self.logger.info('frequency is ' + str(self.controller.getFrequency(self.attocube_piezo_dict[axis]) * ur('Hz')))
            self.logger.info('so the speed is ' + str(round(speed.to('mm/s'),4)))
        else:
            raise Exception('The required frequency needs to be between 1Hz and 2kHz')

    def configurate_scanner(self,axis):
        """- Does the necessary configuration of the Scanner:
        - you need to set the mode to INT, not DC-IN
        - loads the actor file
        - measures the capacitance of the Scanner; **not clear whether it is needed**

        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner or ZPiezoScanner
        :type axis: string

        """
        self.logger.info('Loading Scanner actor file, setting INT mode, measuring capacitances')

        capacitance = self.controller.capMeasure(self.attocube_piezo_dict[axis])*ur('mF')
        capacitance = round(capacitance.to('F'),3)
        self.logger.info(axis+': ' + str(capacitance))
        # self.controller.load(axis,filename=default)

        self.controller.intEnable(self.attocube_piezo_dict[axis],True)
        self.logger.debug('is the scanner on INT mode? ' + str(self.controller.getIntEnable(self.attocube_piezo_dict[axis])))

    def move_to(self,axis,position):
        """| Moves to an absolute position with the Stepper and tells when it arrived
        | **Pay attention: does not indicate if you take a position outside of the boundary, but you will keep hearing the noise of the piezo**

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param position: absolute position that you want to go to; needs to be an integer, no float!
        :type axis: pint quantity

        """
        self.logger.info('Moving ' + axis +' to position: '+ str(position))
        self.controller.moveAbsolute(self.attocube_piezo_dict[axis], int(position.m_as('nm')))

        # check what's happening
        time.sleep(0.5)
        state = 1
        while state == 1:
            newstate = self.controller.getStatus(self.attocube_piezo_dict[axis])  # find bitmask of status
            if newstate == 1:
                pos = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')
                self.logger.info(axis +' moving, currently at ' + str(round(pos.to('mm'),6)))
            elif newstate == 0:
                end = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')
                self.logger.info('axis arrived at ' + str(round(end.to('mm'),6)))
                self.logger.info('difference is ' + str(round(position - end,6)))
            else:
                self.logger.info('axis has value' + str(newstate))
            state = newstate
            time.sleep(0.5)

    def move_relative(self, axis, step):
        """| Moves the Stepper by an amount to be given by the user
        | **Pay attention: does not indicate if you take a position outside of the boundary, but you will keep hearing the noise of the piezo**

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param step: amount to move, can be both positive and negative; needs to be an integer, no float!
        :type step: pint quantity
        """
        begin = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')

        self.logger.info('moving to a relative position, ' + str(step))
        self.controller.moveRelative(self.attocube_piezo_dict[axis],int(step.m_as('nm')))

        time.sleep(1)
        state = 1
        while state == 1:
            newstate = self.controller.getStatus(self.attocube_piezo_dict[axis])  # find bitmask of status
            if newstate == 1:
                pos = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')
                self.logger.info(axis+' moving, currently at ' + str(round(pos.to('mm'),6)))
            elif newstate == 0:
                end = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')
                self.logger.info('axis arrived at ' + str(round(end.to('mm'),6)))
                self.logger.info('has moved ' + str(round(begin - end,6)))
            else:
                self.logger.info('axis has value' + str(newstate))
            state = newstate
            time.sleep(1)

    def given_step(self,axis,direction,amount):
        """| Moves by a number of steps that theoretically should be determined by the set amplitude and frequency; in practice it's different
        | *You have to give it a lot of time, things break if you ask too much whether it is finished yet*

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param direction: direction to move: forward = 0, backward = 1
        :type direction: integer

        :param amount: amount of steps that you want to take
        :type amount: integer
        """
        Steps = []
        self.logger.info('moving ' + axis + ' by ' + str(amount) + ' steps of stepwidth '+ str(self.Stepwidth[self.attocube_piezo_dict[axis]]))

        for ii in range(amount):
            self.controller.moveSingleStep(self.attocube_piezo_dict[axis],direction)
            time.sleep(0.5)
            position = self.controller.getPosition(self.attocube_piezo_dict[axis])*ur('nm')
            self.logger.info('step ' + str(ii) + ': we are now at ' + str(round(position.to('mm'),6)))
            Steps.append(position.m_as('nm'))

        Steps = np.asarray(Steps)
        Stepsize = np.diff(Steps)
        av_steps = np.mean(Stepsize)
        self.logger.info('average step size is ' + str(round(av_steps)*ur('nm')))

    def move_scanner(self, axis, voltage):
        """ | Moves the Scanner by applying a certain voltage
        | *There is no calibration, so you don't know how far; but the range is specified for 50um with a voltage of 0-140V*

        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner or ZPiezoScanner
        :type axis: string

        :param voltage: voltage to move the scanner; from 0-140V
        :type voltage: pint quantity
        """

        if 0 <= voltage.m_as('V') <= 140:
            self.logger.info('moving '+ axis +' by putting ' + str(voltage))
            self.logger.debug('axis={}, voltage = {} in mV'.format(self.attocube_piezo_dict[axis], voltage.m_as('mV')))

            self.controller.dcLevel(self.attocube_piezo_dict[axis], int(voltage.m_as('mV')))

            dc = self.controller.getDcLevel(self.attocube_piezo_dict[axis]) * ur('mV')
            self.logger.info('now the DC level is ' + str(round(dc.to('V'),4)))
        else:
            raise Exception('The required voltage is between 0V - 140V')


    def finalize(self):
        """ This is to close connection to the device
        """
        self.logger.info('Closing connection to device.')
        self.controller.finalize()


if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350'}) as q:
        q.initialize()

        axis = 'XPiezoStepper'       #x of stepper, should be in yml file for experiment and gui
        ampl = 40*ur('V')   #30V
        freq = 1000*ur('Hz')    #Hz

        q.initialize_available_motors()

        q.list_devices()

        q.configurate_stepper(axis,ampl,freq)

        q.move_to(axis,2*ur('mm'))

        q.move_relative(axis, -2 * ur('um'))

        direct = 0  #forward
        steps = 10  #amount of steps

        q.given_step(axis,direct,steps)

        axis = 'XPiezoScanner'  #x of scanner, should be in yml file for experiment and gui

        q.configurate_scanner(axis)

        volts = 100*ur('V')
        q.move_scanner(axis,volts)
