"""
====================
ANC350 Attocube Instrument
====================

This is the instrument level of the position ANC350 from Attocube (in the Montana)

"""

import logging
import yaml           #for the configuration file
import os             #for playing with files in operation system
import sys
import time
import numpy as np
from hyperion import root_dir

from hyperion.instrument.base_instrument import BaseInstrument

from hyperion import ur

class Anc350Instrument(BaseInstrument):
    """
    Anc 350 instrument class
    """
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

        self.initialize()

    def initialize(self):
        """ Starts the connection to the device
        """
        self.logger.info('Opening connection to anc350.')
        self.controller.initialize()

        filename = os.path.join(root_dir, 'instrument', 'position', 'attocube_config.yml')

        with open(filename, 'r') as f:
            info = yaml.load(f, Loader=yaml.FullLoader)

        # for module in info:
        #     if 'Piezo' in module:
        #         self.attocube_piezo_dict[module] = info[module]['axis']
        #         print(self.attocube_piezo_dict)


        with open(filename, 'r') as f:
            self.attocube_piezo_dict = yaml.load(f, Loader=yaml.FullLoader)

        self.logger.info('Started the connection to the device and loaded the axis names yml file')

    def configurate_stepper(self, axis, amplitude, frequency):
        """ - Does the necessary configuration of the Stepper:
        - for closed loop positioning the Amplitude Control needs to be set in Step Width mode, nr. 2
        - loads the actor file, files are in controller folder, their names hardcoded in controller init
        - sets the amplitude and frequency
        - the amplitude influences the step width, the frequency influences the speed

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param amplitude: amplitude voltage; at room temperature you need 30V-40V, at low temperatures 40V-50V, max 60V; high amplitude is large stepwidth
        :type axis: pint quantity

        :param frequency: frequency to be set; higher means more noise but faster; between 1Hz and 2kHz
        :type axis: pint quantity
        """
        ax = self.attocube_piezo_dict[axis]['axis']  # otherwise you keep typing this

        self.logger.info('Loading Stepper actor file, putting amplitude and frequency')

        # filename = 'q_test_long_name'
        # path = os.path.join(root_dir, 'controller', 'attocube')
        self.controller.load(ax)

        self.controller.amplitudeControl(ax,2)
        self.logger.debug('Stepper Amplitude Control put in StepWidth mode')

        print(type(amplitude.m_as('V')))

        if 0 <= amplitude.m_as('mV') <= self.controller.max_amplitude_mV:
            self.logger.debug('checking if the amplitude is okay')

            self.controller.amplitude(ax, int(amplitude.m_as('mV')))  # put the amplitude on the controller, it needs to be an int

            self.Amplitude[ax] = amplitude.m_as('V')   #remember that amplitude in V

            step = self.controller.getStepwidth(ax)
            #huh, 0 makes no sense!!!!
            self.Stepwidth[ax] = step                   #remember the associated step width

            ampl = self.controller.getAmplitude(ax) * ur('mV')
            self.logger.info('amplitude is now ' + str(ampl.to('V')))
            self.logger.info('so the step width is ' + str(step * ur('nm')))
        else:
            self.logger.warning('The required amplitude needs to be between 0V and 60V')
            return

        if 1 <= frequency.m_as('Hz') <= self.controller.max_frequency_Hz:
            self.logger.debug('checking if the frequency is okay')
            self.logger.debug(str(frequency))

            self.controller.frequency(ax, frequency.m_as('Hz'))     #put the frequency on the controller; this needs to be an int (not float)
            self.Frequency[ax] = frequency.m_as('Hz')           #remember that frequency

            speed = self.controller.getSpeed(ax) *ur('nm/s')               #remember the associated speed
            self.Speed[ax] = speed.m_as('nm/s')

            self.logger.info('frequency is ' + str(self.controller.getFrequency(ax) * ur('Hz')))
            self.logger.info('so the speed is ' + str(round(speed.to('mm/s'),4)))
        else:
            self.logger.warning('The required frequency needs to be between 1Hz and 2kHz')
            return

    def capacitance(self,axis):
        """Measures the capacitance of the stepper or scanner; no idea why you would want to do that

        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner, XPiezoStepper, etc.
        :type axis: string
        """
        capacitance = self.controller.capMeasure(self.attocube_piezo_dict[axis]['axis']) * ur('mF')
        capacitance = round(capacitance.to('F'), 3)
        self.logger.info(axis + ': ' + str(capacitance))

    def configurate_scanner(self,axis):
        """- Does the necessary configuration of the Scanner:
        - you need to set the mode to INT, not DC-IN

        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner or ZPiezoScanner
        :type axis: string

        """
        self.logger.info('Putting Scanner setting in INT mode')

        self.controller.intEnable(self.attocube_piezo_dict[axis]['axis'],True)
        self.logger.debug('is the scanner on INT mode? ' + str(self.controller.getIntEnable(self.attocube_piezo_dict[axis]['axis'])))

    def check_if_moving(self,axis,position):
        """
        | Checks whether the piezo is actually moving
        | It checks if you are not out of range, or putting a too low voltage
        | if that's okay, it keeps checking whether you are actually moving
        | If the average moving is below the threshold of 1 um, this method will raise an exception

        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner or ZPiezoScanner
        :type axis: string

        :param position: absolute position that you want to go to; needs to be an integer, no float!
        :type axis: pint quantity

        :return: The end position, so the moving method can compare that with the start position
        """
        Position = np.zeros(5)
        ax = self.attocube_piezo_dict[axis]['axis']     #otherwise you keep typing this
        start_range = ur(self.attocube_piezo_dict[axis]['start_range'])
        end_range = ur(self.attocube_piezo_dict[axis]['end_range'])

        # check what's happening
        current_pos = self.controller.getPosition(ax)*ur('nm')
        self.logger.info(axis + 'starts at position ' + str(round(current_pos.to('mm'),6)))
        ismoved = False

        self.logger.debug('0 < current_pos > 5mm? ' + str(position < 0.0*ur('mm') or position > 5.0*ur('mm')))

        # pay attention: position is what you gave to this method, the position where you want to move to
        # current_pos is what you asked the positioner is at now
        # new_pos is the position to compare the old position with, to check whether you are actually moving at all

        self.logger.debug('start of range: '+str(ur(self.attocube_piezo_dict[axis]['start_range']).m_as('mm')))
        self.logger.debug('stop of range: ' + str(ur(self.attocube_piezo_dict[axis]['end_range'])))

        if position.m_as('mm') < start_range.m_as('mm') or position.m_as('mm') > end_range.m_as('mm'):
            self.logger.warning('Trying to move out of range')
            self.stop_moving(axis)      #you have to do this, otherwise it keeps trying forever
            end = current_pos
            return (end, ismoved)
        elif self.Amplitude[ax] < 1.0*ur('V'):    #if you forgot, it might be 0 V
            self.stop_moving(axis)      #you have to do this, otherwise it keeps trying forever
            end = current_pos
            self.logger.warning('Maybe you should configurate this Stepper axis and set a voltage')
            return (end, ismoved)
        else:
            # time.sleep(0.5)
            # while self.controller.getStatus(ax)['moving']:
            #     self.logger.debug('status of controller: ' + str(self.controller.getStatus(ax)['moving']))
            #
            #     sleeptime = 1.0
            #     time.sleep(sleeptime)
            #     new_pos = self.controller.getPosition(ax)*ur('nm')
            #     self.logger.info(axis + 'moving, currently at ' + str(round(new_pos.to('mm'), 6)))
            #
            #     self.logger.debug(self.Speed[ax]*sleeptime*ur('nm'))
            #
            #
            #
            #     current_pos = new_pos
            # ismoved = True
            # end = current_pos
            # return (end, ismoved)
            # time.sleep(0.5)  # important not to put too short, otherwise it already starts asking before the guy even knows whether he moves
            # while self.controller.getStatus(ax)['moving']:
            #     self.logger.debug('status of controller: '+str(self.controller.getStatus(ax)['moving']))
            #     time.sleep(1.0)     #important not to put too short, otherwise it doesnt move in between comparing
            #     new_pos = self.controller.getPosition(ax)*ur('nm')
            #     self.logger.info(axis + 'moving, currently at ' + str(round(new_pos.to('mm'),6)))
            #
            #     if np.abs(new_pos - current_pos) < 200*ur('nm'):
            #         self.logger.debug('new position - old: '+ str(np.abs(new_pos - current_pos)))
            #         self.logger.warning('Stepper is not moving, check voltage')
            #         end = new_pos
            #         return (end, ismoved)
            #     current_pos = new_pos
            #
            # ismoved = True
            # end = current_pos
            # self.logger.debug('type of end is ' + str(type(end)))
            # return (end, ismoved)
            time.sleep(0.5)  # important not to put too short, otherwise it already starts asking before the guy even knows whether he moves
            while self.controller.getStatus(ax)['moving']:
                self.logger.debug('status of controller: '+str(self.controller.getStatus(ax)['moving']))

                for ii in range(5):
                    new_pos = self.controller.getPosition(ax)*ur('nm')
                    self.logger.info(axis + 'moving, currently at ' + str(round(new_pos.to('mm'),6)))
                    Position[ii]=new_pos.m_as('nm')
                    self.logger.debug(Position)
                    time.sleep(0.5)  # important not to put too short, otherwise it doesnt move in between comparing

                current_pos = self.controller.getPosition(ax)*ur('nm')
                average = np.mean(Position)
                standard = np.std(Position)

                self.logger.debug('current pos - average moved pos'+str(np.abs(current_pos.m_as('nm')-average)))
                self.logger.debug('standard deviation'+str(standard))

                if np.abs(current_pos.m_as('nm')-average) < standard/1.5:
                    self.logger.warning('Stepper is not moving, check voltage and range')
                    end = new_pos
                    return (end, ismoved)
                else:
                    Position = np.zeros(5)

            ismoved = True
            end = current_pos
            self.logger.debug('type of end is ' + str(type(end)))
            return (end, ismoved)


    def move_to(self,axis,position):
        """| Moves to an absolute position with the Stepper and tells when it arrived
        | **Pay attention: does not indicate if you take a position outside of the boundary, but you will keep hearing the noise of the piezo**

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param position: absolute position that you want to go to; needs to be an integer, no float!
        :type axis: pint quantity

        """
        self.logger.info('Moving ' + axis +' to position: '+ str(position))
        self.controller.moveAbsolute(self.attocube_piezo_dict[axis]['axis'], int(position.m_as('nm')))

        [end,ismoved] = self.check_if_moving(axis,position)

        if ismoved:
            self.logger.info('axis arrived at ' + str(round(end.to('mm'), 6)))
            self.logger.info('difference is ' + str(round(position.to('nm') - end.to('nm'), 6)))


    def move_relative(self, axis, step):
        """| Moves the Stepper by an amount to be given by the user
        | **Pay attention: does not indicate if you take a position outside of the boundary, but you will keep hearing the noise of the piezo**

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param step: amount to move, can be both positive and negative; needs to be an integer, no float!
        :type step: pint quantity
        """
        begin = self.controller.getPosition(self.attocube_piezo_dict[axis]['axis'])*ur('nm')

        self.logger.info('moving to a relative position, ' + str(step))
        self.controller.moveRelative(self.attocube_piezo_dict[axis]['axis'],int(step.m_as('nm')))

        #[end,ismoved] = self.check_if_moving(axis, step + begin)

        # if ismoved:
        #     self.logger.info('axis arrived at ' + str(round(end.to('mm'), 6)))
        #     self.logger.info('has moved ' + str(round(begin - end, 6)))

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
        self.logger.info('moving ' + axis + ' by ' + str(amount) + ' steps of stepwidth '+ str(self.Stepwidth[self.attocube_piezo_dict[axis]['axis']]))

        for ii in range(amount):
            self.controller.moveSingleStep(self.attocube_piezo_dict[axis]['axis'],direction)
            time.sleep(0.5)
            position = self.controller.getPosition(self.attocube_piezo_dict[axis]['axis'])*ur('nm')
            self.logger.info('step ' + str(ii) + ': we are now at ' + str(round(position.to('mm'),6)))
            Steps.append(position.m_as('nm'))

        Steps = np.asarray(Steps)
        Stepsize = np.diff(Steps)
        av_steps = np.mean(Stepsize)
        self.logger.info('average step size is ' + str(round(av_steps)*ur('nm')))

    def move_continuous(self, axis, direction):
        pass



    def move_scanner(self, axis, voltage):
        """ | Moves the Scanner by applying a certain voltage
        | *There is no calibration, so you don't know how far; but the range is specified for 50um with a voltage of 0-140V*
        | Pay attention: if you put this one to 0V, it sort of turns itself off; and it takes a lot of time to get it running again, if you make a large step (10V or so)

        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner or ZPiezoScanner
        :type axis: string

        :param voltage: voltage to move the scanner; from 0-140V
        :type voltage: pint quantity
        """

        if 0 <= voltage.m_as('mV') <= self.controller.max_dclevel_mV:
            self.logger.info('moving '+ axis +' by putting ' + str(voltage))
            self.logger.debug('axis={}, voltage = {} in mV'.format(self.attocube_piezo_dict[axis]['axis'], voltage.m_as('mV')))

            self.controller.dcLevel(self.attocube_piezo_dict[axis]['axis'], int(voltage.m_as('mV')))

            # dc = self.controller.getDcLevel(self.attocube_piezo_dict[axis]['axis']) * ur('mV')

            # while abs(dc.m_as('mV')-voltage.m_as('mV')) > 1:
            t0 = time.time()
            notreached = True
            while time.time() - t0 < 3:
                dc = self.controller.getDcLevel(self.attocube_piezo_dict[axis]['axis']) * ur('mV')
                if abs(dc.m_as('mV') - voltage.m_as('mV')) <= 1:
                    notreached = False
                    break
                time.sleep(0.1)
                #self.logger.debug('DC level' + str(round(dc.to('V'), 4)))

            if notreached:
                self.logger.warning('time out for piezo movement')

            self.logger.info('now the DC level is ' + str(round(dc.to('V'),4)))
        else:
            self.logger.warning('The required voltage is between 0V - 140V')
            return

    def stop_moving(self, axis):
        """Stops moving to target/relative/reference position

        :param axis: scanner or stepper axis to be set, XPiezoStepper, XPiezoScanner, YPiezoScanner etc
        :type axis: string
        """
        self.controller.stopApproach(self.attocube_piezo_dict[axis]['axis'])

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
        axis = 'XPiezoStepper'       #x of stepper, should be in yml file for experiment and gui
        ampl = 60*ur('V')   #30V
        freq = 1000*ur('Hz')    #Hz

        q.configurate_stepper(axis,ampl,freq)

        #q.move_to(axis,5.1*ur('mm'))

        q.move_relative(axis, 100 * ur('um'))

        # direct = 0  #forward
        # steps = 10  #amount of steps
        #
        # q.given_step(axis,direct,steps)
        #
        axis = 'XPiezoScanner'  #x of scanner, should be in yml file for experiment and gui

        q.configurate_scanner(axis)

        volts = 140*ur('V')
        q.move_scanner(axis,volts)

