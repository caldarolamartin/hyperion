"""
==========================
ANC350 Attocube Controller
==========================

This is the controller level of the position ANC350 from Attocube (in the Montana)

This code is strongly based and using PyANC350, which was written by Rob Heath; rob@robheath.me.uk; 24-Feb-2015;
It was taken from github in August 2019 by Irina Komen and made to work with Hyperion


Copyright (c) 2018 Rob Heath

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Description from Rob Heath:
PyANC350 is a control scheme suitable for the Python coding style for the attocube ANC350 closed-loop position system.

It implements ANC350lib, which in turn depends on anc350v2.dll which is provided by attocube in the ANC350_DLL folders on the driver disc.
This in turn requires nhconnect.dll and libusb0.dll. Place all of these in the same folder as this module (and that of ANC350lib).

Unlike ANC350lib which is effectively a re-imagining of the C++ header, PyANC350 is intended to behave as one might expect Python to.
This means: returning values; behaving as an object.

At present this only addresses the first ANC350 connected to the machine.

Usage:
    1. instantiate Positioner() class to begin, eg. pos = Positioner().
    2. methods from the ANC350v2 documentation are implemented such that function PositionerGetPosition(handle, axis, &pos) becomes position = pos.getPosition(axis), PositionerCapMeasure(handle,axis,&cap) becomes  cap = pos.capMeasure(axis), and so on. Return code handling is within ANC350lib.
    3. bitmask() and debitmask() functions have been added for  convenience when using certain functions  (e.g. getStatus,moveAbsoluteSync)
    4. for tidiness remember to Positioner.close() when finished!

**Important NOTE:**

This code assumes that the following files are stored in this folder (hyperion/controller/attocube/)

- anc350v2.dll
- anc350v2.lib
- libusb0.dll

And the (actor) calibration files:

- ANPx101-A3-1079.aps
- ANPx101-A3-1087.aps
- ANPz102-F8-393.aps

You should get these files from the manufacturer (except for libusb0.dll).
"""
import sys
import ctypes
import math
import os
from hyperion import logging
from hyperion.controller.base_controller import BaseController
if sys.maxsize > 2**32:
    print('64 bit PC')
else:
    import hyperion.controller.attocube.ANC350lib as ANC350lib
from hyperion import root_dir


