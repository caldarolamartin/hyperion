"""
==========================
ANC350 Attocube Instrument
==========================

This is the instrument level of the position ANC350 from Attocube (in the Montana)

"""
from hyperion import logging
import yaml           #for the configuration file
import os             #for playing with files in operation system
import time
import numpy as np
from hyperion import root_dir
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur

class Anc350Instrument(BaseInstrument):
    """
    Anc 350 instrument class.
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

        if 'temperature' in settings:
            self.temperature = settings['temperature']
        else:
            self.temperature = 300

        self.stop = False

        self.logger.info('Welcome to the instrument of the Attocube')

        self.current_positions = {'XPiezoStepper': 'unavailable', 'YPiezoStepper': 'unavailable', 'ZPiezoStepper': 'unavailable',
                                  'XPiezoScanner': 'unavailable','YPiezoScanner':'unavailable','ZPiezoScanner': 'unavailable'}
        self.initialize()

    def initialize(self):
        """ | Starts the connection to the device by initializing the controller.
        | Loads the axis names from the yml file.
        | Runs set_temperature_limits.
        """
        self.logger.debug('Opening connection to anc350 and loading the axis names yml file.')
        self.controller.initialize()

        filename = os.path.join(root_dir, 'instrument', 'position', 'attocube_config.yml')

        with open(filename, 'r') as f:
            self.attocube_piezo_dict = yaml.load(f, Loader=yaml.FullLoader)

        self.set_temperature_limits()

    def set_temperature_limits(self):
        """The maximum voltage to put on the piezo scanners depends on the temperature in the cryostat. The user has to give that.
        """
        self.logger.debug('The given cryostat temperature is {}K'.format(self.temperature))
        if self.temperature > 4.0:
            self.max_dC_level = 60 * ur('V')
        else:
            self.max_dC_level = 140 *ur('V')

        self.logger.debug('Maximum voltage on scanner piezo: {}'.format(self.max_dC_level))
        self.max_dC_level_300K = 60 *ur('V')

    def get_position(self, axis):
        """ Asks the position from the controller level. This method is useful in higher levels where you want to display the position.

        :param axis: stepper axis, XPiezoStepper, YPiezoStepper, or XPiezoScanner, etc.
        :type axis: string
        """
        ax = self.attocube_piezo_dict[axis]['axis']  # otherwise you keep typing this
        if 'Stepper' in axis:
            self.current_positions[axis] = round(self.controller.getPosition(ax) * ur('nm').to('mm'), 6)
        elif 'Scanner' in axis:
            self.current_positions[axis] = round(self.controller.getDcLevel(ax) * ur('mV'),6)

    def update_all_positions(self):
        """Uses self.get_position to ask the position on all axes. This method is useful in higher levels where you want to display the position.
        """
        for axis in self.attocube_piezo_dict:
            self.get_position(axis)

    def configure_stepper(self, axis, amplitude, frequency):
        """ - Does the necessary configuration of the Stepper:
        - for closed loop positioning the Amplitude Control needs to be set in Step Width mode, nr. 2
        - loads the actor file, files are in controller folder, their names hardcoded in controller init
        - sets the amplitude and frequency
        - the amplitude influences the step width, the frequency influences the speed
        - also stores the current position of the axis in self.current_positions

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param amplitude: amplitude voltage; at room temperature you need 30V-40V, at low temperatures 40V-50V, max 60V; high amplitude is large stepwidth
        :type axis: pint quantity

        :param frequency: frequency to be set; higher means more noise but faster; between 1Hz and 2kHz
        :type axis: pint quantity
        """
        ax = self.attocube_piezo_dict[axis]['axis']  # otherwise you keep typing this

        self.logger.debug('Loading Stepper actor file, putting amplitude and frequency')

        # filename = 'q_test_long_name'
        # path = os.path.join(root_dir, 'controller', 'attocube')
        self.controller.load(ax)

        self.get_position(axis)

        self.controller.amplitudeControl(ax,2)
        self.logger.debug('Stepper Amplitude Control put in StepWidth mode')

        if 0 <= amplitude.m_as('mV') <= self.controller.max_amplitude_mV:
            self.logger.debug('checking if the amplitude is okay')

            self.controller.amplitude(ax, int(amplitude.m_as('mV')))  # put the amplitude on the controller, it needs to be an int

            self.Amplitude[ax] = amplitude.m_as('V')   #remember that amplitude in V

            ampl = self.controller.getAmplitude(ax) * ur('mV')
            self.logger.debug('amplitude is now ' + str(ampl.to('V')))

            step = self.controller.getStepwidth(ax)
            #huh, 0 makes no sense!!!!
            self.Stepwidth[ax] = step                   #remember the associated step width

            self.logger.debug('so the step width is ' + str(step * ur('nm')))
        else:
            self.logger.warning('The required amplitude needs to be between 0V and 60V')
            return

        if 1 <= frequency.m_as('Hz') <= self.controller.max_frequency_Hz:
            self.logger.debug('checking if the frequency is okay')

            self.controller.frequency(ax, frequency.m_as('Hz'))     #put the frequency on the controller; this needs to be an int (not float)
            self.Frequency[ax] = frequency.m_as('Hz')           #remember that frequency

            speed = self.controller.getSpeed(ax) *ur('nm/s')               #remember the associated speed
            self.Speed[ax] = speed.m_as('nm/s')

            self.logger.debug('frequency is ' + str(self.controller.getFrequency(ax) * ur('Hz')))
            self.logger.debug('so the speed is ' + str(round(speed.to('mm/s'),4)))
        else:
            self.logger.warning('The required frequency needs to be between 1Hz and 2kHz')
            return

    def capacitance(self,axis):
        """Measures the capacitance of the stepper or scanner; no idea why you would want to do that.

        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner, XPiezoStepper, etc.
        :type axis: string
        """
        capacitance = self.controller.capMeasure(self.attocube_piezo_dict[axis]['axis']) * ur('mF')
        capacitance = round(capacitance.to('F'), 3)
        self.logger.debug(axis + ': ' + str(capacitance))

    def configure_scanner(self, axis):
        """- Does the necessary configuration of the Scanner:
        - you need to set the mode to INT, not DC-IN

        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner or ZPiezoScanner
        :type axis: string

        """
        self.logger.debug('Putting Scanner setting in INT mode')

        self.controller.intEnable(self.attocube_piezo_dict[axis]['axis'],True)
        self.logger.debug('is the scanner on INT mode? ' + str(self.controller.getIntEnable(self.attocube_piezo_dict[axis]['axis'])))

    def check_if_moving(self,axis,position):
        """| **work in progress!**
        | Checks whether the piezo is actually moving.
        | It checks if you are not out of range, or putting a too low voltage.
        | If that's okay, it keeps checking whether you are actually moving.
        | However, the status of the piezo is not always correct, and the movement is not linear, so this method is not finished yet.
        | It also keeps checking whether self.stop is True, and asking the position. This can be used in higher levels with threads and timers.

        :param axis: scanner axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
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
        self.get_position(axis)
        self.logger.debug(axis + 'starts at position ' + str(round(current_pos.to('mm'),6)))
        ismoved = False

        self.logger.debug('0 < current_pos < 5mm? {}'.format(position < 0.0*ur('mm') or position > 5.0*ur('mm')))

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
        elif self.Amplitude[ax] < 1.0:    #if you forgot, it might be 0 V
            self.stop_moving(axis)      #you have to do this, otherwise it keeps trying forever
            end = current_pos
            self.logger.warning('Maybe you should configurate this Stepper axis and set a voltage')
            return (end, ismoved)
        else:
            time.sleep(0.5)  # important not to put too short, otherwise it already starts asking before the guy even knows whether he moves
            while self.controller.getStatus(ax)['moving']:
                #self.logger.debug('controller moving? '+str(self.controller.getStatus(ax)['moving']))
                self.get_position(axis)
                self.logger.debug('{}'.format(self.current_positions[axis]))
                time.sleep(0.1)
                if self.stop:
                    self.logger.info('Stopping approaching')
                    self.stop = False
                    break
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

                # for ii in range(5):
                #     new_pos = self.controller.getPosition(ax)*ur('nm')
                #     self.logger.info(axis + 'moving, currently at ' + str(round(new_pos.to('mm'),6)))
                #     Position[ii]=new_pos.m_as('nm')
                #     self.logger.debug(Position)
                #     time.sleep(0.5)  # important not to put too short, otherwise it doesnt move in between comparing
                #
                # current_pos = self.controller.getPosition(ax)*ur('nm')
                # average = np.mean(Position)
                # standard = np.std(Position)
                #
                # self.logger.debug('current pos - average moved pos'+str(np.abs(current_pos.m_as('nm')-average)))
                # self.logger.debug('standard deviation'+str(standard))
                #
                # if np.abs(current_pos.m_as('nm')-average) < standard/1.5:
                #     self.logger.warning('Stepper is not moving, check voltage and range')
                #     end = new_pos
                #     return (end, ismoved)
                # else:
                #     Position = np.zeros(5)

            ismoved = True
            end = self.controller.getPosition(ax)*ur('nm')
            self.logger.debug('type of end is ' + str(type(end)))
            return (end, ismoved)

    def move_to(self,axis,position):
        """| Moves to an absolute position with the Stepper and tells when it arrived.
        | **Pay attention: does not indicate if you take a position outside of the boundary, but you will keep hearing the noise of the piezo.**

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
            self.logger.debug('difference is ' + str(round(position.to('nm') - end.to('nm'), 6)))

    def move_relative(self, axis, step):
        """| Moves the Stepper by an amount to be given by the user.
        | **Pay attention: does not indicate if you take a position outside of the boundary, but you will keep hearing the noise of the piezo.**

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param step: amount to move, can be both positive and negative; needs to be an integer, no float!
        :type step: pint quantity
        """
        begin = self.controller.getPosition(self.attocube_piezo_dict[axis]['axis'])*ur('nm')

        self.logger.info('moving to a relative position, ' + str(step))
        self.controller.moveRelative(self.attocube_piezo_dict[axis]['axis'],int(step.m_as('nm')))

        [end,ismoved] = self.check_if_moving(axis, step + begin)

        if ismoved:
            self.logger.info('axis arrived at ' + str(round(end.to('mm'), 6)))
            self.logger.debug('has moved ' + str(round(begin - end, 6)))

    def given_step(self,axis,direction,amount):
        """| Moves by a number of steps that theoretically should be determined by the set amplitude and frequency; in practice it's different.
        | *You have to give it a lot of time, things break if you ask too much whether it is finished yet.*

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param direction: direction to move: forward = 0, backward = 1
        :type direction: integer

        :param amount: amount of steps that you want to take
        :type amount: integer
        """
        Steps = []
        self.logger.info('moving ' + axis + ' by ' + str(amount) + ' steps of stepwidth '+ str(self.Stepwidth[self.attocube_piezo_dict[axis]['axis']]))

        if amount == 1:
            self.logger.debug('You are making 1 step')
            self.controller.moveSingleStep(self.attocube_piezo_dict[axis]['axis'], direction)
            self.get_position(axis)
        else:
            for ii in range(amount):
                self.controller.moveSingleStep(self.attocube_piezo_dict[axis]['axis'],direction)
                time.sleep(0.5)
                position = self.controller.getPosition(self.attocube_piezo_dict[axis]['axis'])*ur('nm')
                self.logger.debug('step ' + str(ii) + ': we are now at ' + str(round(position.to('mm'),6)))
                Steps.append(position.m_as('nm'))
                self.get_position(axis)

            Steps = np.asarray(Steps)
            Stepsize = np.diff(Steps)
            av_steps = np.mean(Stepsize)
            self.logger.debug('average step size is ' + str(round(av_steps)*ur('nm')))

    def move_continuous(self, axis, direction):
        """Keeps moving the stepper axis until you manage to stop it (for which you need threading).

        :param axis: stepper axis to be set, XPiezoStepper, YPiezoStepper or ZPiezoStepper
        :type axis: string

        :param direction: direction to move: forward = 0, backward = 1
        :type direction: integer
        """
        ax = self.attocube_piezo_dict[axis]['axis']

        while not self.stop:
            self.get_position(axis)
            self.controller.moveContinuous(self.attocube_piezo_dict[axis]['axis'], direction)

            #time.sleep(0.1)
        if self.stop:
            self.logger.info('Stopping approaching')
            self.stop_moving(axis)
            self.stop = False

    def move_scanner(self, axis, voltage):
        """ | Moves the Scanner by applying a certain voltage.
        | **Pay attention: the maximum voltage depends on the temperature in the cryostat.**
        | *There is no calibration, so you don't know how far; but the range is specified for 50um with a voltage of 0-140V.*

        :param axis: scanner axis to be set, XPiezoScanner, YPiezoScanner or ZPiezoScanner
        :type axis: string

        :param voltage: voltage to move the scanner; from 0-140V
        :type voltage: pint quantity
        """
        if 0 <= voltage.m_as('mV') <= self.max_dC_level.m_as('mV'):
            if voltage.m_as('mV') > self.max_dC_level_300K.m_as('mV'):
                self.logger.warning('Dont put voltages higher than 60V, unless you are at low temperatures!')

            self.logger.info('moving {} by putting {}'.format(axis, voltage))
            self.logger.debug('axis={}, voltage = {} in mV'.format(self.attocube_piezo_dict[axis]['axis'], voltage.m_as('mV')))

            self.controller.dcLevel(self.attocube_piezo_dict[axis]['axis'], int(voltage.m_as('mV')))

            #time.sleep(0.5)

            # dc = self.controller.getDcLevel(self.attocube_piezo_dict[axis]['axis']) * ur('mV')
            #
            # while abs(dc.m_as('mV')-voltage.m_as('mV')) > 1:
            #     t0 = time.time()
            #     notreached = True
            #     while time.time() - t0 < 3:
            #         dc = self.controller.getDcLevel(self.attocube_piezo_dict[axis]['axis']) * ur('mV')
            #         if abs(dc.m_as('mV') - voltage.m_as('mV')) <= 1:
            #             notreached = False
            #             break
            #         time.sleep(0.1)
            #     #self.logger.debug('DC level' + str(round(dc.to('V'), 4)))
            #
            # if notreached:
            #     self.logger.warning('time out for piezo movement')

            self.get_position(axis)
            dc = self.controller.getDcLevel(self.attocube_piezo_dict[axis]['axis']) * ur('mV')
            self.logger.debug('now the DC level is ' + str(round(dc.to('V'),4)))
        else:
            self.logger.warning('Not moving, exceeding maximum piezo voltage.')
            return

    def zero_scanners(self):
        """Puts 0V on all three Piezo Scanners.
        """
        self.logger.debug('Putting 0V on every Scanner Piezo.')
        self.move_scanner('XPiezoScanner',0*ur('V'))
        self.move_scanner('YPiezoScanner', 0 * ur('V'))
        self.move_scanner('ZPiezoScanner', 0 * ur('V'))

    def stop_moving(self, axis):
        """Stops moving to target/relative/reference position.

        :param axis: scanner or stepper axis to be set, XPiezoStepper, XPiezoScanner, YPiezoScanner etc
        :type axis: string
        """
        self.logger.info('Stop moving')
        self.controller.stopApproach(self.attocube_piezo_dict[axis]['axis'])

    def finalize(self):
        """ This is to close connection to the device.
        """
        self.logger.info('Closing connection to device.')
        self.controller.finalize()


if __name__ == "__main__":

#    with Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350'}) as q:

    q = Anc350Instrument(settings={'dummy':False,'controller': 'hyperion.controller.attocube.anc350/Anc350','temperature': 300})
    axis = 'XPiezoStepper'       #x of stepper, should be in yml file for experiment and gui
    ampl = 30*ur('V')   #30V
    freq = 100*ur('Hz')    #Hz

    q.configure_stepper(axis, ampl, freq)

    #q.move_to(axis,2.1*ur('mm'))

    # q.move_continuous(axis,1)
    # for ii in range(10):
    #     time.sleep(0.1)
    #     print(q.controller.getPosition(q.attocube_piezo_dict[axis]['axis'])*ur('nm'))
    # q.stop_moving(axis)

    #q.move_relative(axis, 100 * ur('um'))

    # direct = 0  #forward
    # steps = 1  #amount of steps
    #
    # q.given_step(axis,direct,steps)
    #
    axis = 'XPiezoScanner'  #x of scanner, should be in yml file for experiment and gui

    q.configure_scanner(axis)

    volts = 40*ur('V')
    q.move_scanner(axis,volts)

    q.finalize()
