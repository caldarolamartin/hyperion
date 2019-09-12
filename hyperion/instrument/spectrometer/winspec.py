# -*- coding: utf-8 -*-
"""
==================
Winspec Instrument
==================

Aron Opheij, TU Delft 2019

"""
import logging
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur

class Winspec(BaseInstrument):
    """ Instrument to control Winspec software. """
    def __init__(self, settings = {'port':None, 'dummy': False,
                                   'controller': 'hyperion.controller.princeton.winspec/WinspecController'}):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class ExampleInstrument created.')
        

    def initialize(self):
        """ Starts the connection to the Winspec softare and retrieves parameters. """
        self.logger.info('Opening connection to device.')
        self.controller.initialize()
        self._gain = self.gain
        self._exposure_time = self.exposure_time
        self._accums = self.accumulations
        self._target_temp = self.target_temp
        

    def finalize(self):
        """ Finalizes Winspec Controller. """
        self.logger.info('Closing connection to device.')
        self.controller.finalize()

    def idn(self):
        """
        Identify command

        :return: Identification string of the device.
        :rtype: string
        """
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn()

    # Hardware settings:

    @property
    def current_temp(self):
        """
        read-only attribute: Temperature measured by Winspec.
        
        getter: Returns the Temperature measued by Winspec.
        type: float
        """
        return self.controller.exp_get('ACTUAL_TEMP')[0]
    
    @property
    def temp_locked(self):
        """
        read-only attribute: Temperature locked state measured by Winspec.
        
        getter: Returns True is the Temperature is "locked"
        type: bool
        """
        return self.controller.exp_get('TEMP_STATUS')[0] == 1
    
    @property
    def target_temp(self):
        """
        attribute: Detector target temperature in degrees Celcius
        
        getter: Returns Target Temperature set in Winspec
        setter: Attempts to updates Target Temperature in Winspec if required. Gives warning if failed.
        type: float
        """
        self._target_temp = self.controller.exp_get('TEMPERATURE')[0]
        return self._target_temp
    
    @target_temp.setter    
    def target_temp(self, value):
        if value != self._target_temp:
            if self.controller.exp_set('TEMPERATURE', value):        # this line also sets the value in winspec
                self.logger.warning('error setting value: {}'.format(value))
            if self.target_temp != value:          # this line also makes sure self._target_temp contains the actual Winspec value
                self.logger.warning('attempted to set target temperature to {}, but Winspec is at {}'.format(self._gain, value))

