# -*- coding: utf-8 -*-
"""
==================
Winspec Instrument
==================

Aron Opheij, TU Delft 2019


Tips for finding new functionality:

Once you have an WinspecInstr object named ws, try the following things:
This will list all keywords:
[key for key in ws.controller.params]
There are shorter lists with only experiment (EXP) and spectrograph (SPT) commands:
[key for key in ws.controller.params_exp]       # note that prefic EXP_ is removed
[key for key in ws.controller.params_spt]       # note that prefic SPT_ is removed
To filter in those you could try:
[key for key in ws.controller.params_exp if 'EXPOSURE' in key]
[key for key in ws.controller.params_spt if 'GROOVES' in key]

To request the value for a keyword try:
ws.controller.exp_get('EXPOSURETIME')
ws.controller.exp_get('GRAT_GROOVES')


Or all grating related keywords:

Or all keywords:
[key for key in ws.controller.params]
If you want only those that have EXPOSURE in their name:

Try:




"""
import logging
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur, Q_
from hyperion.view.general_worker import WorkThread
import threading
import time
# import numpy as np      # I'm having issues with numpy on the computer I'm developing, so I disable it temporarily and modified take_spectrum not to depend on it



class WinspecInstr(BaseInstrument):
    """ Winspec Instrument

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict

    """

    def __init__(self, settings):                   # not specifying a default value for settings is less confusing for novice users
        # don't place the docstring here but above in the class definition
        super().__init__(settings)                  # mandatory line
        self.logger = logging.getLogger(__name__)   # mandatory line
        self.logger.info('Class ExampleInstrument created.')
        self.settings = settings
        self.default_name = 'temp.SPE'

        self._timing_modes = self.remove_unavailable('timing_modes', [0, 'Free Run', 2, 'External Sync'])
        self._shutter_controls = self.remove_unavailable('shutter_controls', [0, 'Normal', 'Disabled Closed', 'Disabled Opened'])
        self._fast_safe = self.remove_unavailable('fast_safe', ['Fast', 'Safe'])

        self.initialize()   # ! required to do this in the __init__

        self._is_acquiring = False
        self._is_moving = False

        self.move_grating_thread = threading.Thread(target = self._move_grating)
        # self.move_grating_thread = WorkThread(self._move_grating)


        # self.mythread = WorkThread(self.mytestfunc)
        # self.mythread.start()
        # print('outside')


    def mytestfunc(self):
        print('inside before')
        time.sleep(1)
        print('inside after')

    def initialize(self):
        """ Starts the connection to the Winspec softare and retrieves parameters. """
        self.logger.info('Opening connection to device.')
        self.controller.initialize()
        self._gain = self.gain
        self._exposure_time = self.exposure_time
        self._accums = self.accumulations
        self._target_temp = self.target_temp



        self.get_gratings_info()
        # self.gratings

    def _move_grating(self):
        #
        self._is_moving = True
        self.controller.spt.Move()
        self._is_moving = False

    def finalize(self):
        """ Mandatory function. Get's called when exiting a 'with' statement."""
        self.logger.info('Closing connection to device.')
        self.controller.finalize()

    def remove_unavailable(self, settings_key, default_options_list):
        # remove items from options_list that don't occur in settings_list and replace with their index
        if settings_key in self.settings:
            for index, value in enumerate(default_options_list):
                if value not in self.settings[settings_key]:
                    default_options_list[index] = index
        return default_options_list

    def get_gratings_info(self):
        self.gratings_grooves = []      # list to hold the grooves/mm for the different gratings
        self.gratings_blaze_name = []   # list to hold the blaze text
        self.gratings_blaze = []        # list to hold numeric blaze wavelength value
        self.number_of_gratings = self.controller.spt_get('GRATINGSPERTURRET')[0]
        # this seems to be the same value:   self.controller.spt_get('INST_CUR_GRAT_NUM')[0]
        for k in range(self.number_of_gratings):
            self.gratings_grooves.append( self.controller.spt_get('INST_GRAT_GROOVES', k+1)[0] )
            text = self.controller.spt_get('GRAT_USERNAME', k+1)[0]
            self.gratings_blaze_name = text
            # try to interpret the blaze wavelength:
            self.gratings_blaze.append(int(''.join(filter(str.isdigit, text))))

        self.logger.info('{} gratings found. grooves/mm: {}, blaze: {}'.format(self.number_of_gratings, self.gratings_grooves,self.gratings_blaze))

    def idn(self):
        """
        Identify command

        :return: Identification string of the device.
        :rtype: string
        """
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn()


    def take_spectrum(self, name=None):
        # very rudimentary version
        if name==None:
            name=self.default_name
        self.doc = self.controller.docfile()
        self.controller.exp.Start(self.doc)
        while self.controller.exp_get('RUNNING')[0]:
            time.sleep(0.02)
        frame = self.doc.GetFrame(1,self.controller._variant_array)
        return frame # temporarly remove dependence on numpy: np.asarray(frame)

        #self.doc.Set


    # Grating Settings:  -----------------------------------------------------------------------------------------

    # ws.controller.spt.Move()

    #        print('GRATINGSPERTURRET: {}'.format(dev.spt_get('GRATINGSPERTURRET')))
    #        print('INST_GRAT_GROOVES 0: {}'.format(dev.spt_get('INST_GRAT_GROOVES',0)))
    #        print('INST_GRAT_GROOVES 1: {}'.format(dev.spt_get('INST_GRAT_GROOVES',1)))
    #        print('INST_GRAT_GROOVES 2: {}'.format(dev.spt_get('INST_GRAT_GROOVES',2)))
    #        print('CUR_GRATING: {}'.format(dev.spt_get('CUR_GRATING')))
    #        print('INST_CUR_GRAT_NUM: {}'.format(dev.spt_get('INST_CUR_GRAT_NUM')))
    #        print('CUR_POSITION: {}'.format(dev.spt_get('CUR_POSITION')))                  <<  in nm
    #        print('ACTIVE_GRAT_POS: {}'.format(dev.spt_get('ACTIVE_GRAT_POS')))            <<  in ???

    @property
    def grating(self):
        return self.controller.spt_get('CUR_GRATING')[0]

    @grating.setter
    def grating(self, number):
        if 0 < number <= self.number_of_gratings:
            if number == self.controller.spt_get('CUR_GRATING')[0]:
                self.logger.debug('Grating {} already in place'.format(number))
            else:
                self.controller.spt_set('NEW_GRATING', number)
                self.move_grating_thread.start()
        else:
            self.logger.warning('{} is invalid grating number (1-{})'.format(number, self.number_of_gratings))

    @property
    def central_wav(self):
        return self.controller.spt_get('CUR_POSITION')[0]

    @central_wav.setter
    def central_wav(self, nanometers):
        if nanometers == self.controller.spt_get('CUR_POSITION')[0]:
            self.logger.debug('Grating already at {}nm'.format(nanometers))
        else:
            self.controller.spt_set('NEW_POSITION', nanometers)
            self.controller.spt.Move()
            # self.move_grating_thread.start()





    # Hardware settings:   ---------------------------------------------------------------------------------------

    @property
    def current_temp(self):
        """
        read-only attribute: Temperature measured by Winspec in degrees Celcius.

        getter: Returns the Temperature measued by Winspec.
        type: float
        """
        return self.controller.exp_get('ACTUAL_TEMP')[0]

    @property
    def temp_locked(self):
        """
        read-only attribute: Temperature locked state measured by Winspec in degrees Celcius.

        getter: Returns True is the Temperature is "locked"
        type: bool
        """
        return self.controller.exp_get('TEMP_STATUS')[0] == 1

    @property
    def target_temp(self):
        """
        attribute: Detector target temperature in degrees Celcius.

        getter: Returns Target Temperature set in Winspec
        setter: Attempts to updates Target Temperature in Winspec if required. Gives warning if failed.
        type: float
        """
        self._target_temp = self.controller.exp_get('TEMPERATURE')[0]
        return self._target_temp

    @target_temp.setter
    def target_temp(self, value):
        # don't place doctring here. add setter info to the getter/property method
        if value != self._target_temp:
            if self.controller.exp_set('TEMPERATURE', value):        # this line also sets the value in winspec
                self.logger.warning('error setting value: {}'.format(value))
            if self.target_temp != value:          # this line also makes sure self._target_temp contains the actual Winspec value
                self.logger.warning('attempted to set target temperature to {}, but Winspec is at {}'.format(self._gain, value))

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



    # Experiment / ADC settings:   --------------------------------------------

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
                self.logger.warning('attempted to set gain to {}, but Winspec is at {}'.format(value, self._gain))

    # Experiment / Main settings:  --------------------------------------------

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
        if type(value) is not type(Q_('s')):
            self.logger.error('exposure_time should be Pint quantity')
        if value.dimensionality != Q_('s').dimensionality:
            self.logger.error('exposure_time should be Pint quantity with unit of time')
        else:
            if value.m_as('us') < 1:                                                    # remove this if necessary
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

    # Experiment / Data Correction settings: ----------------------------------

    @property
    def bg_subtract(self):
        return self.controller.exp_get('BBACKSUBTRACT')[0] == 1     # turn it into bool

    @bg_subtract.setter
    def bg_subtract(self, value):
        self.controller.exp_set('BBACKSUBTRACT',value!=0)       # !=0  forces it to be bool

    @property
    def bg_file(self):
        return self.controller.exp_get('DARKNAME')[0]

    @bg_file.setter
    def bg_file(self, filename):
        # NOTE, this does not check if the file exists
        return self.controller.exp_set('DARKNAME', filename)

