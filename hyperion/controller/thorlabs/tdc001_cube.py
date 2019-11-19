"""
=======================
Thorlabs motor controller
=======================

Is based on the imported Thorlabs APT python software from https://github.com/qpit/thorlabs_apt/tree/master/thorlabs_apt.
This is installed in hyperion and can be found in C:/Users/NAME/AppData/Local/Continuum/anaconda3/envs/hyperion/Lib/site-packages/thorlabs_apt.
This controller basically is just a wrapper to make things work within hyperion.
The core is not always well documented, for better descriptions see the thorlabs_motor_instrument.

"""

import logging
from hyperion.controller.base_controller import BaseController
import thorlabs_apt.core as core
import sys
import time

class TDC001_cube(core.Motor, BaseController):
    """ | This is the controller for the Thorlabs TDC001_cubes that work with motors.
    | It is just a wrapper that is linking to the thorlabs_apt.core with the class Motor in it.
    | Usually, the super().__init__() would execute the init of the BaseController.
    | However, since the current class inherits from both core.Motor and BaseController, only the first init is executed.

    :param settings: the class Motor needs a serial number
    :type settings: dict
    """

    def __init__(self, settings):
        """ | Usually, the super().__init__() would execute the init of the BaseController.
        | However, since the current class inherits from both core.Motor and BaseController, only the first init is executed.
        | So a few lines are copied from BaseController.

        :param settings: the class Motor needs a serial number
        :type settings: dict
        """
        self.logger = logging.getLogger(__name__)
        self._is_initialized = False

        self.logger.info('Class TDC001_cube (Thorlabs motors) is created.')
        self.name = 'TDC001_cube'

        #These lines are a copy of the init of BaseController, that is not executed because it is the second inheritance
        self._settings = settings
        self.serial = settings['serial']
        self._is_initialized = True

        # Calls init of core.Motor, whose init is executed
        super().__init__(self.serial)

        # There is one function that is outside of the Motor class in the core, which would be useful to have accessible.
        # That would be list_available_devices.
        self.core = core

    def initialize(self):
        """ | The external core.Motor object is already initialized by executing super().__init__(self.serial).
        | So this function is just so that higher layers dont give errors.
        """
        self.logger.debug('The external Motor object already initialized in the init.')

    def finalize(self):
        """| Here is should close the connection with the device, but this or similar functions do not exist in the core.Motor.
        | So this function is just so that higher layers dont give errors.
        """

        if self._is_initialized:
            self.logger.debug('It should close the connection here.')
        else:
            self.logger.warning('Finalizing before initializing connection to {}'.format(self.name))
        self._is_initialized = False


class TDC001_cubeDummy(TDC001_cube):
    """
    TDC001_cube Dummy
    =============================
    A dummy version that does not do anything at all.
    """
    pass


if __name__ == "__main__":
    
    import hyperion

    # Set dummy=False to work with the real device
    dummy = False

    if dummy:
        my_class = TDC001_cubeDummy
    else:
        my_class = TDC001_cube

    # settings for your device
    settingsX = {'serial': 83850129}
    settingsWave = {'serial': 83850090}

#    with my_class(settings = settingsX) as dev:

    dev = my_class(settings=settingsX)
    #This function comes from the core, outside of this specific motor
    print('T-cubes available: {}'.format(dev.core.list_available_devices()))

    #Example on how to communicate with this T-cube
    print('serial number: {}'.format(dev.serial_number))
    print('hardware info {}'.format(dev.hardware_info))
    dev.identify

    print('position: {}'.format(dev.position))
    print('in motion? {}'.format(dev.is_in_motion))
    print('motor limit reached? {}'.format(dev.motor_current_limit_reached))
    print('motor error? {}'.format(dev.motion_error))

    print('velocity parameters: {}'.format(dev.get_velocity_parameters()))
    print('velocity parameters: {}'.format(dev.get_velocity_parameter_limits()))

    print('motor parameters {}'.format(dev.get_motor_parameters()))


    axis_info = dev.get_stage_axis_info()
    print('axis info: {}'.format(axis_info))
    if axis_info[1] > 359.0:
        print('this is probably connected to a waveplate')
        unit = 'degree'
    elif 11.0 < axis_info[1] < 13.0:
        print('this is probably connected to a motor stage')
        unit = 'mm'
    else:
        print('connected kind of thorlabs device is unclear, max range: {}'.format(axis_info[1]))
        unit = '?'

    new_min_pos = -12.0

    #def set_stage_axis_info(self, min_pos, max_pos, units, pitch):

    dev.set_stage_axis_info(new_min_pos,axis_info[1], axis_info[2], axis_info[3])

    print(dev.get_stage_axis_info())

        # dev.move_to(5.0,True)
        # print('position: {} {}'.format(dev.position,unit))
        # while dev.is_in_motion:
        #     time.sleep(0.1)
        #     print('is moving? {}'.format(dev.is_in_motion))
        #
        # print('position: {} {}'.format(dev.position, unit))
        #
        # dev.move_by(1.0, True)
        # print('position: {} {}'.format(dev.position,unit))

        # dev.move_home(False)
        # time.sleep(1)
        # print('position: {} {}'.format(dev.position,unit))
        #
        # dev.stop_profiled()
        # print('position: {} {}'.format(dev.position,unit))
