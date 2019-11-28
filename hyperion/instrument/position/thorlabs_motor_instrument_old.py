"""
================
Thorlabs thorlabs_motor Instrument
================

Connects for now to the TDC001 controller.

Example:
    Shows the list of available devices conects to thorlabs_motor x and initialize (without homing) it and moves it by 10 micro meter.


python example code
    # >>> from hyperion.instrument.thorlabs_motor.thorlabs_motor_instrument import Thorlabsmotor
	# >>> checkdevices = Thorlabsmotor()
	# >>> checkdevices.list_available_devices()
	# >>> [(31,81818251)]
    # >>> motorx = Thorlabsmotor()
	# >>> motorx.initialize(81818251)
    # >>> motorx.move_home(True)
    # >>> motorx.move_relative(10)
"""

import logging
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion.experiment.base_experiment import BaseExperiment
from hyperion.controller.thorlabs.TDC001_old import TDC001
from hyperion import ur


class Thorlabsmotor_old(BaseInstrument):
    """ Thorlabsmotor instrument

    """
    
    def __init__(self, settings = {'controller': 'hyperion.controller.thorlabs.TDC001/TDC001',
                                    'serial_number' : 81818251}):
        """ init of the class"""
        
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)

        # properties
        self._output = False
        self._mode = 0
        self.logger.info('Initializing Thorlabs motor settings: {}'.format(settings))

        if 'serial' in settings:
            self._serial_number = settings['serial']
            self.initialize()

    def list_devices(self):
        """ List all available devices"""
        
        aptmotorlist=self.controller.list_available_devices()
        self.logger.info(str(len(aptmotorlist)) + ' thorlabs_motor boxes found:')
        return aptmotorlist
    
    def initialize(self, port=None, homing=0):
        """ Starts the connection to the device in port

        :param port: Serial number to connect to
        :type port: string
        
        :param homing: if homing is not 0 than the thorlabs_motor first homes to its zero position so
        hardware and software are connected. Afterwards it goes to the position defined by homing. This can be saved
        position from before.
        :type homing: number
        """
        self.logger.info('Opening connection to device.')
        if port is None:
            motor = self.controller.initialize(self._serial_number)
        else:
            motor=self.controller.initialize(port)
        # motor = self.controller.initialize()
        if homing != 0:
            self.controller.move_home(True)
            self.controller.move_to(homing)
        return motor

    def initialize_available_motors(self, motor_bag):
        """
        Starts the connection to all motors and sets the thorlabs_motor object in the motor_bag.
        
        :param motor_bag: a dictionary with all the available thorlabs_motor instances.
        :type dictionary
        :return motor_bag: but this time it is filled with thorlabs_motor instances
        :rtype dictionary
        """
        list_with_actule_serial_numbers = []
        for i in self.controller.list_available_devices():
            list_with_actule_serial_numbers.append(i[1])
        
        self.experiment = BaseExperiment()
        #hardcode your paths to the config here:
        self.experiment.load_config("D:\\labsoftware\\hyperion\\examples\\example_experiment_config.yml")

        for instrument in self.experiment.properties["Instruments"]:
            if "Motor" in instrument:
                instrument_path = self.experiment.properties["Instruments"][instrument]
                try:
                    if instrument_path["serial_number"] in list_with_actule_serial_numbers:
                        motor_bag[str(instrument)] = Thorlabsmotor(settings = {'controller': 'hyperion.controller.thorlabs.TDC001/TDC001','serial_number' : instrument_path["serial_number"]})
                        motor_bag[str(instrument)].initialize(instrument_path["serial_number"])
                    else:
                        print("thorlabs_motor: "+str(instrument_path["serial_number"])+" is not available")
                except KeyError:
                    #this is the view
                    print("no serial_number found in thorlabs_motor: "+str(instrument))
                except Exception:
                    print("thorlabs_motor: "+str(instrument_path["serial_number"])+" is not available")

        print("-"*40)
        return motor_bag

    def make_slider_list(self):
        slider_list = []
        temporary_list = []
        slider_namen_list = ["slider_x","slider_y","slider_z"]
        opteller = 0
        for instrument in self.experiment.properties["MetaInstruments"]:
            if "Motor" in instrument:
                for motor_naam in self.experiment.properties["MetaInstruments"][instrument].items():
                    temporary_list.append(slider_namen_list[opteller])
                    temporary_list.append(motor_naam[1])
                    slider_list.append(temporary_list)
                    #reset values
                    temporary_list = []
                    opteller += 1
        
        return slider_list
    
    def move_relative(self, distance):
        """ Moves the thorlabs_motor to a relative position
        
        :param distance: relative distance in micro meter
        :type distance: a pint quantity in micrometer
        """
        self.logger.info("moving: "+str(distance)+" in micrometer")     #this needs to be changed!!!!!!!!
        distance = distance * ur('micrometer')
        distance_mm = distance.to('mm')
        self.controller.move_by(distance_mm, True)

    def move_absolute(self, distance):
        """| Moves the thorlabs_motor by the a absolute distance that is given
            
        :param: distance: a absolute distance
        :type: a pint quantity in micrometer
        """
        distance = distance * ur("micrometer")      #this needs to be changed!!!!!!!!
        #print("some text", distance)
        self.logger.info("moving: "+str(distance))
        self.controller.move_to(float(distance.magnitude),True)
        self.logger.debug("The thorlabs_motor has moved "+str(distance))
        

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
        return self.controller.identify()


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

    @property
    def position(self):
        """Link to controller to get current position

        :return: position
        """
        pos = self.controller.position
        return pos

    def axis_info(self):
        """Link to controller to get axis info, including the range, which helps to know if its a motorized waveplate or stage

        :return: info = (min_pos.value, max_pos.value, units.value, pitch.value)
        """
        info = self.controller.get_stage_axis_info()
        return info


if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    xMotor = {'serial': 83850129, 'instrument': 'hyperion.instrument.position.thorlabs_motor_instrument/Thorlabsmotor',
                'controller': 'hyperion.controller.thorlabs.TDC001/TDC001'}

    yMotor = {'serial': 83850123, 'instrument': 'hyperion.instrument.position.thorlabs_motor_instrument/Thorlabsmotor',
                'controller': 'hyperion.controller.thorlabs.TDC001/TDC001'}


    with Thorlabsmotor_old(settings = xMotor) as sampleX, Thorlabsmotor_old(settings = yMotor) as sampleY:
        # dev.initialize()

        print(type(sampleX.controller._serial_number))

        print(sampleX.axis_info())

        print(sampleX.position)

        sampleX.move_relative(50)

        print(sampleX.position)

        print(type(sampleY.controller._serial_number))

        print(sampleY.axis_info())

        print(sampleY.position)

        # for motor in dev.list_devices():
        #     dev.logger.debug(motor)
        #     dev.initialize(motor[1])
        #     dev.idn()
        #     stage_info = dev.controller.get_stage_axis_info()
        #     dev.logger.debug(stage_info)
        #     if stage_info[1] == 12.0:
        #         dev.move_relative(2.0)
        #     elif stage_info[1] == 360.0:        #that means it's connected to the waveplate
        #         dev.move_absolute(20)
        #     dev.finalize()
        #     dev.logger.debug("-"*40)


