# -*- coding: utf-8 -*-
"""
==================
Winspec controller
==================

This controller connects to the Winspec software (which in turn is used to control Princeton Instruments spectrometers).


"""
# It has been difficult to get this to work.
# For example, one approach that worked at some point, did not work anymore on another machine or after re-installing anaconda with(out) admin rights.
# I've implemented in the code what I think is the most robust approach, but in the following comments I'll mark down some things to try for potential future troubleshooting.

# win32com (available through conda install pywin32) needs to generate some python code the first time it is run (i.e. on every new machine and after re-installing anaconda).
# It seems like it matters if python is installed with admin rights ("for all users"), or without ("just for me").
# I recommend installing without admin rights (because then you always need to run it with admin rights afterwards).
# This version is developed on an install without admin rights.
# If you run into trouble (for an admin install or otherwise), here are some things you could try or look into.
# There's a difference between win32com.client.Dispatch and win32com.client.gencache.EnsureDispatch.
# Supposedly the second should only be have to run once, to generate to generate the pyton code for the "windows com object".
# I find however, that I need to run it every time in my current configuration.
# Instead of having gencache.EnsureDispatch you could also run "makepy.py" yourself.
# To do that you could run the following line and search in the list for something named like Roper Scientific's WinX/32 ...
# import sys, os.path, win32com.client
# os.system( 'python '+'/'.join(os.path.abspath(win32com.client.__file__).split('\\')[0:-1])+'/makepy.py')
# If the name is correct this line does the same:
# os.system( 'python '+'/'.join(os.path.abspath(win32com.client.__file__).split('\\')[0:-1])+'/makepy.py "Roper Scientific\'s WinX/32 v3.11 Type Library"')

# The stuff above will generate some python code in a location similar to:
# C:\Users\aopheij\AppData\Local\Temp\gen_py\3.7\1A762221-D8BA-11CF-AFC2-508201C10000x0x3x11/
# Those files can be used to infer what methods are available and how to use them

# Regarding opening Winspec before accessing it from python or letting python start Winspec:
# In my tests so far, the order doesn't seem to matter. In both cases python can conrtol Winspec.
# One difference so far is that killing python kernel closes Winspec only when python opened Winspec


import logging
import sys
import os.path
import win32com.client
from hyperion.controller.base_controller import BaseController

# some tests:
# import pythoncom