class Anc350(BaseController):
    """
    Class for the ANC350 controller

    :param settings: this includes all the settings needed to connect to the device in question, in this case just dummy.
    :type settings: dict
    """
    def __init__(self, settings):
        super().__init__()  # runs the init of the base_controller class.
        self.logger = logging.getLogger(__name__)
        self.name = 'ANC350'
        self.dummy = settings['dummy']
        self.handle = []
        self.posinf = []
        self.numconnected = []
        self.status = []
        self.logger.debug('Class ANC350 init. Created object.')

        self.max_dclevel_mV = 140000
        self.max_dcLevel_mV_300K = 60000

        self.max_amplitude_mV = 60000
        self.max_frequency_Hz = 2000
        self.actor_name = ['ANPx101-A3-1079.aps','ANPx101-A3-1087.aps','ANPz102-F8-393.aps']


    #----------------------------------------------------------------------------------------------------
    #Used methods both stepper and scanner
    #----------------------------------------------------------------------------------------------------

    def initialize(self):
        """| Initializes the controller.
        | Checks for attocube controller units and connects to it.
        | **Pay attention: there are 6 positioners, but only 1 controller; we connect to the 1.**
        """
        self.check()
        self.connect()
        self._is_initialized = True

    def check(self):
        """Determines number of connected attocube controller devices and their respective hardware IDs.
        """
        self.posinf = ANC350lib.PositionerInfo() #create PositionerInfo Struct
        self.numconnected = ANC350lib.positionerCheck(ctypes.byref(self.posinf)) #look for positioners!
        if self.numconnected > 0:
            self.logger.debug(str(self.numconnected) + 'ANC350 connected')
            self.logger.debug('ANC350 with id:'+ str(self.posinf.id) +'has locked state:' + str(self.posinf.locked))

    def connect(self):
        """| Establishes connection to the first attocube device found.
        | **Pay attention: the 0 that you give to the ANC350lib.Int32 is the first attocube device; not the first of the 6 positioners.**
        """
        self.handle = ANC350lib.Int32(0)
        try:
            ANC350lib.positionerConnect(0,ctypes.byref(self.handle)) #0 means "first device"
            self.logger.info('connected to first (and only) attocube device')
        except Exception as e:
            self.logger.error('unable to connect!')
            raise e

    def capMeasure(self, axis):
        """| Determines the capacitance of the piezo addressed by axis.
        | **Pay attention: the 0 that you give to the ANC350lib.Int32 is the first Attocube device; not the first of the 6 positioners.**

        :param axis: axis number from 0 to 2 for steppers and 3 to 5 for scanners
        :type axis: integer

        :return: capacitance value in mF
        """
        self.status = ANC350lib.Int32(0)
        ANC350lib.positionerCapMeasure(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def finalize(self):
        """Closes connection to ANC350 device.
        """
        self.logger.info('Closing connection to ANC350')
        ANC350lib.positionerClose(self.handle)

    def getStatus(self, axis):
        """| Determines the status of the selected axis.
        | *It is not clear whether it also works for the scanner, or only for the stepper.*
        | result: bit0 (moving) (+1), bit1 (stop detected) (+2), bit2 (sensor error) (+4), bit3 (sensor disconnected) (+8).

        :param axis: axis number from 0 to 2 for steppers and 3 to 5 for scanners
        :type axis: integer

        :return: 1: moving, 2: stop detected, 4: sensor error, 8: sensor disconnected
        """
        self.status = ANC350lib.Int32(0)
        ANC350lib.positionerGetStatus(self.handle,axis,ctypes.byref(self.status))
        status = self.status.value
        out = {}
        out['moving'] = (status & 1)==1
        out['stop'] = (status & 2) == 2
        out['error'] = (status & 4) == 4
        out['disconnected'] = (status & 8) == 8
        return out

    def load(self, axis):
        """| Loads a parameter file for actor configuration.
        | *note: this requires a pointer to a char datatype.*
        | the actor files are in this controller folder, their names are hard coded in the init.
        | *note: Attocube called the up-down actor file ANPz, I called that axis YPiezo.*

        :param axis: axis number from 0 to 2 for steppers and 3 to 5 for scanners
        :type axis: integer
        """
        if axis < 3:
            filename = self.actor_name[axis]

            complete_filename = os.path.join(root_dir, 'controller', 'attocube', filename)

            self.logger.debug('loading actor file: {}'.format(complete_filename))
            filestring = complete_filename.encode('utf8')  # convert python string to bytes
            filestring_pointer = ctypes.c_char_p(filestring)  # create c pointer to variable length char array
            ANC350lib.positionerLoad(self.handle, ctypes.c_int(axis), filestring_pointer)

            self.logger.debug('Loading actor file for attocube piezo appears to have succeeded')
        else:
            self.logger.warning('you are trying to load an actor file for a Scanner, that doesnt need any')

    #Used methods only stepper
    #----------------------------------------------------------------------------------------------------
    def amplitudeControl(self, axis, mode):
        """| Selects the type of amplitude control in the Stepper.
        | The amplitude is controlled by the positioner to hold the value constant determined by the selected type of amplitude control.
        | I thought for closed loop it needs to be set in Step Width mode, nr. 2.
        | However, that gives issues, since sometimes the amplitude is not high enough to make the thing move at all.
        | So Amplitude control mode, nr. 1, seems better.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param mode: Mode takes values 0: speed, 1: amplitude, 2: step size
        :type mode: integer
        """
        ANC350lib.positionerAmplitudeControl(self.handle,axis,mode)

    def amplitude(self, axis, amp):
        """| Set the amplitude setpoint of the Stepper in mV.
        | You need to set the amplitude, max 60V.
        | At room temperature you need 30V for x and y and 40V for z.
        | At low temperature that is higher, 40V or even 50V.
        | Higher amplitude influences step size though.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param amp: amplitude to be set to the Stepper in mV, between 0 and 60V; needs to be an integer!
        :type amp: integer
        """
        if 0 <= amp <= self.max_amplitude_mV:
            ANC350lib.positionerAmplitude(self.handle,axis,amp)
        else:
            raise Exception('The required amplitude needs to be between 0V and 60V')

    def getAmplitude(self, axis):
        """| Determines the actual amplitude.
        | In case of standstill of the actor this is the amplitude setpoint.
        | In case of movement the amplitude set by amplitude control is determined.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :return: measured amplitude in mV
        """
        self.status = ANC350lib.Int32(0)
        ANC350lib.positionerGetAmplitude(self.handle, axis, ctypes.byref(self.status))
        return self.status.value

    def frequency(self, axis, freq):
        """| Sets the frequency of selected stepper axis.
        | Higher means more noise and faster (= less precise?).

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param freq: frequency in Hz, from 1Hz to 2kHz; needs to be an integer!
        :type freq: integer
        """
        self.logger.debug('putting the frequency in the controller level')
        if 1 <= freq <= self.max_frequency_Hz:
            ANC350lib.positionerFrequency(self.handle,axis,freq)
        else:
            raise Exception('The required frequency needs to be between 1Hz and 2kHz')

    def getFrequency(self, axis):
        """Determines the frequency on the stepper.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :return: measured frequency in Hz
        """
        self.freq = ANC350lib.Int32(0)
        ANC350lib.positionerGetFrequency(self.handle,axis,ctypes.byref(self.freq))
        return self.freq.value

    def getPosition(self, axis):
        """| Determines actual position of addressed stepper axis.
        | **Pay attention: the sensor resolution is specified for 200nm.**

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :return: position in nm
        """
        self.pos = ANC350lib.Int32(0)
        ANC350lib.positionerGetPosition(self.handle,axis,ctypes.byref(self.pos))
        return self.pos.value

    def getSpeed(self, axis):
        """| Determines the actual speed.
        | In case of standstill of this actor this is the calculated speed resultingfrom amplitude setpoint, frequency, and motor parameters.
        | In case of movement this is measured speed.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :return: speed in nm/s
        """
        self.spd = ANC350lib.Int32(0)
        ANC350lib.positionerGetSpeed(self.handle,axis,ctypes.byref(self.spd))
        return self.spd.value

    def getStepwidth(self, axis):
        """| Determines the step width.
        | In case of standstill of the motor this is the calculated step width resulting from amplitude setpoint, frequency, and motor parameters.
        | In case of movement this is measured step width.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :return: stepwidth in nm
        """
        self.stepwdth = ANC350lib.Int32(0)
        ANC350lib.positionerGetStepwidth(self.handle,axis,ctypes.byref(self.stepwdth))
        self.logger.debug('stepwidth is here ' + str(self.stepwdth.value))
        return self.stepwdth.value

    def moveAbsolute(self, axis, position, rotcount=0):
        """| Starts approach to absolute target position.
        | Previous movement will be stopped.
        | Rotcount optional argument, not in our case since we dont have rotation options.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param position: absolute target position in nm; needs to be an integer!
        :type position: integer

        :param rotcount: optional argument position units are in 'unit of actor multiplied by 1000' (generally nanometres)
        """
        self.logger.debug('Moving axis {} to an absolute value: {}'.format(axis, position))
        ANC350lib.positionerMoveAbsolute(self.handle,axis,position,rotcount)

    def moveRelative(self, axis, position, rotcount=0):
        """| Starts approach to relative target position.
        | Previous movement will be stopped.
        | Rotcount optional argument, not in our case since we dont have rotation options.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param position: relative target position in nm, can be both positive and negative; needs to be an integer!
        :type position: integer

        :param rotcount: optional argument position units are in 'unit of actor multiplied by 1000' (generally nanometres)
        """
        ANC350lib.positionerMoveRelative(self.handle,axis,position,rotcount)

    def moveSingleStep(self, axis, direction):
        """| Starts a one-step positioning, where the stepwidht is determined by the amplitude and frequency.
        | Previous movement will be stopped.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param direction: can be 0 (forward) or 1 (backward)
        """
        ANC350lib.positionerMoveSingleStep(self.handle,axis,direction)

    def stopApproach(self, axis):
        """
        | Stops approaching target/relative/reference position.
        | DC level of affected axis after stopping depends on setting by .setTargetGround().
        | *Dont know for sure whats the difference with stopMoving.*

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer
        """
        self.logger.info('Stopping the Approach of Stepper')
        ANC350lib.positionerStopApproach(self.handle,axis)

    def moveContinuous(self, axis, direction):
        """Starts continuously positioning with set parameters for ampl and speed and amp control respectively.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param direction: can be 0 (forward) or 1 (backward)
        :type direction: integer
        """
        ANC350lib.positionerMoveContinuous(self.handle,axis,direction)


    #Used methods only scanner
    #----------------------------------------------------------------------------------------------------

    def dcLevel(self, axis, dclev):
        """Sets the dc level of selected scanner (or maybe stepper, if you want).

        :param axis: axis number from 0 to 2 for steppers and 3 to 5 for scanners
        :type axis: integer

        :param dclev: DC level in mV; needs to be an integer!
        :type dclev: integer
        """

        if 0 <= dclev <= self.max_dclevel_mV:
            if dclev > self.max_dcLevel_mV_300K:
                self.logger.warning('Putting more than 60V is only okay at low temperatures')

            ANC350lib.positionerDCLevel(self.handle, axis, dclev)
        else:
            self.logger.warning('Trying to exceed the voltage on the piezo')

    def getDcLevel(self, axis):
        """| Determines the status actual DC level on the scanner (or stepper).
        | **Again: the 0 is for the number of controller units, not the 6 positioners.**

        :param axis: axis number from 3 to 5 for scanners
        :type axis: integer

        :return: measured DC level in mV
        """
        self.dclev = ANC350lib.Int32(0)
        ANC350lib.positionerGetDcLevel(self.handle,axis,ctypes.byref(self.dclev))
        return self.dclev.value

    def getIntEnable(self, axis):
        """Determines status of internal signal generation of addressed axis. only applicable for scanner/dither axes.

        :param axis: axis number from 3 to 5 for scanners
        :type axis: integer

        :return: True if the INT mode is selected, False if not
        """
        self.status = ctypes.c_bool(None)
        ANC350lib.positionerGetIntEnable(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def intEnable(self, axis, state):
        """Activates/deactivates internal signal generation of addressed axis; only applicable for scanner/dither axes.

        :param axis: axis number from 3 to 5 for scanners
        :type axis: integer

        :param state: True is enabled, False is disabled
        :type state: bool
        """
        ANC350lib.positionerIntEnable(self.handle,axis,ctypes.c_bool(state))


    # ----------------------------------------------------------------------------------------------------
    # Maybe useful methods, but now unused
    # ----------------------------------------------------------------------------------------------------

    def moveAbsoluteSync(self, bitmask_of_axes):
        """| *UNUSED*
        | Starts the synchronous approach to absolute target position for selected axis.
        | Previous movement will be stopped.
        | Target position for each axis defined by .setTargetPos() takes a *bitmask* of axes!
        | *Not clear what's the difference with moveAbsolute.*

        :param bitmask_of_axes:
        """
        ANC350lib.positionerMoveAbsoluteSync(self.handle,bitmask_of_axes)

    def moveReference(self, axis):
        """| *UNUSED*
        | Starts approach to reference position.
        | Previous movement will be stopped.
        | *No idea whats the difference with moveRelative*

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer
        """
        ANC350lib.positionerMoveReference(self.handle,axis)

    def resetPosition(self, axis):
        """| *UNUSED*
        | sets the origin to the actual position.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer
        """
        ANC350lib.positionerResetPosition(self.handle,axis)

    def setOutput(self, axis, state):
        """| *UNUSED*
        | activates/deactivates the addressed axis.
        | *no idea what that means, but sounds interesting.*

        :param axis:
        :param state:
        """
        ANC350lib.positionerSetOutput(self.handle,axis,ctypes.c_bool(state))

    def setStopDetectionSticky(self, axis, state):
        """| *UNUSED*
        | when enabled, an active stop detection status remains active until cleared manually by .clearStopDetection().
        | *Is this what in Daisy is called hump detection? Than it might be useful.*

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param state:
        """
        ANC350lib.positionerSetStopDetectionSticky(self.handle,axis,state)

    def stopDetection(self, axis, state):
        """| *UNUSED*
        | switches stop detection on/off.
        | *Is this what in Daisy is called hump detection? Than it might be useful.*

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param state:
        """
        ANC350lib.positionerStopDetection(self.handle,axis,ctypes.c_bool(state))

    def stopMoving(self, axis):
        """| *UNUSED*
        | stops any positioning, DC level of affected axis is set to zero after stopping.

        :param axis:
        """
        ANC350lib.positionerStopMoving(self.handle,axis)

    def updateAbsolute(self, axis, position):
        """| *UNUSED*
        | update s target position for a *running* approach.
        | function has lower performance impact on running approach compared to .moveAbsolute().
        | position units are in 'unit of actor multiplied by 1000' (generally nanometres).

        :param axis:
        :param position:
        """
        ANC350lib.positionerUpdateAbsolute(self.handle,axis,position)

    # ----------------------------------------------------------------------------------------------------
    # Not (yet) used methods
    # ----------------------------------------------------------------------------------------------------

    def acInEnable(self, axis, state):
        """| *UNUSED*
        | Activates/deactivates AC input of addressed axis; only applicable for dither axes.
        """
        ANC350lib.positionerAcInEnable(self.handle,axis,ctypes.c_bool(state))

    def bandwidthLimitEnable(self, axis, state):
        """| *UNUSED*
        | activates/deactivates the bandwidth limiter of the addressed axis. only applicable for scanner axes.
        """
        ANC350lib.positionerBandwidthLimitEnable(self.handle,axis,ctypes.c_bool(state))

    def clearStopDetection(self, axis):
        """| *UNUSED*
        | when .setStopDetectionSticky() is enabled, this clears the stop detection status.
        """
        ANC350lib.positionerClearStopDetection(self.handle,axis)

    def dcInEnable(self, axis, state):
        """| *UNUSED*
        | Activates/deactivates DC input of addressed axis; only applicable for scanner/dither axes.
        """
        ANC350lib.positionerDcInEnable(self.handle,axis,ctypes.c_bool(state))

    def dutyCycleEnable(self, state):
        """*UNUSED*
        controls duty cycle mode.
        """
        ANC350lib.positionerDutyCycleEnable(self.handle,ctypes.c_bool(state))

    def dutyCycleOffTime(self, value):
        """*UNUSED*
        sets duty cycle off time.
        """
        ANC350lib.positionerDutyCycleOffTime(self.handle,value)

    def dutyCyclePeriod(self, value):
        """*UNUSED*
        sets duty cycle period.
        """
        ANC350lib.positionerDutyCyclePeriod(self.handle,value)

    def externalStepBkwInput(self, axis, input_trigger):
        """| *UNUSED*
        | configures external step trigger input for selected axis. a trigger on this input results in a backwards single step.
        | input_trigger: 0 disabled, 1-6 input trigger.

        """
        ANC350lib.positionerExternalStepBkwInput(self.handle,axis,input_trigger)

    def externalStepFwdInput(self, axis, input_trigger):
        """| *UNUSED*
        | configures external step trigger input for selected axis.
        | a trigger on this input results in a forward single step.
        | input_trigger: 0 disabled, 1-6 input trigger.

        """
        ANC350lib.positionerExternalStepFwdInput(self.handle,axis,input_trigger)

    def externalStepInputEdge(self, axis, edge):
        """| *UNUSED*
        | configures edge sensitivity of external step trigger input for selected axis.
        | edge: 0 rising, 1 falling.
        """
        ANC350lib.positionerExternalStepInputEdge(self.handle,axis,edge)

    def getAcInEnable(self, axis):
        """| *UNUSED*
        | determines status of ac input of addressed axis. only applicable for dither axes.
        """
        self.status = ctypes.c_bool(None)
        ANC350lib.positionerGetAcInEnable(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def getBandwidthLimitEnable(self, axis):
        """| *UNUSED*
        | determines status of bandwidth limiter of addressed axis. only applicable for scanner axes.
        """
        self.status = ctypes.c_bool(None)
        ANC350lib.positionerGetBandwidthLimitEnable(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def getDcInEnable(self, axis):
        """| *UNUSED*
        | determines status of dc input of addressed axis. only applicable for scanner/dither axes.
        """
        self.status = ctypes.c_bool(None)
        ANC350lib.positionerGetDcInEnable(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def getReference(self, axis):
        """*UNUSED*
        determines distance of reference mark to origin.
        """
        self.pos = ANC350lib.Int32(0)
        self.validity = ctypes.c_bool(None)
        ANC350lib.positionerGetReference(self.handle,axis,ctypes.byref(self.pos),ctypes.byref(self.validity))
        return self.pos.value, self.validity.value

    def getReferenceRotCount(self, axis):
        """*UNUSED*
        determines actual position of addressed axis.
        """
        self.rotcount = ANC350lib.Int32(0)
        ANC350lib.positionerGetReferenceRotCount(self.handle,axis,ctypes.byref(self.rotcount))
        return self.rotcount.value

    def getRotCount(self, axis):
        """*UNUSED*
        determines actual number of rotations in case of rotary actuator.
        """
        self.rotcount = ANC350lib.Int32(0)
        ANC350lib.positionerGetRotCount(self.handle,axis,ctypes.byref(self.rotcount))
        return self.rotcount.value

    def quadratureAxis(self, quadratureno, axis):
        """| *UNUSED*
        | selects the axis for use with this trigger in/out pair.
        | quadratureno: number of addressed quadrature unit (0-2).
        """
        ANC350lib.positionerQuadratureAxis(self.handle,quadratureno,axis)

    def quadratureInputPeriod(self, quadratureno, period):
        """| *UNUSED*
        | selects the stepsize the controller executes when detecting a step on its input AB-signal.
        | quadratureno: number of addressed quadrature unit (0-2). period: stepsize in unit of actor * 1000.
        """
        ANC350lib.positionerQuadratureInputPeriod(self.handle,quadratureno,period)

    def quadratureOutputPeriod(self, quadratureno, period):
        """| *UNUSED*
        | selects the position difference which causes a step on the output AB-signal.
        | quadratureno: number of addressed quadrature unit (0-2). period: period in unit of actor * 1000.
        """
        ANC350lib.positionerQuadratureOutputPeriod(self.handle,quadratureno,period)

    def sensorPowerGroupA(self, state):
        """| *UNUSED*
        | switches power of sensor group A.
        | Sensor group A contains either the sensors of axis 1-3 or 1-2 dependent on hardware of controller.
        """
        ANC350lib.positionerSensorPowerGroupA(self.handle,ctypes.c_bool(state))

    def sensorPowerGroupB(self, state):
        """| *UNUSED*
        | switches power of sensor group B.
        | Sensor group B contains either the sensors of axis 4-6 or 3 dependent on hardware of controller.
        """
        ANC350lib.positionerSensorPowerGroupB(self.handle,ctypes.c_bool(state))

    def setHardwareId(self, hwid):
        """*UNUSED*
        sets the hardware ID for the device (used to differentiate multiple devices).
        """
        ANC350lib.positionerSetHardwareId(self.handle,hwid)

    def setTargetGround(self, axis, state):
        """*UNUSED*
        when enabled, actor voltage set to zero after closed-loop positioning finished.
        """
        ANC350lib.positionerSetTargetGround(self.handle,axis,ctypes.c_bool(state))

    def setTargetPos(self, axis, pos, rotcount=0):
        """*UNUSED*
        sets target position for use with .moveAbsoluteSync().
        """
        ANC350lib.positionerSetTargetPos(self.handle,axis,pos,rotcount)

    def singleCircleMode(self, axis, state):
        """| *UNUSED*
        | switches single circle mode.
        | In case of activated single circle mode the number of rotations are ignored and the shortest way to target position is used. Only relevant for rotary actors.
        """
        ANC350lib.positionerSingleCircleMode(self.handle,axis,ctypes.c_bool(state))

    def staticAmplitude(self, amp):
        """*UNUSED*
        sets output voltage for resistive sensors.
        """
        ANC350lib.positionerStaticAmplitude(self.handle,amp)

    def stepCount(self, axis, stps):
        """*UNUSED*
        configures number of successive step scaused by external trigger or manual step request. steps = 1 to 65535.
        """
        ANC350lib.positionerStepCount(self.handle,axis,stps)

    def trigger(self, triggerno, lowlevel, highlevel):
        """| *UNUSED*
        | sets the trigger thresholds for the external trigger.
        | triggerno is 0-5, lowlevel/highlevel in units of actor * 1000.
        """
        ANC350lib.positionerTrigger(self.handle,triggerno,lowlevel,highlevel)

    def triggerAxis(self, triggerno, axis):
        """*UNUSED*
        selects the corresponding axis for the addressed trigger. triggerno is 0-5.
        """
        ANC350lib.positionerTriggerAxis(self.handle,triggerno,axis)

    def triggerEpsilon(self, triggerno, epsilon):
        """*UNUSED*
        sets the hysteresis of the external trigger. epsilon in units of actor * 1000.
        """
        ANC350lib.positionerTriggerEpsilon(self.handle,triggerno,epsilon)

    def triggerModeIn(self, mode):
        """| *UNUSED*
        | selects the mode of the input trigger signals.
        | state: 0 disabled - inputs trigger nothing,
        | 1 quadrature - three pairs of trigger in signals are used to accept AB-signals for relative positioning,
        | 2 coarse - trigger in signals are used to generate coarse steps.
        """
        ANC350lib.positionerTriggerModeIn(self.handle,mode)

    def triggerModeOut(self, mode):
        """| *UNUSED*
        | selects the mode of the output trigger signals.
        | state: 0 disabled - inputs trigger nothing,
        | 1 position - the trigger outputs reacts to the defined position ranges with the selected polarity,
        | 2 quadrature - three pairs of trigger out signals are used to signal relative movement as AB-signals, 3 IcHaus - the trigger out signals are used to output the internal position signal of num-sensors.
        """
        ANC350lib.positionerTriggerModeOut(self.handle,mode)

    def triggerPolarity(self, triggerno, polarity):
        """ *UNUSED*

        sets the polarity of the external trigger, triggerno: 0-5, polarity: 0 low active, 1 high active.
        """
        ANC350lib.positionerTriggerPolarity(self.handle,triggerno,polarity)

class Anc350Dummy(Anc350):
    pass

def bitmask(input_array):
    """
    | takes an array or string and converts to integer bitmask.
    | reads from left to right e.g. 0100 = 2 not 4.
    """
    total = 0
    for i in range(len(input_array)):
        if int(input_array[i]) != 0 and int(input_array[i])!=1:
            raise Exception('nonbinary value in bitmask, panic!')
        else:
            total += int(input_array[i])*(2**(i))
    return total

def debitmask(input_int,num_bits = False):
    """
    | takes a bitmask and returns a list of which bits are switched.
    | reads from left to right e.g. 2 = [0, 1] not [1, 0].
    """
    if num_bits == False and input_int>0:
        num_bits = int(math.ceil(math.log(input_int+1,2)))
    elif input_int == 0:
        return [0]

    result_array = [0]*num_bits
    for i in reversed(range(num_bits)):
        if input_int - 2**i >= 0:
            result_array[i] = 1
            input_int -= 2**i
    return result_array


if __name__ == "__main__":

    import time

    with Anc350(settings = {'dummy': False}) as anc:
        anc.initialize()

        #-------------------------------
        #controlling the stepper
        #-------------------------------


        anc.load(0)

        # instantiate position as anc
        print('-------------------------------------------------------------')
        print('capacitances:')
        # for axis in range(2):
        #     print(axis, anc.capMeasure(axis))
        # print('-------------------------------------------------------------')

        print('setting Amplitude Control to StepWidth mode, which seems to be the close loop one')
        anc.amplitudeControl(0,2)

        anc.amplitude(0,30000)      #30V
        print('amplitude is ',anc.getAmplitude(0),'mV')

        print('so the step width is ',anc.getStepwidth(0),'nm')

        anc.frequency(0,1000)
        print('frequency is ',anc.getFrequency(0),'Hz')

        print('so the speed is ',anc.getSpeed(0),'nm/s')

        print('axis is now at', anc.getPosition(0))



        #there are 4 ways in which you can move the stepper

        #nr. 1: to an absolute position

        # print('moving to x = 2mm')
        # anc.moveAbsolute(ax['x'], 2000000)
        #
        # # check what's happening
        # time.sleep(0.5)
        # state = 1
        # while state == 1:
        #     newstate = anc.getStatus(ax['x'])  # find bitmask of status
        #     if newstate == 1:
        #         print('axis moving, currently at', anc.getPosition(ax['x']))
        #     elif newstate == 0:
        #         print('axis arrived at', anc.getPosition(ax['x']))
        #     else:
        #         print('axis has value', newstate)
        #     state = newstate
        #     time.sleep(0.5)

        #nr. 2: with a step, the stepwidth was determined by the amplitude and frequency
        #so the step is order of magnitude 300 nm

        print('-------------------------------------------------------------')
        print('moving 10 single steps of stepwidth, determined by set amplitude and frequency')

        #forward 0, backward 1
        #but you have to give it time, because it won't tell you that it's not finished moving yet
        # for ii in range(10):
        #     anc.moveSingleStep(0,0)
        #     time.sleep(0.5)
        #     print(ii,': we are now at ',anc.getPosition(0),'nm')
        #
        # #nr. 3: with a step that you give it by ordering a relative move
        # #but this one takes a very long time
        #
        print('-------------------------------------------------------------')

        # position = -10000
        #
        # print('moving to a relative position, ...um back')
        # startpos = anc.getPosition(0)
        # anc.moveRelative(0,position)
        # time.sleep(0.4)         #important to have this number, otherwise it already starts asking before the guy even knows whether he moves
        #
        # pos = anc.getPosition(0)
        # didntmove = False
        # while anc.getStatus(0)['moving']:
        #     time.sleep(0.1)
        #     new_pos = anc.getPosition(0)
        #     print(new_pos)
        #     if np.abs(new_pos - pos) < 500:
        #         didntmove = True
        #         break
        #     pos = new_pos
        #
        # print(anc.getPosition(0))
        # print(didntmove)

        #np.abs(startpos - pos) <

        # time.sleep(1)
        # state = 1
        # while state == 1:
        #     newstate = anc.getStatus(ax['x'])  # find bitmask of status
        #     print(newstate)
        #     if newstate == 1:
        #         print('axis moving, currently at', anc.getPosition(ax['x']))
        #     elif newstate == 0:
        #         print('axis arrived at', anc.getPosition(ax['x']))
        #     elif newstate == 2 | 3:
        #         print('axis arrived at range; ', anc.getStatus(0))
        #     else:
        #         print('axis has value', newstate)
        #     state = newstate
        #     time.sleep(0.1)
        #
        # #nr. 4: put a voltage on the piezo
        # #this means it makes a small step too; in theory
        # #it's too small to detect with the closed loop resolution, need a camera to see it
        # #60V seems to be the max
        # #this should have a fine positioning range of 3.5um
        #
        # print('-------------------------------------------------------------')
        # print('moving in fine positioning mode by putting 10V')
        # anc.dcLevel(0,10000)
        # print('put a DC level of ',anc.getDcLevel(0),'mV')

        #you need to set the mode to INT
        #this means you can apply a voltage of 0-140V to the piezo

        print('-------------------------------------------------------------')
        print('now we start with the SCANNER')
        anc.intEnable(3,True)
        print('is the scanner on INT mode? ',anc.getIntEnable(3))

        #this one has only one way to make a step: put a voltage

        print('-------------------------------------------------------------')
        print('moving something by putting 40V')
        anc.dcLevel(3,40000)
        print('put a DC level of ',anc.getDcLevel(3),'mV')









