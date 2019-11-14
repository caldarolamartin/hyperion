"""
====================================
Thorlabs thorlabs_motor Instrument
====================================

Connects to the tdc001_cube controller, which is just a wrapper for the core underneath that we installed.
You can find the core here https://github.com/qpit/thorlabs_apt/tree/master/thorlabs_apt,
or installed in C:/Users/NAME/AppData/Local/Continuum/anaconda3/envs/hyperion/Lib/site-packages/thorlabs_apt.

I implemented and documented those functions that I am actually going to use. If you want to use others, they might exist in the core.
"""

import logging
from hyperion.instrument.base_instrument import BaseInstrument

from hyperion import ur
import time


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

        self.aptmotorlist = []
        self._name = settings['name']
        self.kind_of_device = 'stage'


    def initialize(self):
        """| Asks some useful information to the T-cube.
        | Blinks the light to identify the T-cube.
        | Runs get_axis_info, which will figure out whether you are connected to a waveplate or stage motor.
        """
        self.logger.debug('serial number of {}: {}'.format(self._name, self.controller.serial_number))

        self.logger.debug('hardware info: {}'.format(self.controller.hardware_info))
        self.controller.identify

        self.get_axis_info()

    def finalize(self):
        """ This would have been to close connection to the device, but that method does not exist in the core controller.
        """
        self.logger.info('Should close connection to T-cube: {}'.format(self._name))


    def get_axis_info(self):
        """ | **Important** returns axis information of stage.
        | If units = 1, the units are in mm and the device is a stage motor.
        | If units = 2, the units are in degrees and the device is a motorized waveplate.
        | Store this in self.kind_of_device.

        :return: (minimum position, maximum position, stage units, pitch)
        :rtype: tuple
        """
        (min_pos, max_pos, units, pitch) = self.controller.get_stage_axis_info()
        if units == 2:
            self.kind_of_device = 'waveplate'
            self.logger.info('the T-cube is connected to a {}'.format(self.kind_of_device))
        elif units == 1:
            self.kind_of_device = 'stage'
            self.logger.info('the T-cube is connected to a motor {}'.format(self.kind_of_device))
        else:
            self.logger.info('connected kind of thorlabs device is unclear, max range: {}'.format(max_pos))
        return (min_pos, max_pos, units, pitch)

    def position(self):
        """| Asks the position to the controller. Both returns it and stores it in self.pos.
        | Units depend on the kind of device; either mm or degrees.

        :return: position in mm or degrees
        :rtype: pint quantity
        """
        pos = self.controller.position
        if self.kind_of_device == 'waveplate':
            pos = pos*ur('degrees')
        elif self.kind_of_device == 'stage':
            pos = pos*ur('mm')

        self.logger.info('Current position of {} is {}'.format(self._name, pos))
        return pos

    def is_in_motion(self):
        """Returns whether thorlabs motor is in motion, and prints a warning.

        :return: in motion
        :rtype: bool
        """
        in_motion = self.controller.is_in_motion
        if in_motion:
            self.logger.warning('You are still moving {}'.format(self._name))
        return in_motion

    def motor_current_limit_reached(self):
        """
        Return whether current limit of thorlabs_motor has been reached, and prints a warning.

        :return: current limit reached
        :rtype: bool
        """
        limit_reached = self.controller.motor_current_limit_reached
        if limit_reached:
            self.logger.warning('You reached the motor limits of {}'.format(self._name))
        return limit_reached

    def motion_error(self):
        """
        Returns whether there is a motion error (= excessing position error), and prints a warning.

        :return: motion error
        :rtype: bool
        """
        motion_error = self.controller.motion_error
        if motion_error:
            self.logger.warning('You have a motion error of {}'.format(self._name))
        return motion_error

    def move_home(self, blocking):
        """| Move to home position.
        | If blocking is True, it will move until its done.
        | If blocking is False, it might not reach its destination if you dont give it time.

        :param blocking: wait until homed
        :type blocking: bool
        """
        self.logger.info('Trying to move {} home.'.format(self._name))
        self.controller.move_home(blocking)
        if not self.is_in_motion():
            self.logger.debug('Destination of {} is reached: {}'.format(self._name, self.position()))

    def check_move(self, value):
        """| Checks whether the units actually agree with the kind of device, so degrees for a waveplate or mm or so for a stage motor.
        | Returns whether you can move, otherwise prints warnings.
        | Return the value without units, removing either the degrees or the mm.
        | The controller thinks in degrees and mm.

        :param value: distance or new position that you would want to move
        :type value: pint quantity

        :return: you_can_move, value
        :rtype: Bool, float
        """
        you_can_move = False
        unit = 'mm'

        self.logger.debug(self.kind_of_device)

        if not self.motor_current_limit_reached():
            if self.kind_of_device == 'waveplate':
                if value.check('[length]'):
                    self.logger.warning('You want to move a waveplate, but gave the distance in mm')
                elif value.check('[]'):
                    you_can_move = True
                    unit = 'degree'
                else:
                    self.logger.warning('You gave the distance in weird units')
            elif self.kind_of_device == 'stage':
                if value.check('[length]'):
                    you_can_move = True
                    unit = 'mm'
                elif value.check('[]'):
                    self.logger.warning('You want to move a stage motor, but gave the distance without units')
                else:
                    self.logger.warning('You gave the distance in weird units')

        return you_can_move, unit


    def move_absolute(self, new_position, blocking):
        """| Moves the T-cube to a new position, but first checks the units by calling check_units.
        | The method check_units will already convert the pint quantity to a float correctly.
        | If blocking is True, it will move until its done.
        | If blocking is False, it might not reach its destination if you dont give it time.

        :param new_position: the new position
        :type new_position: pint quantity

        :param blocking:
        :type blocking: bool
        """
        self.logger.debug('Trying to move {} to {}'.format(self._name, new_position))
        moved = False

        (you_can_move, unit) = self.check_move(new_position)

        self.logger.debug("{} {}".format(you_can_move, new_position))

        if you_can_move:
            self.controller.move_to(new_position.m_as(unit), blocking)
            self.motion_error()
            moved = True

        if not self.is_in_motion():
            if moved:
                self.logger.debug('Destination is reached: {}'.format(self.position()))
            else:
                self.logger.debug('You did not move at all.')

    def move_relative(self, distance, blocking):
        """| Moves the T-cube with a distance relative to the current one, but first checks the units by calling check_units.
        | The method check_units will already convert the pint quantity to a float correctly.
        | If blocking is True, it will move until its done.
        | If blocking is False, it might not reach its destination if you dont give it time.

        :param value: relative distance in mm or degree
        :type value: pint quantity

        :param blocking: wait until moving is finished; default False
        :type blocking: bool
        """
        self.logger.info('Trying to move by {}'.format(distance))

        moved = False

        (you_can_move, unit) = self.check_move(distance)

        if you_can_move:
            self.motor_current_limit_reached()
            self.controller.move_by(distance.m_as(unit), blocking)
            self.motion_error()
            moved = True

        if not self.is_in_motion():
            if moved:
                self.logger.debug('Destination is reached: {}'.format(self.position()))
            else:
                self.logger.debug('You did not move at all.')

    def make_step(self, stepsize, blocking):
        """| Moves the T-cube by one step of a stepsize
        | Actually just uses move_relative
        | If blocking is True, it will move until its done.
        | If blocking is False, it might not reach its destination if you dont give it time.

        :param stepsize: stepsize in mm or degree
        :type stepsize: pint quantity

        :param blocking: wait until moving is finished; default False
        :type blocking: bool
        """
        self.logger.debug('Making one step of size {}'.format(stepsize))
        self.move_relative(stepsize,blocking)

    def stop_moving(self):
        """| Stop motor but turn down velocity slowly (profiled).
        | **Pay attention: not tested yet**
        """
        self.logger.info('Stops with moving.')
        self.controller.stop_profiled()