# Could repeat this for flatfield and blemish
#        FLATFLDNAME
#        BDOFLATFIELD
#        BLEMISHFILENAME
#        DOBLEMISH


# BGTYPE ??

    # Experiment / Timing settings: ----------------------------------

    @property
    def delay_time_s(self):
        # Experiment / Timing / Delay Time in seconds
        return self.controller.exp_get('DELAY_TIME')[0]

    @delay_time_s.setter
    def delay_time_s(self, seconds):
        # Experiment / Timing / Delay Time in seconds
        self.controller.exp_set('DELAY_TIME', seconds)

    # helper function:
    def setter_string_to_number(self, string, available_list):
        # also allows for int and checks if it is in the available list as a string
        if type(string)==int:
            if type(available_list[string])!=int:
                return string
        elif string in available_list:
            return available_list.index(string)
        self.logger.warning("{} Is not a valid option in {}".format(string, available_list))
        return -1  # use this to indicate invalid

    @property
    def timing_mode(self):
        number = self.controller.exp_get('TIMING_MODE')[0]
        return self._timing_modes[number]

    @timing_mode.setter
    def timing_mode(self, string):
        number = self.setter_string_to_number(string, self._timing_modes)
        if number>=0:
            self.controller.exp_set('TIMING_MODE', number)

    @property
    def shutter_control(self):
        number = self.controller.exp_get('SHUTTER_CONTROL')[0]
        return self._shutter_controls[number]

    @shutter_control.setter
    def shutter_control(self, string):
        number = self.setter_string_to_number(string, self._shutter_controls)
        if number>=0:
            self.controller.exp_set('SHUTTER_CONTROL', number)

    @property
    def fast_safe(self):
        number = self.controller.exp_get('SYNC_ASYNC')[0]
        return self._fast_safe[number]

    @fast_safe.setter
    def fast_safe(self, string):
        number = self.setter_string_to_number(string, self._fast_safe)
        if number>=0:
            self.controller.exp_set('SYNC_ASYNC', number)


    # Could add
    #edge_trigger


    # Experiment Setup / ROI Setup -------------------------------------------------


#XDIM
#YDIM
#XBINNED ?
#
#
#







if __name__ == "__main__":
    from hyperion import _logger_format
#   from hyperion import Q_
    import hyperion

#    hyperion.set_logfile('winspec_instr.log')
    hyperion.file_logger.setLevel( logging.WARNING )
    hyperion.stream_logger.setLevel( logging.DEBUG )






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

    ws = WinspecInstr(settings = {'port': 'None', 'dummy' : False,
                                   'controller': 'hyperion.controller.princeton.winspec_contr/WinspecContr', 'shutter_controls':['Disabled Closed','Disabled Opened']})
    # ws.initialize() # this is done in the __init__ now

    ws.exposure_time = Q_('300ms')

    ws.central_wav = 300