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

        self.settings = settings
        self.aptmotorlist = []
        self._name = self.settings['name']
        self.kind_of_device = 'stage'

        self.initialize()
        self.current_position = []
        self.stop = False


    def initialize(self):
        """ - Initializes the cube:
        - checks whether the serial number is recognized by the cube
        - runs list_device to check whether this serial number actually exists in all connected T-cubes
        - asks the harware info just in case
        - blinks the light to identify the T-cube
        - runs set_axis_info, which will set the minimum position to -12 and
        - run get_axis_info, which will figure out whether you are connected to a waveplate or stage motor **always run this one!!**
        """
        self.logger.info('Initializing your {} and checking some basic things.'.format(self._name))

        self.logger.debug('serial number of {}: {}'.format(self._name, self.controller.serial_number))

        if self.list_devices():
            if self.controller.serial_number is not self.settings['serial']:
                self.logger.warning('Something is seriously wrong with serial numbers!')
            else:
                self.logger.debug('hardware info: {}'.format(self.controller.hardware_info))
                self.controller.identify
                #self.get_axis_info()
                self.set_axis_info()
                self.current_position = self.position()
        else:
            self.logger.error('Your serial number does not exist in this whole thorlabs device.')

    def finalize(self):
        """ This would have been to close connection to the device, but that method does not exist in the core controller.
        """
        self.logger.info('Should close connection to cube: {}'.format(self._name))


    def get_axis_info(self):
        """ | **Important** returns axis information of stage.
        | If units = 1, the units are in mm and the device is a stage motor.
        | If units = 2, the units are in degrees and the device is a motorized waveplate.
        | Store this in self.kind_of_device, so the rest of this class knows.

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

    def set_axis_info(self):
        """| Executes get_axis_info to set the kind of device, and changes the minimum position to -12.0.
        | This is important because the stage axis puts itself at 0 if you shut down the cubes,
        | so it happens that afterwards you want to go to a negative position.
        | To prevent errors, this method changes the minimum position from 0 to -12.0.
        """
        current_axis_info = self.get_axis_info()
        new_minimum_position = -12.0

        self.controller.set_stage_axis_info(new_minimum_position, current_axis_info[1], current_axis_info[2], current_axis_info[3])
        self.logger.debug('Minimum position changed to -12.0 to prevent errors.')

    def position(self):
        """| Asks the position to the controller and returns that.
        | Units depend on the kind of device; either mm or degrees.
        | Remembers the current_position as declared in the init.

        :return: position in mm or degrees
        :rtype: pint quantity
        """
        pos = self.controller.position
        if self.kind_of_device == 'waveplate':
            pos = pos*ur('degrees')
        elif self.kind_of_device == 'stage':
            pos = pos*ur('mm')

        self.current_position = pos
        return pos

    def is_in_motion(self):
        """Returns whether thorlabs motor is in motion, and prints a warning if so.

        :return: in motion
        :rtype: bool
        """
        in_motion = self.controller.is_in_motion
        if in_motion:
            self.logger.debug('You are still moving {}'.format(self._name))
        return in_motion

    def motor_current_limit_reached(self):
        """
        Return whether current limit of thorlabs_motor has been reached, and prints a warning if so.

        :return: current limit reached
        :rtype: bool
        """
        limit_reached = self.controller.motor_current_limit_reached
        if limit_reached:
            self.logger.warning('You reached the motor limits of {}'.format(self._name))
        return limit_reached

    def motion_error(self):
        """
        Returns whether there is a motion error (= excessing position error), and prints a warning if so.

        :return: motion error
        :rtype: bool
        """
        motion_error = self.controller.motion_error
        if motion_error:
            self.logger.warning('You have a motion error of {}'.format(self._name))
        return motion_error

    def moving_loop(self):
        """| This method is used by the move_home, move_relative and move_absolute methods.
        | It stays in the while loop until the position is reached or self.stop is set to True,
        | meanwhile updating the current_position as known in this instrument level.
        | This means it can be used in higher levels to display the position on the gui and thread the stop function.
        | If the sleeps are making your program too slow, they could be changed.
        | Pay attention not to make the first sleep too short, otherwise it already starts asking before the guy even knows whether he moves.
        """

        time.sleep(0.2) # important not to put too short, otherwise it already starts asking before the guy even knows whether he moves

        while self.is_in_motion():
            self.position()
            self.motion_error()
            time.sleep(0.1)
            if self.stop:
                self.logger.info('Stopping the moving loop.')
                self.stop = False
                break

    def move_home(self, blocking):
        """| Moves to home position.
        | You can use the blocking method of the core, but than higher layers will not be able to stop the move or know the position.
        | So I implemented my own blocking that uses the is_in_motion method.
        | If blocking is True, it will move until its done.
        | If blocking is False, it might not reach its destination if you dont give it time.

        :param blocking: wait until homed
        :type blocking: bool
        """
        self.logger.info('Moving {} home.'.format(self._name))
        if blocking:
            self.controller.move_home(False)  # the blocking for the controller is False now
            self.moving_loop()
        else:
            self.controller.move_home(False)

        #self.controller.move_home(blocking)
        self.logger.debug('Destination of {} is reached: {}'.format(self._name, self.position()))

    def check_move(self, value):
        """| First checks whether there is no limit reached.
        | Then checks whether the units actually agree with the kind of device, so degrees for a waveplate or a length for a stage motor.
        | Returns whether you can move, otherwise prints warnings.
        | Returns the units of the value, since the controller thinks in degrees and mm.

        :param value: distance or new position that you would want to move
        :type value: pint quantity

        :return: you_can_move, value
        :rtype: Bool, float
        """
        you_can_move = False
        unit = 'mm'

        self.logger.debug(self.kind_of_device)

        if not self.motor_current_limit_reached():      #the current limit is not reached
            if self.kind_of_device == 'waveplate':
                if value.check('[length]'):
                    self.logger.warning('You want to move a waveplate, but gave the distance in mm')
                elif value.check('[]'):
                    you_can_move = True         #you move a waveplate and gave the value in degrees, so go ahead
                    unit = 'degree'
                else:
                    self.logger.warning('You gave the distance in weird units')
            elif self.kind_of_device == 'stage':
                if value.check('[length]'):
                    you_can_move = True         #you move a stage motor and give mm or another length, so go ahead
                    unit = 'mm'
                elif value.check('[]'):
                    self.logger.warning('You want to move a stage motor, but gave the distance without units')
                else:
                    self.logger.warning('You gave the distance in weird units')

        return you_can_move, unit

    def move_absolute(self, new_position, blocking):
        """| Moves the T-cube to a new position, but first checks the units by calling check_move.
        | The method check_move will give back the correct units.
        | If blocking is True, it will move until its done.
        | If blocking is False, it might not reach its destination if you dont give it time.

        :param new_position: the new position
        :type new_position: pint quantity

        :param blocking:
        :type blocking: bool
        """
        moved = False

        (you_can_move, unit) = self.check_move(new_position)
        #self.logger.debug("{} {}".format(you_can_move, new_position))

        if you_can_move:
            self.logger.debug('Moving {} to {}'.format(self._name, new_position))
            #self.controller.move_to(new_position.m_as(unit), blocking)
            if blocking:
                self.controller.move_to(new_position.m_as(unit), False)  # the blocking for the controller is False now
                self.moving_loop()
            else:
                self.controller.move_to(new_position.m_as(unit), False)
            moved = True

        if moved:
            self.logger.debug('Destination is reached: {}'.format(self.position()))
        else:
            self.logger.debug('You did not move at all.')

    def move_relative(self, distance, blocking):
        """| Moves the T-cube with a distance relative to the current one, but first checks the units by calling check_move.
        | The method check_move will give back the correct units.
        | If blocking is True, it will move until its done.
        | If blocking is False, it might not reach its destination if you dont give it time.

        :param value: relative distance in mm or degree
        :type value: pint quantity

        :param blocking: wait until moving is finished; default False
        :type blocking: bool
        """
        moved = False

        (you_can_move, unit) = self.check_move(distance)

        if you_can_move:
            self.logger.info('Moving {} by {}'.format(self._name, distance))    # the blocking for the controller is False now
            if blocking:
                self.controller.move_by(distance.m_as(unit), False)
                self.moving_loop()
            moved = True

        if moved:
            self.logger.debug('Destination is reached: {}'.format(self.position()))
        else:
            self.logger.debug('You did not move at all.')

    def move_velocity(self, direction, blocking):
        """| Moves the T-cube with a certain velocity until it gets stoped.
        | The method check_move will give back the correct units.
        | If blocking is True, it will move until its done.
        | If blocking is False, it might not reach its destination if you dont give it time.

        :param blocking: wait until moving is finished; default False
        :type blocking: bool

        :param direction: direction of movement
        :type direction: 1 for forward 2 for backward
        """


        direction_string = "unknown"
        if direction == 1:
            direction_string = "Forward"
        elif direction == 2:
            direction_string = "Backward"
        if blocking:
            self.controller.move_velocity(direction)
            self.moving_loop()
            self.logger.info('Moving in {} direction'.format(direction_string))    # the blocking for the controller is False now




    def make_step(self, stepsize, blocking):
        """| Moves the T-cube by one step of a stepsize.
        | Actually just uses move_relative, but I thought maybe this method might be useful for a gui.
        | If blocking is True, it will move until its done.
        | If blocking is False, it might not reach its destination if you dont give it time.

        :param stepsize: stepsize in mm or degree
        :type stepsize: pint quantity

        :param blocking: wait until moving is finished; default False
        :type blocking: bool
        """
        self.logger.debug('{} is making one step of size {}'.format(self._name, stepsize))
        self.move_relative(stepsize, blocking)

    def stop_moving(self):
        """| Stop motor but turn down velocity slowly (profiled).
        """
        self.logger.info('{} stops with moving.'.format(self._name))
        self.controller.stop_profiled()

#-----------------------------------------------------------------------------------------------------------------------
    def list_devices(self):
        """ | Lists all available devices.
        | It actually maybe should live outside of this class, since it talks to all Thorlabs motors attached, not a single one.
        | However, I could not make that work, so now I kept it here.
        | It also runs through the list now and checks whether the serial of the T-cube that you want to talk to, exists in the list.
        """
        self.aptmotorlist = self.controller.core.list_available_devices()
        self.logger.info('{} thorlabs_motor boxes found: {}'.format(len(self.aptmotorlist),self.aptmotorlist))

        found = False
        for ii in range(len(self.aptmotorlist)):
            if self.settings['serial'] in self.aptmotorlist[ii]:
                found = True
        return found


if __name__ == "__main__":
    import hyperion

    xMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850129, 'name': 'xMotor'}

    yMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube', 'serial': 83850123, 'name': 'yMotor'}

    WaveplateMotor = {'controller': 'hyperion.controller.thorlabs.tdc001_cube/TDC001_cube','serial' : 83850090, 'name': 'Waveplate'}

    with Thorlabsmotor(settings = xMotor) as sampleX, Thorlabsmotor(settings = WaveplateMotor) as waveplate:
        sampleX.position()

        #sampleX.move_relative(100*ur('um'),True)

        # sampleY.position()
        #
        # sampleY.move_relative(1*ur('mm'),True)
        # sampleY.position()

        waveplate.position()

        waveplate.move_absolute(10*ur('degree'),True)
        # time.sleep(1)
        # waveplate.stop_moving()
        # waveplate.position()

        #waveplate.move_relative(-10*ur('degrees'),True)

        #waveplate.make_step(1*ur('degrees'),True)

        waveplate.move_home(True)