#display:
#ROTATE
#FLIP
#REVERSE
#

    @property
    def display_rotate(self):
        """
        attribute: Display Rotate.
        
        getter: Returns if Display Rotation is set in Winspec.
        setter: Sets Display Rotation in Winspec.
        type: bool
        """
        return self.controller.exp_get('ROTATE')[0] == 1

    @display_rotate.setter
    def display_rotate(self, value):
        self.controller.exp_set('ROTATE', value!=0)     # the value!=0 converts it to a bool
        
    @property
    def display_reverse(self):
        """
        attribute: Display Reverse (left-right)
        
        getter: Returns if Display Reverse is set in Winspec.
        setter: Sets Display Reverse in Winspec.
        type: bool
        """
        return self.controller.exp_get('REVERSE')[0] == 1

    @display_reverse.setter
    def display_reverse(self, value):
        self.controller.exp_set('REVERSE', value!=0)     # the value!=0 converts it to a bool

    @property
    def display_flip(self):
        """
        attribute: Display Flip (up-down).
        
        getter: Returns if Display Flip is set in Winspec.
        setter: Sets Display Flip in Winspec.
        type: bool
        """
        return self.controller.exp_get('FLIP')[0] == 1

    @display_flip.setter
    def display_flip(self, value):
        self.controller.exp_set('FLIP', value!=0)     # the value!=0 converts it to a bool
        


    # Experiment / ADC settings

    @property
    def gain(self):
        """
        attribute: ADC Gain value. (Known allowed values: 1, 2)
        
        getter: Returns Gain set in Winspec
        setter: Attempts to updates Gain setting in Winspec if required. Gives warning if failed.
        type: int
        """
        self._gain = self.controller.exp_get('GAIN')[0]
        return self._gain
    
    @gain.setter    
    def gain(self, value):
        if value != self._gain:
            if self.controller.exp_set('GAIN', value):        # this line also sets the value in winspec
                self.logger.warning('error setting value: {}'.format(value))
            if self.gain != value:          # this line also makes sure self._gain contains the actual Winspec value
                self.logger.warning('attempted to set gain to {}, but Winspec is at {}'.format(self._gain, value))

    @property
    def accumulations(self):
        """
        attribute: Number of Accumulations.
        
        getter: Returns the Number of Accumulations set in Winspec
        setter: Attempts to updates the Number of Accumulations in Winspec if required. Gives warning if failed.
        type: int
        """
        self._accums = self.controller.exp_get('ACCUMS')[0]
        return self._accums
    
    @accumulations.setter
    def accumulations(self, value):
        if value != self._accums:
            if self.controller.exp_set('ACCUMS', value):        # this line also sets the value in winspec
                self.logger.warning('error setting value: {}'.format(value))
            if self.accumulations != value:          # this line also makes sure self._accums contains the actual Winspec value
                self.logger.warning('attempted to set accumulations to {}, but Winspec is at {}'.format(self._accums, value))

    @property
    def exposure_time(self):
        """
        attribute: Exposure Time.
        
        getter: Returns the Exposure Time set in Winspec
        setter: Attempts to updates the Exposure Time in Winspec if required. Gives warning if failed.
        type: Pint Quantity of unit time
        """

        winspec_exposure_units = [ur('us'), ur('ms'), ur('s'), ur('min')]
        exp_pint_unit = winspec_exposure_units[ self.controller.exp_get('EXPOSURETIME_UNITS')[0] -1 ]
        exp_value = self.controller.exp_get('EXPOSURETIME')[0]
        self._exposure_time = exp_value * exp_pint_unit
        return self._exposure_time
        
    @exposure_time.setter
    def exposure_time(self, value):
        if type(value) is not type(ur('s')):
            self.logger.error('exposure_time should be Pint quantity')
        elif value.dimensionality != ur('s').dimensionality:
            self.logger.error('exposure_time should have unit of time')
        else:
            if value < 1*ur('microsecond'):                                         # remove this if necessary
                self.logger.warning('WinSpec will not accept exposuretime smaller than 1 us')
            
            if value != self._exposure_time or value.m != self._exposure_time.m:
                if value.units == 'microsecond':
                    exp_unit = 1
                    exp_value = value.m_as('microsecond')
                elif value.units == 'millisecond':
                    exp_unit = 2
                    exp_value = value.m_as('millisecond')
                elif value.units == 'second':
                    exp_unit = 3
                    exp_value = value.m_as('second')
                elif value.units == 'minute':    
                    exp_unit = 4
                    exp_value = value.m_as('minute')
                elif value > 10*ur('minute'):
                    exp_unit= 4
                    exp_value = value.m_as('minute')
                elif value < 1*ur('microsecond'):
                    exp_unit = 1
                    exp_value = value.m_as('microsecond')
                else:
                    exp_unit = 3
                    exp_value = value.m_as('second')
        
                self.controller.exp_set('EXPOSURETIME_UNITS',exp_unit)
                self.controller.exp_set('EXPOSURETIME',exp_value)
                
        if self.exposure_time != value:     # this line also makes sure self._exposuretime gets the real Winspec value
            self.logger.warning('attempted to set exposure time to {}, but Winspec is at {}'.format(value, self._exposure_time))
            

            
            
    def timing_mode():
        # 1 Free Run
        # 3 External Sync
        pass
        
    def shutter_control():
        # 1 Normal
        # 2 Disabled closed
        # 3 Disabled opened
        pass
        
    def delay_time():
        # Experiment / Timing / Delay Time in seconds
        pass
        
        
#edge_trigger
        


#XDIM
#YDIM
#XBINNED ?
#
#
#





#    @property
#    def amplitude(self):
#        """ Gets the amplitude value
#        :return: voltage amplitude value
#        :rtype: pint quantity
#        """
#        self.logger.debug('Getting the amplitude.')
#        return self.controller.amplitude * ur('volts')
#
#    @amplitude.setter
#    def amplitude(self, value):
#        """ This method is to set the amplitude
#        :param value: voltage value to set for the amplitude
#        :type value: pint quantity
#        """
#        self.controller.amplitude = value.m_as('volts')


if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

#    dummy = [False]
#    for d in dummy:
#        with Winspec(settings = {'port':'None', 'dummy' : d,
#                                   'controller': 'hyperion.controller.princeton.winspec/WinspecController'}) as dev:
#            dev.initialize()
#            print(dev.idn())
#            # v = 2 * ur('volts')
#            # dev.amplitude = v
#            # print(dev.amplitude)
#            # dev.amplitude = v
#            # print(dev.amplitude)
#
#    print('done')
    
    ws = Winspec(settings = {'port':'None', 'dummy' : False,
                                   'controller': 'hyperion.controller.princeton.winspec/WinspecController'})
    ws.initialize()