class WinspecContr(BaseController):
    """ Winspec Controller"""


    def __init__(self, settings = {}):
        """ Init of the class.

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict, optional

        """
        super().__init__(settings)  # mandatory line
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class WinspecController created.')
        self.name = 'Winspec Controller'
        self.ws = None
        self.params = {}
        self.params_exp = {}
        self.params_spt = {}
        self.exp = None
        self._spec_mgr = None
        self.spt = None
        # I don't really understand this stuff, but after a very long search trying many things, this turns out to work for collecting spectral data
        self._variant_array = win32com.client.VARIANT( win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_ARRAY | win32com.client.pythoncom.VT_I4 , [1,2,3,4] )
        

    def initialize(self):
        """ Starts or connects to Winspec software"""
        self.logger.info('Starting or connecting to Winspec')
        try:
            self.ws = win32com.client.gencache.EnsureDispatch("WinX32.Winx32App")
            self.ws.Hide(0) # make Winspec software visible
            self._generate_params()
            self.exp = self._dispatch('WinX32.ExpSetup')
            self._spec_mgr = self._dispatch('WinX32.SpectroObjMgr')
            self.spt = self._spec_mgr.Current
        except win32com.client.pywintypes.com_error:
            self.logger.warning('Can\'t find Winspec. Are you sure it\'s installed?')
            # If Winspec is installed but you run into issues here, have a look at comments t the top of this file.
        self._is_initialized = True     # THIS IS MANDATORY!!
                                        # this is to prevent you to close the device connection if you
                                        # have not initialized it inside a with statement

    def _dispatch(self, winx32_class_name):
        """ Helper function that wraps win32com.client.Dispatch() and catches errors"""
        try:
            return win32com.client.Dispatch(winx32_class_name)
        except win32com.client.pywintypes.com_error:
            self.logger.warning('Winspec is not initialized or unknown class')
            return None

    def _generate_params(self):
        """
        Gets constants from WinX32 com object and stores them in self.params dictionary
        Main reason to do this is so that programmer can use autocomplete (TAB) to view list of parameters.
        Additionally it generates params_exp and params_SPT with all the EXP and SPT parameters respectively.
        """
        self.logger.info("Generating dictionary of parameters")
        _constants = win32com.client.constants.__dict__['__dicts__'][0]
        # Convert these constants to a regular dictionary and only include key-value pairs of which the value is a number (integer)
        self.params = {}
        self.params_exp = {}
        self.params_spt = {}
        self.params_tgc = {}
        self.params_tgp = {}
        self.params_dm = {}
        self.params_other = {}
        for key in _constants:
            if isinstance(_constants[key], int):
                self.params[key] = _constants[key]
                if key[:4] == 'EXP_':
                    self.params_exp[key[4:]] = _constants[key]
                elif key[:4] == 'SPT_':
                    self.params_spt[key[4:]] = _constants[key]
                elif key[:4] == 'TGC_':
                    self.params_tgc[key[4:]] = _constants[key]
                elif key[:4] == 'TGP_':
                    self.params_tgp[key[4:]] = _constants[key]
                elif key[:3] == 'DM_':
                    self.params_dm[key[3:]] = _constants[key]
                else:
                    self.params_other[key] = _constants[key]

    def docfile(self):
        return self._dispatch('WinX32.DocFile')

    def close(self):
        """ Closes the Winspec software.
        Note that this is not necessary."""
        if self._is_initialized:
            self.ws.Quit()

    def finalize(self):
        """   Does nothing, except set _is_initialized to False.
        Closing the Winspec software is not necessary.
        """
        self._is_initialized = False

    def idn(self):
        """ Returns Winspec version

        :return: identification for the device
        :rtype: string
        """
        self.logger.debug('Ask IDN to device.')
        return 'Winspec '+self.ws.Version

    def exp_get(self, msg, *args, **kwargs):
        """ Retrieve WinSpec Experiment parameter
        :param msg: should be a key of self.params_exp
        :type msg: string
        :param *args, **kwargs: Any additional arguments are passed along into the self.exp.GetParam()
        :return: returns Winspec value 
        :rtype: int or tuple ?
        """
        if msg.upper() in self.params_exp:
            return self.exp.GetParam(self.params_exp[msg.upper()], *args, **kwargs)[:-1]
        else:
            self.logger.warning('Unknown EXP parameter: {}'.format(msg))
            return None

    def exp_set(self, msg, value):
        """ Retrieve WinSpec Experiment parameter
        :param msg: should be a key of self.params_exp
        :type msg: string
        :param value: The value to set
        :type value: Depends on parameter, float, what else ????????
        :return: returns errorvalue, 0 if succeeded
        :rtype: int?
        """
        if msg.upper() in self.params_exp:
            return self.exp.SetParam(self.params_exp[msg.upper()], value)
        else:
            self.logger.warning('Unknown EXP parameter: {}'.format(msg))
            return None

    def spt_get(self, msg, *args, **kwargs):
        if msg.upper() in self.params_spt:
            return self.spt.GetParam(self.params_spt[msg.upper()], *args, **kwargs)[:-1]
        else:
            self.logger.warning('Unknown SPT parameter: {}'.format(msg))
            return None

    def spt_set(self, msg, value):
        """ Returns 0 for success, 1 for failure"""
        if msg.upper() in self.params_spt:
            return self.spt.SetParam(self.params_spt[msg.upper()], value)
        else:
            self.logger.warning('Unknown SPT parameter: {}'.format(msg))
            return None

    # def query(self, msg):
    #     """ writes into the device msg
    #
    #     :param msg: command to write into the device port
    #     :type msg: string
    #     """
    #     self.logger.debug('Writing into the example device:{}'.format(msg))
    #     self.write(msg)
    #     ans = self.read()
    #     return ans
    #
    # def read(self):
    #     """ Fake read that returns always the value in the dictionary FAKE RESULTS.
    #
    #     :return: fake result
    #     :rtype: string
    #     """
    #     return self.FAKE_RESPONSES['A']
    #
    # def write(self, msg):
    #     """ Writes into the device
    #     :param msg: message to be written in the device port
    #     :type msg: string
    #     """
    #     self.logger.debug('Writing into the device:{}'.format(msg))


    @property
    def amplitude(self):
        """ Gets the amplitude value.

        :getter:
        :return: amplitude value in Volts
        :rtype: float

        For example, to use the getter you can do the following

        >>> with DummyOutputController() as dev:
        >>>    dev.initialize('COM10')
        >>>    dev.amplitude
        1

        :setter:
        :param value: value for the amplitude to set in Volts
        :type value: float

        For example, using the setter looks like this:

        >>> with DummyOutputController() as dev:
        >>>    dev.initialize('COM10')
        >>>    dev.amplitude = 5
        >>>    dev.amplitude
        5


        """
        self.logger.debug('Getting the amplitude.')
        return self._amplitude

    @amplitude.setter
    def amplitude(self, value):
        # would be nice to add a way to check that the value is within the limits of the device.
        if self._amplitude != value:
            self.logger.info('Setting the amplitude to {}'.format(value))
            self._amplitude = value
            self.write('A{}'.format(value))
        else:
            self.logger.info('The amplitude is already {}. Not changing the value in the device.'.format(value))