#-----------------------------------------------------------------------------------------------------------------------
    def list_devices(self):
        """ | Lists all available devices.
        | It actually should live outside of this class, since it talks to all Thorlabs motors attached, not a single one.
        | However, I could not make that work, so now I kept it here.
        """
        self.aptmotorlist = self.controller.core.list_available_devices()
        self.logger.info('{} thorlabs_motor boxes found: {}'.format(len(self.aptmotorlist),self.aptmotorlist))



if __name__ == "__main__":
    import hyperion

    xMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83841160, 'name': 'xMotor'}

    yMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube', 'serial': 83850123, 'name': 'yMotor'}

    WaveplateMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850090, 'name': 'Waveplate'}

    with Thorlabsmotor(settings = xMotor) as sampleX, Thorlabsmotor(settings = WaveplateMotor) as waveplate:
        sampleX.list_devices()

        sampleX.initialize()
        sampleX.position()

        sampleX.move_relative(1*ur('mm'),True)

        # sampleY.motor_current_limit_reached()
        # sampleY.initialize()
        # sampleY.position()
        #
        # sampleY.move_relative(1*ur('mm'),True)
        # sampleY.position()

        waveplate.initialize()
        waveplate.position()

        waveplate.move_absolute(30*ur('degree'),True)
        # time.sleep(1)
        # waveplate.stop_moving()
        # waveplate.position()

        waveplate.move_relative(-10*ur('degrees'),True)

        waveplate.make_step(1*ur('degrees'),True)

        waveplate.move_home(True)
