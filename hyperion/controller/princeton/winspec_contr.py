# -*- coding: utf-8 -*-
"""
==================
Winspec controller
==================

This controller connects to the Winspec software (which in turn is used to control Princeton Instruments spectrometers).

Note: this controller detects if PyQt5 module is laoded and if so it will take precautions to for threading.

.. seealso::
    :doc:`../instrument/winspec_instr`

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
from hyperion import logging
import sys
if sys.maxsize > 2**32:
    print('64 bit')
else:
    import win32com.client
from hyperion.controller.base_controller import BaseController

import pythoncom  # required for threading support

# This controller should detect if PyQt5 is used (or other threading packages) and automatically start in
# "threading mode", but if it doesn't and there are threading issues (e.g. an error mentioning that CoInitialize has
# not been called), you could force it to use threading by passing this settings parameter: force_threading_mode = True


class WinspecContr(BaseController):
    """ Winspec Controller.
        This class contains low level functionality for communicating with Winspec software.
        Higher level functionality is in the instrument.

        Note:
        There is an issue between win32com (used to control the Winspec software) and threading. A workaround is
        implemented in this controller and is applied automatically if it detects that the PyQt5 module is loaded. To
        force it to use this threading compatible mode add the key 'force_threading_mode' to the config dictionary and
        set it True. To force it not to use this mode set it False. (Omit it or set it to None for automatic detection)

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict

    """
    def __init__(self, settings={}):                # note: usually it's not recommended to specify default value, but here I did because it's an empty dict
        # don't place the docstring here but above in the class definition
        super().__init__(settings)                  # mandatory line
        self.logger = logging.getLogger(__name__)   # mandatory line
        self.logger.info('Class WinspecController created.')

        # force_threading_mode:
        #   True    Force it to use threading mode
        #   None    Automatic (default behaviour)
        #   False   Force it to not use threading mode
        if 'force_threading_mode' in settings:
            self._force_threading = settings['force_threading_mode']
        else:
            self._force_threading = None
        self._threading_mode = None

        # pythoncom.CoInitialize()                    # added this line for threading
        self.name = 'Winspec Controller'
        # self.ws = None
        self.params = {}
        self.params_exp = {}
        self.params_spt = {}
        # self.exp = None
        # self._spec_mgr = None
        # self.spt = None
        # I don't really understand this stuff, but after a very long search trying many things, this turns out to work for collecting spectral data
        self._variant_array = win32com.client.VARIANT( win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_ARRAY | win32com.client.pythoncom.VT_I4 , [1,2,3,4] )

    def initialize(self):
        self._is_initialized = False
        if self._force_threading is True or (self._force_threading is None and 'PyQt5' in sys.modules):
            # if _force_threading is None and PyQt5 is detected
            # if _force_threading is True
            self.logger.info('Winspec in threading mode ' + ['(automatic)', '(forced)'][self._force_threading is True])
            from hyperion.view.general_worker import WorkThread
            from time import sleep
            init_thread = WorkThread(self.__initialize_in_thread)
            self._busy_with_thread = True
            init_thread.start()
            timeout_count = 50  # wait 5 seconds before spitting out warnings
            while self._busy_with_thread:
                sleep(.2)
                if timeout_count<=0:
                    self.logger.warning('Waiting for Winspec')
            init_thread.quit()
            self._threading_mode = True
        else:
            # if _force_threading is False
            # if _force_threading is None and PyQt5 is not detected
            self.logger.info('Winspec NOT in threading mode ' + ['(forced)', '(automatic)'][self._force_threading is None])
            self._threading_mode = False
            self.__initialize_without_threading_support()

        self._generate_params()
        self._is_initialized = True     # THIS IS MANDATORY!!
                                        # this is to prevent you to close the device connection if you
                                        # have not initialized it inside a with statement

        # self.xdim = self.exp_get('XDIM')[0]
        # self.ydim = self.exp_get('YDIM')[0]
        self.xdim = self.exp_get('XDIMDET')[0]
        self.ydim = self.exp_get('YDIMDET')[0]

    def __initialize_in_thread(self):
        """
        Mandatory function. Starts or connects to Winspec software
        """
        self.logger.info('Starting Winspec in threading compatible mode')
        try:
            pythoncom.CoInitialize()
            ws_app = win32com.client.Dispatch("WinX32.Winx32App")
            # ws_app = win32com.client.Dispatch("WinX32.Winx32App")
            self._ws_app_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, ws_app)
            # com_object = win32com.client.gencache.EnsureDispatch("WinX32.Winx32App")
            # self.ws = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, com_object)
            ws_app.Hide(0) # make Winspec software visible
            # ws_exp = self._dispatch('WinX32.ExpSetup')
            ws_exp = win32com.client.Dispatch('WinX32.ExpSetup')
            self._ws_exp_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, ws_exp)
            # ws_spec_mgr = self._dispatch('WinX32.SpectroObjMgr')
            ws_spec_mgr = win32com.client.Dispatch('WinX32.SpectroObjMgr')
            self._ws_spec_mgr_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, ws_spec_mgr)

            docfile = win32com.client.Dispatch('WinX32.DocFile')
            self._docfile_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, docfile)

            # ws_doc = win32com.client.Dispatch('WinX32.DocFile')
            # self._ws_doc_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, ws_spec_mgr)

            # ws_spt = ws_spec_mgr.Current
            # self.exp = self._dispatch('WinX32.ExpSetup')
            # self._spec_mgr = self._dispatch('WinX32.SpectroObjMgr')
            # self.spt = self._spec_mgr.Current

            # exp_inst = win32com.client.Dispatch('WinX32.ExpSetup')
            # self.exp_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, exp_id)
        except win32com.client.pywintypes.com_error:
            self.logger.warning("Can't find Winspec. Are you sure it's installed?")
            # If Winspec is installed but you run into issues here, have a look at comments t the top of this file.

        self._busy_with_thread = False

    def __initialize_without_threading_support(self):
        """
        Mandatory function. Starts or connects to Winspec software
        """
        self.logger.info('Starting or connecting to Winspec')
        try:
            self._ws_app = win32com.client.gencache.EnsureDispatch("WinX32.Winx32App")
            self._ws_app.Hide(0)  # make Winspec software visible
            self._exp = self._dispatch('WinX32.ExpSetup')
            self._spec_mgr = self._dispatch('WinX32.SpectroObjMgr')
            self._spt = self._spec_mgr.Current
            # pythoncom.CoInitialize()
            # exp_inst = win32com.client.Dispatch('WinX32.ExpSetup')
            # self.exp_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, exp_id)
        except win32com.client.pywintypes.com_error:
            self.logger.warning('Can\'t find Winspec. Are you sure it\'s installed?')
            # If Winspec is installed but you run into issues here, have a look at comments t the top of this file.

    @property
    def ws_app(self):
        if self._threading_mode:
            pythoncom.CoInitialize()
            ws_exp = win32com.client.Dispatch(
                pythoncom.CoGetInterfaceAndReleaseStream(self._ws_exp_id, pythoncom.IID_IDispatch)
            )
            self._ws_exp_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, ws_exp)
            return ws_exp
        else:
            return self._ws_app

    @property
    def exp(self):
        if self._threading_mode:
            pythoncom.CoInitialize()
            ws_exp = win32com.client.Dispatch(
                pythoncom.CoGetInterfaceAndReleaseStream(self._ws_exp_id, pythoncom.IID_IDispatch)
            )
            self._ws_exp_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, ws_exp)
            return ws_exp
        else:
            return self._exp

    @property
    def spt(self):
        if self._threading_mode:
            pythoncom.CoInitialize()
            ws_spec_mgr = win32com.client.Dispatch(
                pythoncom.CoGetInterfaceAndReleaseStream(self._ws_spec_mgr_id, pythoncom.IID_IDispatch)
            )
            self._ws_spec_mgr_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, ws_spec_mgr)
            return ws_spec_mgr.Current
        else:
            return self._spt

    def docfile(self):
        if self._threading_mode:
            pythoncom.CoInitialize()
            docfile = win32com.client.Dispatch(
                pythoncom.CoGetInterfaceAndReleaseStream(self._docfile_id, pythoncom.IID_IDispatch)
            )
            self._docfile_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, docfile)
            return docfile
        else:
            return self._dispatch('WinX32.DocFile')

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
        self.logger.debug("Generating dictionary of parameters")
        _constants = win32com.client.constants.__dict__['__dicts__'][0]
        # Convert these constants to a regular dictionary and only include key-value pairs of which the value is a number (integer)
        self.params = {}
        self.params_exp = {}
        self.params_spt = {}
        self.params_tgc = {}
        self.params_tgp = {}
        self.params_dm = {}
        self.params_x = {}
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
                elif key[:2] == 'X_':
                    self.params_x[key[2:]] = _constants[key]
                else:
                    self.params_other[key] = _constants[key]

    def close(self):
        """ Closes the Winspec software.
        Note that this is not necessary."""
        if self._is_initialized:
            self.ws_app.close()

    def finalize(self):
        """
        Mandatory function. Get's called when exiting a 'with' statement.
        For this controller it does nothing though, except set _is_initialized to False.
        Closing the Winspec software is not necessary.
        """
        self._is_initialized = False

    def idn(self):
        """ Returns Winspec version.
        **Pay attention: doesn't seem to work with threads!**

        :return: identification for the device
        :rtype: string
        """
        self.logger.debug('Ask IDN to device.')
        if self._is_initialized:
            return 'Winspec ' + self.ws_app.Version

    def _check_not_init(self):
        if not self._is_initialized:
            self.logger.error('Winspec Controller is not initialized')
            return True

    def exp_get(self, msg, *args, **kwargs):
        """ Retrieve WinSpec Experiment parameter

        :param msg: should be a key of self.params_exp
        :type msg: string
        :param \*args,**kwargs: Any additional arguments are passed along into the self.exp.GetParam()
        :return: returns Winspec value
        :rtype: int or tuple ?
        """
        if self._check_not_init(): return
        if msg.upper() in self.params_exp:
            return self.exp.GetParam(self.params_exp[msg.upper()], *args, **kwargs)[:-1]
        else:
            self.logger.warning('Unknown EXP parameter: {}'.format(msg))
            return None

    def exp_set(self, msg, value):
        """ Set WinSpec Experiment parameter

        :param msg: should be a key of self.params_exp
        :type msg: string
        :param value: The value to set
        :type value: Depends on parameter  (int, float, string)
        :return: returns errorvalue, 0 if succeeded
        :rtype: typically a tuple containing an int, float or string
        """
        if self._check_not_init(): return
        if msg.upper() in self.params_exp:
            return self.exp.SetParam(self.params_exp[msg.upper()], value)
        else:
            self.logger.warning('Unknown EXP parameter: {}'.format(msg))
            return None

    def spt_get(self, msg, *args, **kwargs):
        """ Retrieve WinSpec Spectrograph parameter

        :param msg: should be a key of self.params_spt
        :type msg: string
        :param value: The value to set
        :type value: Depends on parameter (int, float, string)
        :param \*args,**kwargs: Any additional arguments are passed along into the self.spt.GetParam()
        :return: returns errorvalue, 0 if succeeded
        :rtype: typically a tuple containing an int, float or string
        """
        if self._check_not_init(): return
        if msg.upper() in self.params_spt:
            return self.spt.GetParam(self.params_spt[msg.upper()], *args, **kwargs)[:-1]
        else:
            self.logger.warning('Unknown SPT parameter: {}'.format(msg))
            return None

    def spt_set(self, msg, value):
        """ Set WinSpec Spectrograph parameter

        :param msg: should be a key of self.params_spt
        :type msg: string
        :param value: The value to set
        :type value: Depends on parameter  (int, float, string)
        :return: returns errorvalue, 0 if succeeded
        :rtype: typically a tuple containing an int, float or string
        """
        if self._check_not_init(): return
        if msg.upper() in self.params_spt:
            return self.spt.SetParam(self.params_spt[msg.upper()], value)
        else:
            self.logger.warning('Unknown SPT parameter: {}'.format(msg))
            return None



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

    # To change the logging file use this anywhere:
    # hyperion.set_logfile('my_new_file_path_and_name.log')
    # To modify the levels use this anywhere :
    # hyperion.file_logger.setLevel( logging.INFO )
    # hyperion.stream_logger.setLevel( logging.WARNING )

    # from hyperion import _logger_format
    # logging.basicConfig(level=logging.DEBUG, format=_logger_format,
    #     handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
    #               logging.StreamHandler()])



    dummy = False  # change this to false to work with the real device

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

    # Because closing the device connection is not important for Winspec I'm not using 'with' in this example

    ws = WinspecContr({'force_threading_mode': True})
    ws.initialize()
    print( ws.exp_get('EXPOSURETIME')[0] )

    # Comment
    #
    # EXP_EXPOSURE seems to contain the exposuretime in seconds, but it appears that it is not always immediately updated, I recommend using EXP_EXPOSURETIME and EXP_EXPOSURETIME_UNITS instead

