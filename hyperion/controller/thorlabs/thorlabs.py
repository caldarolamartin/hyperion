# Template with the minimal structure and extra explanatory comments.
# For hyperion version 0.1

"""
=======================
Device Model Controller
=======================

Description of device controller
"""

import logging
from hyperion.controller.base_controller import BaseController
import thorlabs_apt._APTAPI as _APTAPI
import thorlabs_apt._error_codes as _error_codes
import thorlabs_apt.core as core
from thorlabs_apt.core import Motor as motor
import time


#class DeviceModelController(BaseController,core):
class DeviceModelController(BaseController):
    """ 
    More description here
    
    :param settings: This includes all the settings needed to connect to the device in question.
    :type settings: dict
    """
    
    # MANDATORY METHOD:
    def __init__(self, settings):
        """ Don't put docstring here but directly under class ClassName() """
        
        # MANDATORY LINES at beginning of __init__():
        # Call init of BaseController
        super().__init__(settings)


        # In the background, the __init__() of Basecontroller will
        # do these lines for you:
        # self._is_initialized = False
        # self._settings = settings
        # Create logger
        self.logger = logging.getLogger(__name__)

        self.logger.info('Class TDC001 (Thorlabs motors) is created.')
       
        self.name = 'Device Model Controller'

        self.core = core
        self._APTAPI = _APTAPI
        self._error_codes = _error_codes
        self.motor = motor
        # Storing the settings in internal variables.
        # If they're not specified, default values are used.

    def initialize(self):
        self._is_initialized = True


    # MANDATORY METHOD
    # If you don't make it the method of the same name from BaseController will
    # be called to warn you that you've forgotten to make it.
    def finalize(self):
        """
        This method closes the connection to the device.
        It is ran automatically if you use a with block.
        """
        
        if self._is_initialized:
            # Your code to close the connection goes here
            self.logger.debug('Doing something')
        else:
            self.logger.warning('Finalizing before initializing connection to {}'.format(self.name))

        # MANDATORY LINE at end of finalilze:
        # Reset the flag to indicate the object is not connected to the device
        self._is_initialized = False

    # strongly recommended method:
    def idn(self):
        """
        Identify command

        :return: identification for the device
        :rtype: string
        """
        self.logger.debug('Ask *IDN? to device.')
        return self.query('*IDN?')[-1]

# The dummy version of the controller class:
# Its name should be the same as the main controller class above,
# but with 'Dummy' suffix. (This allows it to be automatically found)
# It shoudl inherit from the main controller class above
class DeviceModelControllerDummy(DeviceModelController):
    """
    Device Model Controller Dummy
    =============================

    A dummy version of the Device Model Controller

    Some notes on how to use it.
    """
    
    # If you don't want to write it put this one word here.
    # In that case the dummy class is identical to the parent class.
    pass 
    
    # Otherwise remove the pass above and add methods that overwrite those from
    # the parent class. Typically you would overwrite the methods that directly
    # deal with communicating to the hardware, such as read() and write().


# Here follows code to for testing (during development)
# It is run when you run this file directly.

if __name__ == "__main__":
    
    # Import stuff for logging. This will change in a future version
    from hyperion import _logger_format, _logger_settings
    logging.basicConfig(level=logging.WARNING, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    # Set dummy=False to work with the real device
    dummy = False

    if dummy:
        my_class = DeviceModelControllerDummy
    else:
        my_class = DeviceModelController

    # settings for your device
    example_settings = {'port': 'COM4', 'baudrate': 9600, 'write_termination': '\n'}

    # Here we create an object of our controller class.
    # By doing it in a with statement, __exit__() and hence finalize() will be 
    # called even if the code crashes. This will ensure the connection to the 
    # device is properly closed.
    with my_class(settings = example_settings) as dev:

        serial_number = 83850129
        #serial_number = 83850090

        print(dev.core.hardware_info(serial_number))
        print('Start:')
        print(dev.core.list_available_devices())


        print('serial number: {}'.format(dev.motor(serial_number).serial_number))
        print('hardware info {}'.format(dev.motor(serial_number).hardware_info))
        dev.motor(serial_number).identify

        print('position: {}'.format(dev.motor(serial_number).position))
        print('in motion? {}'.format(dev.motor(serial_number).is_in_motion))
        print('motor limit reached? {}'.format(dev.motor(serial_number).motor_current_limit_reached))
        print('motor error? {}'.format(dev.motor(serial_number).motion_error))

        print('velocity parameters: {}'.format(dev.motor(serial_number).get_velocity_parameters()))
        print('velocity parameters: {}'.format(dev.motor(serial_number).get_velocity_parameter_limits()))

        axis_info = dev.motor(serial_number).get_stage_axis_info()
        print('axis info: {}'.format(axis_info))
        if axis_info[1] > 300:
            print('this is probably connected to a waveplate')
        else:
            print('this is probably connected to a motor stage')

        dev.motor(serial_number).move_to(1.0,True)
        print('position: {}'.format(dev.motor(serial_number).position))

        dev.motor(serial_number).move_by(1.0, True)
        print('position: {}'.format(dev.motor(serial_number).position))

        dev.motor(serial_number).move_home(False)
        time.sleep(1)
        print('position: {}'.format(dev.motor(serial_number).position))

        dev.motor(serial_number).stop_profiled()
        print('position: {}'.format(dev.motor(serial_number).position))


            #import dev.core.Motor()


            #if motor[1] == 83850111:
            # dev.core.initialize(motor[1])
            # dev.core.idn()
            # print(dev.core.get_stage_axis_info())
            # #dev.move_to(0)
            # print(dev.core.position)
            # dev.core.finalize()
            # print("-"*40)



        # Call methods and print result to test if the class works as expected.
        
        # No need to call dev.finalize() The with statement takes care of that.
