"""
================
Thorlabs motor Instrument
================

Connects for now to the TDC001 controller.

Example:
    Shows the list of available devices conects to motor x and initialize (without homing) it and moves it by 10 micro meter. 

```python
    >>>  from hyperion.instrument.motor.thorlabs_motor_instrument import Thorlabsmotor
	>>> checkdevices = Thorlabsmotor()
	>>> checkdevices.list_available_devices()
	>>> [(31,81818251)]
    >>> motorx = Thorlabsmotor()
	>>> motorx.initialize(81818251)
    >>> motorx.move_home(True)
    >>> motorx.move_relative_um(10)
```


"""
import logging
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion.experiment.base_experiment import BaseExperiment
from hyperion.controller.thorlabs.TDC001 import TDC001
from hyperion import ur


class Thorlabsmotor(BaseInstrument):
    """ Thorlabsmotor instrument

    """
    
    def __init__(self, settings = {'controller': 'hyperion.controller.thorlabs.TDC001/TDC001',
                                    'serial_number' : 81818251}):
        """ init of the class"""
        
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        
        if 'serial_number' in settings:
            self._serial_number = settings['serial_number']
        # property
        self._output = False
        self._mode = 0



        self.logger.info('Initializing Thorlabs motoer settings: {}'.format(settings))
        
        # initialize
        #self.controller.initialize()


    def list_devices(self):
        """ List all available devices. Returns serial numbers"""
        
        aptmotorlist=self.controller.list_available_devices()
        print(str(len(aptmotorlist)) + ' motor boxes found:')
        print(aptmotorlist)
    
    def initialize(self, port, homing=0):
        """ Starts the connection to the device in port

        :param port: Serial number to connect to
        :type port: string
        
        :param homing: if homing is not 0 than the motor first homes to its zero position so 
        hardware and software are connected. Afterwards it goes to the position defined by homing. This can be saved
        position from before.
        :type homing: number
        """
        self.logger.info('Opening connection to device.')
        motor=self.controller.initialize(port)
        if homing != 0:
            self.controller.move_home(True)
            self.controller.move_to(homing)
        return motor
    def initialize_available_motors(self, motor_bag):
        """
        Starts the connection to all motors 
        and sets the motor object in the motor_bag.
        
        :param motor_bag: a fictional bag with all the available motor instances.
        :type dict
        :return motor_bag: but this time it is filled with motor instances
        :rtype dict
        """
        opteller = 0
        list_with_actule_serial_numbers = []
        for i in self.controller.list_available_devices():
            list_with_actule_serial_numbers.append(i[1])
        
        experiment = BaseExperiment()
        experiment.load_config("C:\\Users\\LocalAdmin\\Desktop\\hyperion_stuff\\hyperion\\examples\\example_experiment_config.yml")
        for instrument in experiment.properties["Instruments"]:
            if "Motor" in str(instrument):
                for motor_item in experiment.properties["Instruments"][opteller].values():
                    if not "view" in motor_item and motor_item["serial_number"] in list_with_actule_serial_numbers:
                        #' '.join(instrument.keys()) = the name given(in the .yml file) to the motor
                        #motor_item["serial_number"] = serial_number of the motor
                        print("initialize: "+ str(motor_item["serial_number"]))
                        motor_bag[' '.join(instrument.keys())] = Thorlabsmotor(settings = {'controller': 'hyperion.controller.thorlabs.TDC001/TDC001','serial_number' : motor_item["serial_number"]})
                        motor_bag[' '.join(instrument.keys())].initialize(motor_item["serial_number"])
                    elif "view" in motor_item:
                        #these are the gui's
                        print("initialize: "+ str(motor_item["view"]))
                    else:
                        #these gui's are not available
                        print("motor: "+str(motor_item["serial_number"])+" is not available")
                    opteller += 1
            else:
                opteller += 1
        return motor_bag
    
    def move_relative_um(self,distance):
        """ Moves the motor to a relative position
        
        :param distance: relative distance in micro meter
        :type homing: number
        """
        distance_mm=distance/1000
        self.controller.move_by(distance_mm)
        

    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.info('Closing connection to device.')
        self.controller.finalize()

    def idn(self):
        """ Identify command

        :return: identification for the device
        :rtype: string

        """
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn()


    @property
    def amplitude(self):
        """ Gets the amplitude value
        :return: voltage amplitude value
        :rtype: pint quantity
        """
        self.logger.debug('Getting the amplitude.')
        return self.controller.amplitude * ur('volts')

    @amplitude.setter
    def amplitude(self, value):
        """ This method is to set the amplitude
        :param value: voltage value to set for the amplitude
        :type value: pint quantity
        """
        self.controller.amplitude = value.m_as('volts')


if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with Thorlabsmotor(settings = {'controller': 'hyperion.controller.thorlabs.TDC001/TDC001'}) as dev:
        dev.list_devices()



