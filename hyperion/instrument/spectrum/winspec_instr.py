# -*- coding: utf-8 -*-
"""
==================
Winspec Instrument
==================

Aron Opheij, TU Delft 2019

IMPORTANT REMARK:
In the current implementation it is not possible to use this instrument in threads.

Tips for finding new functionality:

Once you have an WinspecInstr object named ws, try the following things:
This will list all keywords:
[key for key in ws.controller.params]
There are shorter lists with only experiment (EXP) and spectrograph (SPT) commands:
[key for key in ws.controller.params_exp]       # note that prefix EXP_ is removed
[key for key in ws.controller.params_spt]       # note that prefix SPT_ is removed
To filter in those you could try:
[key for key in ws.controller.params_exp if 'EXPOSURE' in key]
[key for key in ws.controller.params_spt if 'GROOVES' in key]

To request the value for a keyword try:
ws.controller.exp_get('EXPOSURETIME')
ws.controller.exp_get('GRAT_GROOVES')

"""
import threading
from hyperion import logging
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur, Q_
from hyperion import root_dir
# from hyperion.view.general_worker import WorkThread
import time
import os
import yaml
# import numpy as np      # I'm having issues with numpy on the computer I'm developing, so I disable it temporarily and modified take_spectrum not to depend on it

class WinspecInstr(BaseInstrument):
    """ Winspec Instrument

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict

        Information for settings dict:
        To overwrite certain possible values add a key conaining a list of possible values to the settings dict:
        For example, if your WinSpec does not have 'Normal' mod in shutter_controls, add this key:
        shutter_controls:
          - Closed
          - Opened

    """

    def __init__(self, settings):                   # not specifying a default value for settings is less confusing for novice users
        # don't place the docstring here but above in the class definition
        super().__init__(settings)                  # mandatory line
        self.logger = logging.getLogger(__name__)   # mandatory line
        self.logger.info('Class ExampleInstrument created.')
        self.settings = settings
        self.default_name = 'temp.SPE'

        self._timing_modes = self._remove_unavailable('timing_modes', [0, 'Free Run', 2, 'External Sync'])
        self._shutter_controls = self._remove_unavailable('shutter_controls', [0, 'Normal', 'Closed', 'Opened'])
        self._fast_safe = self._remove_unavailable('fast_safe', ['Fast', 'Safe'])
        self._ccd = self._remove_unavailable('ccd', ['Full', 'ROI'])
        self._autosave = self._remove_unavailable('autosave', ['Ask', 'Auto', 'No'])

        if 'horz_width_multiple' in self.settings:
            self._horz_width_multiple = self.settings['horz_width_multiple']  # This parameter specifies if camera requires horizontal range of certain interval
        else:
            self._horz_width_multiple = 1   # This parameter specifies if camera requires horizontal range of certain interval

        self.initialize()   # ! required to do this in the __init__

        # self._is_acquiring = False
        self._is_moving = False

        self.frame = []

        # bug fix:
        self.ccd = 'Full'
        self.controller.xdim = self.controller.exp_get('XDIM')
        self.controller.ydim = self.controller.exp_get('YDIM')
        self.ccd = 'ROI'

        # !!!!!   THREADING WILL NOT WORK IN THE CURRENT IMPLENTATION
        #         I have some ideas to try, but I'll first finish an operational version without threading

        # self.move_grating_thread = threading.Thread(target = self._move_grating)
        # self.move_grating_thread = WorkThread(self._move_grating)

    def initialize(self):
        """ Starts the connection to the Winspec softare and retrieves parameters. """
        self.logger.info('Opening connection to device.')
        self.controller.initialize()
        # self._gain = self.gain
        self._exposure_time = self.exposure_time
        # self._accums = self.accumulations
        # self._target_temp = self.target_temp
        # # Get grating info:
        self.gratings_grooves = []  # list to hold the grooves/mm for the different gratings
        self.gratings_blaze_name = []  # list to hold the blaze text
        # self.gratings_blaze = []  # list to hold numeric blaze wavelength value
        self.number_of_gratings = self.controller.spt_get('GRATINGSPERTURRET')[0]
        # this seems to be the same value:   self.controller.spt_get('INST_CUR_GRAT_NUM')[0]
        for k in range(self.number_of_gratings):
            self.gratings_grooves.append(self.controller.spt_get('INST_GRAT_GROOVES', k)[0])
            text = self.controller.spt_get('GRAT_USERNAME', k + 1)[0]
            self.gratings_blaze_name.append(text)
            # # try to interpret the blaze wavelength:
            # self.gratings_blaze.append(int(''.join(filter(str.isdigit, text))))

        # # To prevent error when trying to save or aquire without
        # self.doc = self.controller.docfile()

        self.logger.info(
            '{} gratings found. grooves/mm: {}, blaze: {}'.format(self.number_of_gratings, self.gratings_grooves,
                                                                  self.gratings_blaze_name))

        filename = os.path.join(root_dir, 'instrument', 'spectrum', 'winspec_config_irina.yml')

        with open(filename, 'r') as f:
            self.config_settings = yaml.load(f, Loader=yaml.FullLoader)

    def _move_grating(self):
        """ Low level function to move grating after specifying the new position. """
        self._is_moving = True
        self.controller.spt.Move()
        self._is_moving = False

    def finalize(self):
        """ Mandatory function. Get's called when exiting a 'with' statement."""
        self.logger.info('Closing connection to device.')

        self.controller.finalize()

    def _remove_unavailable(self, settings_key, default_options_list):
        """
        Low level function to remove items from options_list that don't occur in settings_list and replace with their index.
        :param settings_key: the key name in the settings dict
        :param default_options_list: list of default values
        :return: corrected list
        """
        if settings_key in self.settings:
            for index, value in enumerate(default_options_list):
                if value not in self.settings[settings_key]:
                    default_options_list[index] = index
        return default_options_list

    def idn(self):
        """
        Identify command

        :return: Identification string of the device.
        :rtype: string
        """
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn()

    def start_acquiring(self, name=None):
        """
        Starts acquisition of spectrum. Does not wait for it to finish.
        If name is specified. The last spectrum in WinSpec is closed and a new spectrum with the specified name is created.
        If name is None (DEFAULT) the current spectrum will be overwritten.

        :param name: Full path to file to store. Or None, for using default.
        :type name: string
        """

        if name==None:
            # name=self.default_name
            if hasattr(self,'doc'):
                try:
                    self.doc.Close()
                except:
                    self.logger.warning('Winspec: Failed to close doc')
            self.doc = self.controller.docfile()
        else:
            if hasattr(self,'doc'):
                try:
                    self.doc.Close()
                except:
                    self.logger.warning('Winspec: Failed to close doc')
            self.filename = name
            self.doc = self.controller.docfile()
        self.controller.exp.Start(self.doc)

    @property
    def is_acquiring(self):
        """ Read only property that indicates if WinSpec is still busy acquiring. Returns True or False."""
        return self.controller.exp_get('RUNNING')[0]==1

    def nm_axis(self):
        """ Returns list with nm axis values of last collected spectrum."""
        # Retrieve nm axis in cumbersome way. (There must be a better/faster way,  but haven't found it yet)
        wav = []
        cal = self.doc.GetCalibration()
        for index in range(len(self.frame)):
            wav.append(cal.Lambda(index+1))
        return wav

    def collect_spectrum_alt(self):
        thread = threading.Thread(self.waitforacquiring())
        thread.start()
        thread.join()
        self.frame = self.doc.GetFrame(1,self.controller._variant_array)
        # return frame                      # direct tuple of tuples
        # return np.asarray(frame)          # np approach
        if len(self.frame[0])==1:
            return [col[0] for col in self.frame] # convert to 1D list
        else:
            return [list(col) for col in self.frame] # convert to nested list

    def start_focus(self):

        if hasattr(self, 'doc'):
            self.doc.Close()
        self.doc = self.controller.docfile()

        self.controller.exp.StartFocus(self.doc)

    def stop_focus(self):

        self.controller.exp.Stop()



    def collect_spectrum(self, wait=True, sleeptime=False):
        """
        | Retrieves the last acquired spectrum from Winspec.
        | **Pay attention: you need to extra sleeps if you are autosaving with Winspec**
        | If you are not using the Autosave option, you have to put sleeptime to False.

        :param wait: If wait is True (DEFAULT) it will wait for WinSpec to finish collecting data.
        :type wait: bool

        :param sleeptime: Sleeptime adds some sleeps to make sure Winspec has enough time to Autosave ascii images
        :type sleeptime: bool

        :return: list or nested list
        """
        if wait:
            while self.is_acquiring:
                if sleeptime:
                    time.sleep(1)       #use this one if you want to autosave images
                else:
                    time.sleep(0.1)     #this is enough if you autosave spectra
                self.logger.debug("acquiring? {}".format(self.is_acquiring))

            #this sleep is to save an image as ASCII, that takes quite some time,
            # and Winspec breaks if you dont give that time
            if sleeptime:
                time.sleep(2)

        self.frame = self.doc.GetFrame(1,self.controller._variant_array)
        # return frame                      # direct tuple of tuples
        # return np.asarray(frame)          # np approach
        if len(self.frame[0])==1:
            return [col[0] for col in self.frame] # convert to 1D list
        else:
            return [list(col) for col in self.frame] # convert to nested list

    def waitforacquiring(self):
        while self.is_acquiring == True:
            time.sleep(0.1)

    def take_spectrum(self, name=None, sleeptime=True):
        """
        Acquire spectrum, wait for data and collect it.
        Performs start_acquiring(name), followed by collect_spectrum(True).
        See those methods for more details.
        """

        self.start_acquiring(name)
        return self.collect_spectrum(True, sleeptime)

    def take_spectrum_alt(self, name=None, sleeptime=True):
        """
        Acquire spectrum, wait for data and collect it.
        Performs start_acquiring(name), followed by collect_spectrum(True).
        See those methods for more details.
        """

        self.start_acquiring(name)
        return self.collect_spectrum_alt()

    def saveas(self, filename):
        """
        Make WinSpec save current spectrum to disk (in format specified in WinSpec).
        Note: I's also possible to use autosave function of WinSpec:  self.autosave = 'Auto'
        :param filename: The full path to save the file. If None specified it used default name.
        :type filename: string
        :return:
        """
        if filename is None:
            self.doc.Save()
        else:
            self.doc.SaveAs(filename)

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
        """
        attribute: Grating number (starts at 1)

        getter: Returns current grating number
        setter: Switched to new grating. Waits for it to complete.
        type: int
        """
        return self.controller.spt_get('CUR_GRATING')[0]

    @grating.setter
    def grating(self, number):
        current = self.controller.spt_get('CUR_GRATING')[0]
        if 0 < number <= self.number_of_gratings:
            if number == current:
                self.logger.debug('Grating {} already in place'.format(number))
            else:
                self.controller.spt_set('NEW_GRATING', number)
                self.logger.info('changing grating from {} to {} ...'.format(current, number))
                self.controller.spt.Move()
                self.logger.info('finished changing grating')
        else:
            self.logger.warning('{} is invalid grating number (1-{})'.format(number, self.number_of_gratings))

    @property
    def central_nm(self):
        """
        attribute: Central position of grating in nm

        getter: Returns current central position of grating
        setter: Rotates grating to new nm position. Waits for it to complete.
        type: float
        """

        return self.controller.spt_get('CUR_POSITION')[0]

    @central_nm.setter
    def central_nm(self, nanometers):
        current = self.controller.spt_get('CUR_POSITION')[0]
        if nanometers == current:
            self.logger.debug('Grating already at {}nm'.format(nanometers))
        else:
            self.controller.spt_set('NEW_POSITION', nanometers)
            self.logger.info('moving grating from {} to {} ...'.format(current, nanometers))
            self.controller.spt.Move()
            self.logger.info('finished moving grating')
            # self.move_grating_thread.start()

    # Hardware settings:   ---------------------------------------------------------------------------------------

    @property
    def current_temp(self):
        """
        read-only attribute: Temperature measured by Winspec in degrees Celcius.

        getter: Returns the Temperature measured by Winspec.
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
        attribute: ADC Gain value.

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
    def ccd(self):
        """
        attribute: CCD Readout mode.
        default possible values: 'Full' 'ROI'
        type: str
        """
        number = ws.controller.exp_get('USEROI')[0]
        return self._ccd[number]

    @ccd.setter
    def ccd(self, string):
        number = self._setter_string_to_number(string, self._ccd)
        if number>=0:
            self.controller.exp_set('USEROI', number)

    @property
    def spec_mode(self):
        """
        attribute: True for Spectroscopy Mode, False for Imaging Mode
        :type: bool
        """
        return ws.controller.exp_get('ROIMODE')[0]==1

    @spec_mode.setter
    def spec_mode(self, value):
        ws.controller.exp_set('ROIMODE', value!=0)

    def getROI(self):
        """
        Retrieve current Region Of Interest.
        :return: list containing [top, bottom, v_binsize, left, right, h_binsize]
        """
        # return top, bottom, v_group, left, right, h_group
        self._roi = self.controller.exp.GetROI(1)
        r = self._roi.Get()    # returns tuple: (top, left, bottom, right, h_group, v_group)
        return [r[0], r[2], r[5], r[1], r[3], r[4]]

    def setROI(self, top='full_im', bottom=None, v_binsize=None, left=1, right=None, h_binsize=1):
        """
        Note for the new camera (the 1024x1024 one) the  horizontal range needs to be a multiple of 4 pixels.
        If the users input fails this criterium, this method will expand the range.
        Also the v_group and h_group, need to fit in the specified range. If the input fails, a suitable value will be used. And the user will be warned.
        :param top: Top-pixel number (inclusive) (integer starting at 1). Alternatively 'full_im' (=DEFAULT) of 'full_spec' can be use.
        :param bottom: Bottom-pixel number (integer). DEFAULT value is bottom of chip
        :param v_binsize: Vertical bin-size in number of pixels (integer). None sums from 'top' to 'bottom'. DEFAULT: None
        :param left: Left-pixel number (inclusive) (integer starting from 1). DEFAULT is 1
        :param right: Right-pixel number (integer). DEFAULT is rightmost pixel
        :param h_binsize: Horizontal binning (integer), DEFAULT is 1
        :return:

        Examples:
        setROI('full_im')   returns the full CCD
        setROI('full_spec') returns the full CCD, summed vertically to result in 1D array
        setROI(51)          sums from pixel 51 to the bottom
        setROI(51, 70)      sums vertically from pixel 51 to 70
        setROI(51, 70, 20)  sums vertically from pixel 51 to 70
        setROI(41, 60, 5)   result in 4 bins of 5 pixles
        setROI(41, 60, 1)   no binning, result will be 20 pixels high
        setROI(41, 60, None, 101, 601)      modify horizontal range
        setROI(41, 60, None, 101, 601, 10)  apply horizontal binning of 10 pixels (result will be 50 datapoints wide)
        """
        self.logger.debug('right{}, left{}'.format(right,left))

        if bottom is None:
            bottom = self.controller.ydim[0]

        if right is None:
            right = self.controller.xdim[0]

        if type(top) is str:
            if top=='full_im':
                top = 1
                bottom = self.controller.ydim[0]
                v_binsize = 1
            elif top != 'full_spec':
                self.logger.warning('unknown command {}, using full_spec ')
                top = 'full_spec'
            if top =='full_spec':
                top = 1
                bottom = self.controller.ydim[0]
                v_binsize = 1024


        # if v_group is not specified assume summing vertically from top to bottom:
        if v_binsize is None:
            v_binsize = bottom - (top - 1)

        self.logger.debug("bottom{}, top{}".format(bottom, top))
        self.logger.debug("vertical binsize: {}".format(v_binsize))

        # Some basic range corrections:
        # revert top/bottom and left/right if they're inverted
        if bottom < top:
            temp = top
            top = bottom
            bottom = temp
        if right < left:
            temp = left
            left = right
            right = temp
        # apply basic limits of the CCD
        if top < 1: top = 1
        if left < 1: left = 1
        if bottom > self.controller.ydim[0]: bottom = self.controller.ydim[0]
        if right > self.controller.xdim[0]: right = self.controller.xdim[0]

        # if bottom < top:
        #     if top < self.controller.ydim-1:
        #         bottom = top
        #     else:
        #         top = bottom
        # if right < left:
        #     if left < self.controller.xdim-1:
        #         right = left + 1
        #     else:
        #         left = right - 1
        # if not 0 < top <= bottom: self.logger.error('top value invalid')
        # if not top <= bottom <= self.controller.ydim: self.logger.error('bottom value invalid')
        # if not 0 < left <= right: self.logger.error('left value invalid')
        # if not left <= right <= self.controller.xdim: self.logger.error('right value invalid')

        pix = right - (left - 1)
        self.logger.debug('right{}, left{}'.format(right,left))
        if self._horz_width_multiple > 1:
            # note: I've generalized this from 4 to self._horz_width_multiple
            # Check if horizontal range is multiple of 4 pixels. Expand if required.
            # This is required for the new spectrometer (the one with 1024x1024 pixels)
            self.logger.debug("pix{}, _horz_width_multiple{}".format(pix, self._horz_width_multiple))
            if pix%self._horz_width_multiple:
                self.logger.debug('pix%self._horz_width_multiple is true')
                ad = self._horz_width_multiple-pix+self._horz_width_multiple*int(pix/self._horz_width_multiple) # number of pixels to add (1,2,3)
                self.logger.debug('ad: {}'.format(ad))
                while ad:
                    if ad and right < self.controller.xdim:
                        right += 1
                        ad -= 1
                    if ad and left>1:
                        left -= 1
                        ad -= 1
            self.logger.warning('horizontal range is not muliple of {}: expanded to [{}-{}]'.format(self._horz_width_multiple, left, right))
            pix = right - (left - 1)

        # if necessary correct h_group to fit horizontal range:
        new_h = h_binsize
        if pix%h_binsize:
            new_h = h_binsize - ((h_binsize - 1) % self._horz_width_multiple) + (self._horz_width_multiple - 1)   # ceil to nearest multiple of self._horz_width_multiple
            while pix%new_h:        # note: this loop should end at the latest when new_h == 1
                new_h -= 1

        if new_h != h_binsize:
            self.logger.warning('h_group {} does not fit in horizontal range of [{}-{}]: changing to: {}'.format(h_binsize, left, right, h_new))
            h_binsize = h_new

        new_v = v_binsize
        pix = bottom - (top-1)
        if pix%v_binsize:
            new_v = v_binsize + 1
            while pix%new_v:        # note: this loop should end at the latest when new_v == 1
                new_v -= 1

        if new_v != v_binsize:
            self.logger.warning('v_group {} does not fit in vertical range of [{}-{}]: changing to: {}'.format(v_binsize, top, bottom, v_new))
            v_binsize = v_new

        # set the new ROI:
        self._roi = self.controller.exp.GetROI(1)                       # get ROI object
        self._roi.Set(top, left, bottom, right, h_binsize, v_binsize)       # put in the new values
        self.controller.exp.ClearROIs()                                 # clear ROIs in WinsSpec
        self.controller.exp.SetROI(self._roi)                           # set the ROI object in WinSpec
        self.ccd = 'ROI'                                                # switch from Full Chip to Region Of Interest mode

        # I'm not sure if I need to do something with ROIMODE (0= Imaging Mode,   1= Spectroscopy Mode)

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

    @property
    def exposure_time_alt(self):
        exp_value=self.controller.exp_get('EXPOSURE')[0]
        self._exposure_time = exp_value * ur('s')

        return self._exposure_time

    @exposure_time_alt.setter
    def exposure_time_alt(self, value):
        if type(value) is not type(Q_('s')):
            self.logger.error('exposure_time should be Pint quantity')
        if value.dimensionality != Q_('s').dimensionality:
            self.logger.error('exposure_time should be Pint quantity with unit of time')

        else:
            if value.units == 'millisecond':
                exp_value = value.m / 1000
            elif value.units == 'second':
                exp_value = value.m
            elif value.units == 'minute':
                exp_value = value.m * 60

        self.controller.exp_set('EXPOSURE', exp_value)

    @exposure_time.setter
    def exposure_time(self, value,alt=False):
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
        """
        attribute: Background Subtraction

        getter: Returns if Background Subtraction is enabled.
        setter: Sets Background Subtraction.
        type: bool
        """
        return self.controller.exp_get('BBACKSUBTRACT')[0] == 1     # turn it into bool

    @bg_subtract.setter
    def bg_subtract(self, value):
        self.controller.exp_set('BBACKSUBTRACT',value!=0)       # !=0  forces it to be bool

    @property
    def bg_file(self):
        """
        attribute: Full path to Background File
        Note: it does not check if the file exists or is it is a valid file.
        type: string
        """
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

    # Experiment / Data File settings: ----------------------------------
    @property
    def confirm_overwrite(self):
        """
        attribute: Confirm Overwrite File
        type: bool
        """
        return self.controller.exp_get('OVERWRITECONFIRM')[0] == 1  # turn it into bool

    @confirm_overwrite.setter
    def confirm_overwrite(self, value):
        self.controller.exp_set('OVERWRITECONFIRM',value!=0)       # !=0  forces it to be bool

    @property
    def filename(self):
        """
        Note that this needs to be set before aqcuiring a spectrum.
        If you want to store the SPE files as well, the best approach is to make sure
          self.autosave = 'Auto'

        use take_spectrum('new_name.SPE')
        :return:
        """
        return self.controller.exp_get('DATFILENAME')[0]

    @filename.setter
    def filename(self, string):
        self.controller.exp_set('DATFILENAME', string)

    @property
    def autosave(self):
        """
        attribute: Auto-save and prompts:
        default possible values: 'Ask', 'Auto', 'No'
        type: str
        """
        number = self.controller.exp_get('AUTOSAVE')[0] - 1
        return self._autosave[number]

    @autosave.setter
    def autosave(self, string):
        number = self._setter_string_to_number(string, self._autosave)
        if number>=0:
            self.controller.exp_set('AUTOSAVE', number + 1)

    # Experiment / Timing settings: ----------------------------------

    @property
    def delay_time_s(self):
        """
        attribute: The delay time under Experiment/Timing in seconds
        type: float
        """
        # Experiment / Timing / Delay Time in seconds
        return self.controller.exp_get('DELAY_TIME')[0]

    @delay_time_s.setter
    def delay_time_s(self, seconds):
        # Experiment / Timing / Delay Time in seconds
        self.controller.exp_set('DELAY_TIME', seconds)

    def _setter_string_to_number(self, string, available_list):
        """
        Low level helper method that returns index of string in available_list.
        :param string: string to find
        :param available_list: list of possible strings
        :return: The index of the string if found, -1 otherwise (to indicate not found)
        """
        if type(string)==int:
            if type(available_list[string])!=int:
                return string
        elif string in available_list:
            return available_list.index(string)
        self.logger.warning("{} Is not a valid option in {}".format(string, available_list))
        return -1  # use this to indicate invalid

    @property
    def timing_mode(self):
        """
        attribute: Timing Mode
        default possible values: 'Normal', 'Closed', 'Opened'
        type: str
        """
        number = self.controller.exp_get('TIMING_MODE')[0]
        return self._timing_modes[number]

    @timing_mode.setter
    def timing_mode(self, string):
        number = self._setter_string_to_number(string, self._timing_modes)
        if number>=0:
            self.controller.exp_set('TIMING_MODE', number)

    @property
    def shutter_control(self):
        """
        attribute: Shutter Control
        default possible values: ? , 'Free Run', ? , 'External Sync'
        type: str
        """
        number = self.controller.exp_get('SHUTTER_CONTROL')[0]
        return self._shutter_controls[number]

    @shutter_control.setter
    def shutter_control(self, string):
        number = self._setter_string_to_number(string, self._shutter_controls)
        if number>=0:
            self.controller.exp_set('SHUTTER_CONTROL', number)

    @property
    def fast_safe(self):
        """
        attribute: Fast or Safe mode in Experiment/Timing
        default possible values: 'Fast', 'Safe'
        type: str
        """
        number = self.controller.exp_get('SYNC_ASYNC')[0]
        return self._fast_safe[number]

    @fast_safe.setter
    def fast_safe(self, string):
        number = self._setter_string_to_number(string, self._fast_safe)
        if number>=0:
            self.controller.exp_set('SYNC_ASYNC', number)

    # Could add
    #edge_trigger

    # Experiment / Processes settings; ------------------------------------------------
    @property
    def ascii_output(self):
        """
        attribute: Also save as ASCII file (next to SPE)

        getter: Returns if ASCII save is enabled.
        setter: Sets saving as ASCII file.
        type: bool
        """
        return self.controller.exp_get('ASCIIOUTPUTFILE')[0] == 1     # turn it into bool

    @ascii_output.setter
    def ascii_output(self, value):
        self.controller.exp_set('ASCIIOUTPUTFILE',value!=0)       # !=0  forces it to be bool


    def configure_settings(self):
        #self.logger.debug(str(self.idn()))

        self.logger.info('Put settings as written down in instrument config file')

        self.display_rotate = self.config_settings['display']['rotate']
        self.display_reverse = self.config_settings['display']['reverse']
        self.display_flip = self.config_settings['display']['flip']
        self.logger.debug('display_rotate: ' +  str(self.display_rotate))
        self.logger.debug('display_reverse: ' + str(self.display_reverse))
        self.logger.debug('display_flip: ' + str(self.display_flip))

        self.logger.debug('Target temperature: ' + str(self.target_temp))
        self.logger.debug('Current temperature: ' + str(self.current_temp))

        self.confirm_overwrite = self.config_settings['data_file']['confirm_overwrite']
        self.autosave = self.config_settings['data_file']['autosave']
        self.logger.debug('Data file confirm overwrite: ' + str(self.confirm_overwrite))
        self.logger.debug('Data file: ' + str(self.autosave))

        self.logger.debug('Current controller gain: ' + str(self.gain))

        self.timing_mode = self.config_settings['timing']['mode']
        self.fast_safe = self.config_settings['timing']['fast_safe']
        self.delay_time_s = self.config_settings['timing']['delay_time_s']
        self.logger.debug('Timing mode: ' + str(self.timing_mode))
        self.logger.debug('Timing on : ' + str(self.fast_safe))
        self.logger.debug('Timing delay time: ' + str(self.delay_time_s) + 's')

        self.ascii_output = self.config_settings['ascii_file']
        self.logger.debug('Saving ascii file: ' + str(self.ascii_output)) #this is correct if you look at Winspec, but wrong here!!!





if __name__ == "__main__":
    #logging.stream_level = logging.INFO



    settings = {'port': 'None', 'dummy': False,
                'controller': 'hyperion.controller.princeton.winspec_contr/WinspecContr'}

    settings_irina = {'port': 'None', 'dummy': False,
                'controller': 'hyperion.controller.princeton.winspec_contr/WinspecContr',
                'shutter_controls': ['Closed', 'Opened'], 'horz_width_multiple': 4}


    ws = WinspecInstr(settings)
    d = ws.take_spectrum()
    print(d)




    # ws.configure_settings()

    test_everything = False

    if test_everything:
        print(ws.idn())
        print('\nHardware Display settings:')
        print('display_rotate = ', ws.display_rotate)
        print('display_reverse = ', ws.display_reverse)
        print('display_flip = ', ws.display_flip)

        print('\nHardware Temperature settings:')
        print('target_temp = ', ws.target_temp)
        print('current_temp = ', ws.current_temp, '  (read-only property)')
        print('temp_locked = ', ws.temp_locked, '  (read-only property)')

        print('\nExperiment Settings:')
        print('Data File        filename = ', ws.filename)
        ws.confirm_overwrite = False
        print('Data File        confim_overwrite = ', ws.confirm_overwrite)
        ws.autosave = 'Auto'
        print('Data File        autosave = ', ws.autosave)
        print('ADC              gain = ', ws.gain)
        print('Timing           timing_mode = ', ws.timing_mode)
        print('Timing           shutter_control = ', ws.shutter_control)
        print('Timing           fast_safe = ', ws.fast_safe)
        print('Timing           delay_time_s = ', ws.delay_time_s)
        ws.bg_subtract = False
        print('Data Corrections bg_subtract = ', ws.bg_subtract)
        print('Data Corrections bg_file = ', ws.bg_file)
        ws.ascii_output = True
        print('Saving copy of data in Ascii file = ', ws.ascii_output)

        ws.exposure_time = Q_('3s')
        print('Main             exposure_time = ', ws.exposure_time)
        ws.ccd = 'ROI'
        print('Main             ccd = ', ws.ccd)
        print('Main             accumulations = ', ws.accumulations)
        print('ROI              spec_mode = ', ws.spec_mode)

        print('\nROI = ', ws.getROI())

        print('\nGrating Settings:')
        print(ws.number_of_gratings, ' gratings found')
        for k in range(ws.number_of_gratings):
            print(k+1, ':  ', ws.gratings_grooves[k], 'gr/mm  ',  ws.gratings_blaze_name[k])

        print('current grating = ', ws.grating)
        print('Switching grating ...')
        if ws.grating == 2:
            ws.grating = 1
        elif ws.grating == 1:
            ws.grating = 2

        print('central_nm = ', ws.central_nm)
        print('Changing grating central nm ...')
        if ws.central_nm < 450:
            ws.central = 500
        if ws.central_nm > 450:
            ws.central = 400

    print('Taking spectrum ...')
    counts = ws.take_spectrum('image')
    nm = ws.nm_axis()
    #print(nm,counts)

    ws.shutter_control = 'Closed'

    ws.central_wav = 300



# frame = ws.doc.GetFrame(1,ws.controller._variant_array)
