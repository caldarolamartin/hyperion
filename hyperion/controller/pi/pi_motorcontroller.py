"""
=======================
PI motor controller
=======================

Note: this is a wrapper class around an external controller to fit it into hyperion structure

Is based on the imported PI python software distributed by PI.
This should be installed on the local computer.
This controller basically is just a wrapper to make things work within hyperion.
PI Motorstage, make sure the motor-controller box and the stage are connected and that the drivers for the motor box are installed
(from the CD drive!!). Also make sure the PI_Mercury_GCS_DLL_x64.dll is in the same folder as the script


"""
from hyperion import logging
from hyperion.controller.base_controller import BaseController
import sys
sys.path.insert(0, "C:\\Users\\Public\\Documents\\Python Scripts\\Software\\PIPython-1.3.4.17")
from pipython import pitools
from pipython import GCSDevice


class PI_motorcontroller(BaseController):
    """
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

        self.logger.info('Class PI_motorcontroller is created')


        # Calls init of core.Motor, whose init is executed
        super().__init__()

        # There is one function that is outside of the Motor class in the core, which would be useful to have accessible.
        # That would be list_available_devices
        self.logger.debug("Done with motorcontroller")

        self.CONTROLLERNAME = str(settings['controllername'])
        print(self.CONTROLLERNAME)
        self.STAGES = (settings['stages'],)  # connect stages to axes
        self.REFMODE = (settings['refmode'],)  # reference the connected stages
    def initialize(self):
        """ | The external core.Motor object is already initialized by executing super().__init__(self.serial).
        | So this function is just so that higher layers dont give errors.
        """

        pidevice = GCSDevice('C-863.10')
        pidevice.InterfaceSetupDlg(key='sample')
        print('connected: {}'.format(pidevice.qIDN().strip()))
        print('initialize connected stages...')
        pitools.startup(pidevice, stages=self.STAGES, refmode=self.REFMODE)
        return pidevice
        self.logger.info('initialized PI motorcontroller')

    def finalize(self):
        """| Here is should close the connection with the device, but this or similar functions do not exist in the core.Motor.
        | So this function is just so that higher layers dont give errors.
        """

        if self._is_initialized:
            self.logger.debug('It should close the connection here.')
        else:
            self.logger.warning('Finalizing before initializing connection to {}'.format(self.name))
        self._is_initialized = False


if __name__ == "__main__":

    # settings for your device
    settings = {'controllername': "C-836.10",'stages':'M-404.6PD','refmode':'MNL' }

    #    with my_class(settings = settingsX) as dev:

    contr = PI_motorcontroller(settings=settings)
    print("gelukt")
    dev=contr.initialize()