class WinspecContrDummy(WinspecContr):
    """
    Example Controller Dummy
    ========================

    A dummy version of the Example Controller.

    In essence we have the same methods and we re-write the query to answer something meaningful but
    without connecting to the real device.

    """


    def query(self, msg):
        """ writes into the device msg

        :param msg: command to write into the device port
        :type msg: string
        """
        self.logger.debug('Writing into the dummy device:{}'.format(msg))
        ans = 'A general dummy answer'
        return ans



if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    dummy = False  # change this to false to work with the real device in the COM specified below.

    if dummy:
        my_class = WinspecControllerDummy
    else:
        my_class = WinspecContr

#    with my_class(settings = {'dummy':dummy}) as dev:
#        dev.initialize()
#        print(dev.idn())
#        print('GRATINGSPERTURRET: {}'.format(dev.spt_get('GRATINGSPERTURRET')))
#        print('INST_GRAT_GROOVES 0: {}'.format(dev.spt_get('INST_GRAT_GROOVES',0)))
#        print('INST_GRAT_GROOVES 1: {}'.format(dev.spt_get('INST_GRAT_GROOVES',1)))
#        print('INST_GRAT_GROOVES 2: {}'.format(dev.spt_get('INST_GRAT_GROOVES',2)))
#        print('CUR_GRATING: {}'.format(dev.spt_get('CUR_GRATING')))
#        print('INST_CUR_GRAT_NUM: {}'.format(dev.spt_get('INST_CUR_GRAT_NUM')))
#        print('CUR_POSITION: {}'.format(dev.spt_get('CUR_POSITION')))                  <<  in nm
#        print('ACTIVE_GRAT_POS: {}'.format(dev.spt_get('ACTIVE_GRAT_POS')))            <<  in ???
#        print('INST_CUR_GRAT_POS: {}'.format(dev.spt_get('INST_CUR_GRAT_POS')))
#        dev.exp_set('EXPOSURETIME',2.0)
#        print('EXPOSURETIME: {}'.format(dev.exp_get('EXPOSURETIME')))
#        doc = dev.docfile()
#        dev.exp.Start(doc)
#        #dev.close() # Note that closeing Winspec is not necessary. Especially for testing it's quicker to leave it open


    ws = WinspecContr()
    ws.initialize()


    from hyperion.view.general_worker import WorkThread

    thr = WorkThread(ws.spt.Move)






"""
Comment

EXP_EXPOSURE seems to contain the exposuretime in seconds, but it appears that it is not always immediately updated, I recommend using EXP_EXPOSURETIME and EXP_EXPOSURETIME_UNITS instead

"""