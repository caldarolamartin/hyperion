#
#  PyANC350 is a control scheme suitable for the Python coding style
#    for the attocube ANC350 closed-loop positioner system.
#
#  It implements ANC350lib, which in turn depends on anc350v2.dll
#    which is provided by attocube in the ANC350_DLL folders
#    on the driver disc.
#    This in turn requires nhconnect.dll and libusb0.dll. Place all
#    of these in the same folder as this module (and that of ANC350lib).
#
#  Unlike ANC350lib which is effectively a re-imagining of the
#    C++ header, PyANC350 is intended to behave as one might expect
#    Python to. This means: returning values; behaving as an object.
#
#  At present this only addresses the first ANC350 connected to the
#    machine.
#
#  Usage:
#  1. instantiate Positioner() class to begin, eg. pos = Positioner().
#  2. methods from the ANC350v2 documentation are implemented such that
#      function PositionerGetPosition(handle, axis, &pos)
#      becomes position = pos.getPosition(axis),
#      PositionerCapMeasure(handle,axis,&cap) becomes
#      cap = pos.capMeasure(axis), and so on. Return code handling is
#      within ANC350lib.
#  3. bitmask() and debitmask() functions have been added for
#      convenience when using certain functions
#      (e.g. getStatus,moveAbsoluteSync)
#  4. for tidiness remember to Positioner.close() when finished!
#
#                PyANC350 is written by Rob Heath
#                      rob@robheath.me.uk
#                         24-Feb-2015
#                       robheath.me.uk

from hyperion import root_dir
from hyperion.controller.base_controller import BaseController

import hyperion.controller.attocube.ANC350lib as ANC350lib
import ctypes
import math
import os
import sys
import numpy as np
import logging


class Anc350(BaseController):
    def __init__(self, settings={'dummy': False}):
        """ INIT of the class

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict
        """
        super().__init__()  # runs the init of the base_controller class.
        self.logger = logging.getLogger(__name__)
        self.name = 'ANC350'
        self.dummy = settings['dummy']
        self.logger.info('Class ANC350 init. Created object.')

    #----------------------------------------------------------------------------------------------------
    #Used methods both stepper and scanner
    #----------------------------------------------------------------------------------------------------

    def initialize(self):
        """Initializes controller
        Checks for attocube controller units and connects to it
        Pay attention: there are 6 positioners, but only 1 controller; we connect to the 1

        """
        self.check()
        self.connect()
        self._is_initialized = True

    def check(self):
        """Determines number of connected attocube controller devices and their respective hardware IDs
        """
        self.posinf = ANC350lib.PositionerInfo() #create PositionerInfo Struct
        self.numconnected = ANC350lib.positionerCheck(ctypes.byref(self.posinf)) #look for positioners!
        if self.numconnected > 0:
            self.logger.info(str(self.numconnected) + 'ANC350 connected')
            self.logger.info('ANC350 with id:'+ str(self.posinf.id) +'has locked state:' + str(self.posinf.locked))

    def connect(self):
        """Establishes connection to first attocube device found
        Pay attention: the 0 that you give to the ANC350lib.Int32 is the first attocube device; not the first of the 6 positioners
        """
        self.handle = ANC350lib.Int32(0)
        'I am reaching the handle'
        try:
            ANC350lib.positionerConnect(0,ctypes.byref(self.handle)) #0 means "first device"
            self.logger.info('connected to first positioner')
        except Exception as e:
            self.logger.error('unable to connect!')
            raise e

    def capMeasure(self, axis):
        """Determines the capacitance of the piezo addressed by axis
        Pay attention: the 0 that you give to the ANC350lib.Int32 is the first attocube device; not the first of the 6 positioners

        :param axis: axis number from 0 to 2 for steppers and 3 to 5 for scanners
        :type axis: integer

        :return status.value: capacitance value in mF
        """
        self.status = ANC350lib.Int32(0)
        ANC350lib.positionerCapMeasure(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def finalize(self):
        """Closes connection to ANC350 device
        """
        self.logger.info('Closing connection to ANC350')
        ANC350lib.positionerClose(self.handle)


    #Used methods only stepper
    #----------------------------------------------------------------------------------------------------
    def amplitudeControl(self, axis, mode):
        """Selects the type of amplitude control in the stepper
        The amplitude is controlled by the positioner to hold the value constant determined by the selected type of amplitude control.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param mode: Mode takes values 0: speed, 1: amplitude, 2: step size
        :type mode: integer
        """
        ANC350lib.positionerAmplitudeControl(self.handle,axis,mode)

    def amplitude(self, axis, amp):
        """Set the amplitude setpoint of the Stepper in mV

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param amp: amplitude to be set to the Stepper in mV, between
        :type amp: integer or float
        """
        if 0 <= amp <= 60000:
            ANC350lib.positionerAmplitude(self.handle,axis,amp)
        else:
            raise Exception('The required amplitude needs to be between 0V and 60V')

    def getAmplitude(self, axis):
        """Determines the actual amplitude.
        In case of standstill of the actor this is the amplitude setpoint.
        In case of movement the amplitude set by amplitude control is determined.

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :return: measured amplitude in mV
        """
        self.status = ANC350lib.Int32(0)
        ANC350lib.positionerGetAmplitude(self.handle, axis, ctypes.byref(self.status))
        return self.status.value

    def frequency(self, axis, freq):
        """Sets the frequency of selected stepper axis

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :param freq: frequency in Hz, from 1Hz to 2kHz
        :type freq: integer
        """
        if 1 <= freq <= 2000:
            ANC350lib.positionerFrequency(self.handle,axis,freq)
        else:
            raise Exception('The required frequency needs to be between 1Hz and 2kHz')

    def getFrequency(self, axis):
        """Determines the frequency on the stepper

        :param axis: axis number from 0 to 2 for steppers
        :type axis: integer

        :return: measured frequency in Hz
        """
        self.freq = ANC350lib.Int32(0)
        ANC350lib.positionerGetFrequency(self.handle,axis,ctypes.byref(self.freq))
        return self.freq.value

    def getPosition(self, axis):
        """Determines actual position of addressed stepper axis
        Pay attention: the sensor resolution is specified for 200nm

        :param axis:
        :return:
        """
        '''
        
        '''
        self.pos = ANC350lib.Int32(0)
        ANC350lib.positionerGetPosition(self.handle,axis,ctypes.byref(self.pos))
        return self.pos.value

    #Used methods only scanner
    #----------------------------------------------------------------------------------------------------

    def dcLevel(self, axis, dclev):
        """Sets the dc level of selected scanner (or maybe stepper, if you want)

        :param axis: axis number from 0 to 2 for steppers and 3 to 5 for scanners
        :type axis: integer

        :param dclev: DC level in mV
        :type dclev: integer
        """
        if 0 <= dclev <= 140000:
            ANC350lib.positionerDCLevel(self.handle, axis, dclev)
        else:
            raise Exception('The required voltage is between 0V - 140V')

    def getDcLevel(self, axis):
        """Determines the status actual DC level on the scanner (or stepper)
        Again: the 0 is for the number of controller units, not the 6 positioners

        :param axis: axis number from 3 to 5 for scanners
        :type axis: integer

        :return: measured DC level in mV
        """
        self.dclev = ANC350lib.Int32(0)
        ANC350lib.positionerGetDcLevel(self.handle,axis,ctypes.byref(self.dclev))
        return self.dclev.value

    def getIntEnable(self, axis):
        """Determines status of internal signal generation of addressed axis. only applicable for scanner/dither axes

        :param axis: axis number from 3 to 5 for scanners
        :type axis: integer

        :return: True if the INT mode is selected, False if not
        """
        self.status = ctypes.c_bool(None)
        ANC350lib.positionerGetIntEnable(self.handle,axis,ctypes.byref(self.status))
        return self.status.value




    # ----------------------------------------------------------------------------------------------------
    # Not (yet) used methods
    # ----------------------------------------------------------------------------------------------------

    def acInEnable(self, axis, state):
        '''
        Activates/deactivates AC input of addressed axis; only applicable for dither axes
        '''
        ANC350lib.positionerAcInEnable(self.handle,axis,ctypes.c_bool(state))


    def bandwidthLimitEnable(self, axis, state):
        '''
        activates/deactivates the bandwidth limiter of the addressed axis. only applicable for scanner axes
        '''
        ANC350lib.positionerBandwidthLimitEnable(self.handle,axis,ctypes.c_bool(state))

    def clearStopDetection(self, axis):
        '''
        when .setStopDetectionSticky() is enabled, this clears the stop detection status
        '''
        ANC350lib.positionerClearStopDetection(self.handle,axis)

    def dcInEnable(self, axis, state):
        '''
        Activates/deactivates DC input of addressed axis; only applicable for scanner/dither axes
        '''
        ANC350lib.positionerDcInEnable(self.handle,axis,ctypes.c_bool(state))

    def dutyCycleEnable(self, state):
        '''
        controls duty cycle mode
        '''
        ANC350lib.positionerDutyCycleEnable(self.handle,ctypes.c_bool(state))

    def dutyCycleOffTime(self, value):
        '''
        sets duty cycle off time
        '''
        ANC350lib.positionerDutyCycleOffTime(self.handle,value)

    def dutyCyclePeriod(self, value):
        '''
        sets duty cycle period
        '''
        ANC350lib.positionerDutyCyclePeriod(self.handle,value)

    def externalStepBkwInput(self, axis, input_trigger):
        '''
        configures external step trigger input for selected axis. a trigger on this input results in a backwards single step. input_trigger: 0 disabled, 1-6 input trigger
        '''
        ANC350lib.positionerExternalStepBkwInput(self.handle,axis,input_trigger)

    def externalStepFwdInput(self, axis, input_trigger):
        '''
        configures external step trigger input for selected axis. a trigger on this input results in a forward single step. input_trigger: 0 disabled, 1-6 input trigger
        '''
        ANC350lib.positionerExternalStepFwdInput(self.handle,axis,input_trigger)

    def externalStepInputEdge(self, axis, edge):
        '''
        configures edge sensitivity of external step trigger input for selected axis. edge: 0 rising, 1 falling
        '''
        ANC350lib.positionerExternalStepInputEdge(self.handle,axis,edge)

    def getAcInEnable(self, axis):
        '''
        determines status of ac input of addressed axis. only applicable for dither axes
        '''
        self.status = ctypes.c_bool(None)
        ANC350lib.positionerGetAcInEnable(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def getBandwidthLimitEnable(self, axis):
        '''
        determines status of bandwidth limiter of addressed axis. only applicable for scanner axes
        '''
        self.status = ctypes.c_bool(None)
        ANC350lib.positionerGetBandwidthLimitEnable(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def getDcInEnable(self, axis):
        '''
        determines status of dc input of addressed axis. only applicable for scanner/dither axes
        '''
        self.status = ctypes.c_bool(None)
        ANC350lib.positionerGetDcInEnable(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def getReference(self, axis):
        '''
        determines distance of reference mark to origin
        '''
        self.pos = ANC350lib.Int32(0)
        self.validity = ctypes.c_bool(None)
        ANC350lib.positionerGetReference(self.handle,axis,ctypes.byref(self.pos),ctypes.byref(self.validity))
        return self.pos.value, self.validity.value

    def getReferenceRotCount(self, axis):
        '''
        determines actual position of addressed axis
        '''
        self.rotcount = ANC350lib.Int32(0)
        ANC350lib.positionerGetReferenceRotCount(self.handle,axis,ctypes.byref(self.rotcount))
        return self.rotcount.value

    def getRotCount(self, axis):
        '''
        determines actual number of rotations in case of rotary actuator
        '''
        self.rotcount = ANC350lib.Int32(0)
        ANC350lib.positionerGetRotCount(self.handle,axis,ctypes.byref(self.rotcount))
        return self.rotcount.value

    def getSpeed(self, axis):
        '''
        determines the actual speed. In case of standstill of this actor this is the calculated speed resulting	from amplitude setpoint, frequency, and motor parameters. In case of movement this is measured speed.
        '''
        self.spd = ANC350lib.Int32(0)
        ANC350lib.positionerGetSpeed(self.handle,axis,ctypes.byref(self.spd))
        return self.spd.value

    def getStatus(self, axis):
        '''
        determines the status of the selected axis. result: bit0 (moving), bit1 (stop detected), bit2 (sensor error), bit3 (sensor disconnected)
        '''
        self.status = ANC350lib.Int32(0)
        ANC350lib.positionerGetStatus(self.handle,axis,ctypes.byref(self.status))
        return self.status.value

    def getStepwidth(self, axis):
        '''
        determines the step width. In case of standstill of the motor this is the calculated step width	resulting from amplitude setpoint, frequency, and motor parameters. In case of movement this is measured step width
        '''
        self.stepwdth = ANC350lib.Int32(0)
        ANC350lib.positionerGetStepwidth(self.handle,axis,ctypes.byref(self.stepwdth))
        return self.stepwdth.value

    def intEnable(self, axis, state):
        '''
        Activates/deactivates internal signal generation of addressed axis; only applicable for scanner/dither axes
        '''
        ANC350lib.positionerIntEnable(self.handle,axis,ctypes.c_bool(state))

    def load(self, axis, filename):
        '''
        loads a parameter file for actor configuration.	note: this requires a pointer to a char datatype. having no parameter file to test, I have no way of telling whether this will work, especially with the manual being as erroneous as it is. as such, use at your own (debugging) risk!
        '''
        ANC350lib.positionerLoad(self.handle, axis, ctypes.byref(ctypes.c_char(filename.encode())))

        # ANC350lib.positionerLoad(self.handle, axis, ctypes.byref(ctypes.c_char(bytearray(filename.encode()))))

        #ANC350lib.positionerLoad(self.handle,axis,ctypes.byref(ctypes.c_char_p(filename.encode('utf-8'))))

        #f = ctypes.create_string_buffer(filename.encode())


    def moveAbsolute(self, axis, position, rotcount=0):
        '''
        starts approach to absolute target position. previous movement will be stopped. rotcount optional argument position units are in 'unit of actor multiplied by 1000' (generally nanometres)
        '''
        print('I reached the move absolute method')
        ANC350lib.positionerMoveAbsolute(self.handle,axis,position,rotcount)

    def moveAbsoluteSync(self, bitmask_of_axes):
        '''
        starts the synchronous approach to absolute target position for selected axis. previous movement will be stopped. target position for each axis defined by .setTargetPos() takes a *bitmask* of axes!
        '''
        ANC350lib.positionerMoveAbsoluteSync(self.handle,bitmask_of_axes)

    def moveContinuous(self, axis, direction):
        '''
        starts continuously positioning with set parameters for ampl and speed and amp control respectively. direction can be 0 (forward) or 1 (backward)
        '''
        ANC350lib.positionerMoveContinuous(self.handle,axis,direction)

    def moveReference(self, axis):
        '''
        starts approach to reference position. previous movement will be stopped.
        '''
        ANC350lib.positionerMoveReference(self.handle,axis)

    def moveRelative(self, axis, position, rotcount=0):
        '''
        starts approach to relative target position. previous movement will be stopped. rotcount optional argument. position units are in 'unit of actor multiplied by 1000' (generally nanometres)
        '''
        ANC350lib.positionerMoveRelative(self.handle,axis,position,rotcount)

    def moveSingleStep(self, axis, direction):
        '''
        starts a one-step positioning. Previous movement will be stopped. direction can be 0 (forward) or 1 (backward)
        '''
        ANC350lib.positionerMoveSingleStep(self.handle,axis,direction)

    def quadratureAxis(self, quadratureno, axis):
        '''
        selects the axis for use with this trigger in/out pair. quadratureno: number of addressed quadrature unit (0-2)
        '''
        ANC350lib.positionerQuadratureAxis(self.handle,quadratureno,axis)

    def quadratureInputPeriod(self, quadratureno, period):
        '''
        selects the stepsize the controller executes when detecting a step on its input AB-signal. quadratureno: number of addressed quadrature unit (0-2). period: stepsize in unit of actor * 1000
        '''
        ANC350lib.positionerQuadratureInputPeriod(self.handle,quadratureno,period)

    def quadratureOutputPeriod(self, quadratureno, period):
        '''
        selects the position difference which causes a step on the output AB-signal. quadratureno: number of addressed quadrature unit (0-2). period: period in unit of actor * 1000
        '''
        ANC350lib.positionerQuadratureOutputPeriod(self.handle,quadratureno,period)

    def resetPosition(self, axis):
        '''
        sets the origin to the actual position
        '''
        ANC350lib.positionerResetPosition(self.handle,axis)

    def sensorPowerGroupA(self, state):
        '''
        switches power of sensor group A. Sensor group A contains either the sensors of axis 1-3 or 1-2 dependent on hardware of controller
        '''
        ANC350lib.positionerSensorPowerGroupA(self.handle,ctypes.c_bool(state))

    def sensorPowerGroupB(self, state):
        '''
        switches power of sensor group B. Sensor group B contains either the sensors of axis 4-6 or 3 dependent on hardware of controller
        '''
        ANC350lib.positionerSensorPowerGroupB(self.handle,ctypes.c_bool(state))

    def setHardwareId(self, hwid):
        '''
        sets the hardware ID for the device (used to differentiate multiple devices)
        '''
        ANC350lib.positionerSetHardwareId(self.handle,hwid)

    def setOutput(self, axis, state):
        '''
        activates/deactivates the addressed axis
        '''
        ANC350lib.positionerSetOutput(self.handle,axis,ctypes.c_bool(state))

    def setStopDetectionSticky(self, axis, state):
        '''
        when enabled, an active stop detection status remains active until cleared manually by .clearStopDetection()
        '''
        ANC350lib.positionerSetStopDetectionSticky(self.handle,axis,state)

    def setTargetGround(self, axis, state):
        '''
        when enabled, actor voltage set to zero after closed-loop positioning finished
        '''
        ANC350lib.positionerSetTargetGround(self.handle,axis,ctypes.c_bool(state))

    def setTargetPos(self, axis, pos, rotcount=0):
        '''
        sets target position for use with .moveAbsoluteSync()
        '''
        ANC350lib.positionerSetTargetPos(self.handle,axis,pos,rotcount)

    def singleCircleMode(self, axis, state):
        '''
        switches single circle mode. In case of activated single circle mode the number of rotations are ignored and the shortest way to target position is used. Only relevant for rotary actors.
        '''
        ANC350lib.positionerSingleCircleMode(self.handle,axis,ctypes.c_bool(state))

    def staticAmplitude(self, amp):
        '''
        sets output voltage for resistive sensors
        '''
        ANC350lib.positionerStaticAmplitude(self.handle,amp)

    def stepCount(self, axis, stps):
        '''
        configures number of successive step scaused by external trigger or manual step request. steps = 1 to 65535
        '''
        ANC350lib.positionerStepCount(self.handle,axis,stps)

    def stopApproach(self, axis):
        '''
        stops approaching target/relative/reference position. DC level of affected axis after stopping depends on setting by .setTargetGround()
        '''
        ANC350lib.positionerStopApproach(self.handle,axis)

    def stopDetection(self, axis, state):
        '''
        switches stop detection on/off
        '''
        ANC350lib.positionerStopDetection(self.handle,axis,ctypes.c_bool(state))

    def stopMoving(self, axis):
        '''
        stops any positioning, DC level of affected axis is set to zero after stopping.
        '''
        ANC350lib.positionerStopMoving(self.handle,axis)

    def trigger(self, triggerno, lowlevel, highlevel):
        '''
        sets the trigger thresholds for the external trigger. triggerno is 0-5, lowlevel/highlevel in units of actor * 1000
        '''
        ANC350lib.positionerTrigger(self.handle,triggerno,lowlevel,highlevel)

    def triggerAxis(self, triggerno, axis):
        '''
        selects the corresponding axis for the addressed trigger. triggerno is 0-5
        '''
        ANC350lib.positionerTriggerAxis(self.handle,triggerno,axis)

    def triggerEpsilon(self, triggerno, epsilon):
        '''
        sets the hysteresis of the external trigger. epsilon in units of actor * 1000
        '''
        ANC350lib.positionerTriggerEpsilon(self.handle,triggerno,epsilon)

    def triggerModeIn(self, mode):
        '''
        selects the mode of the input trigger signals. state: 0 disabled - inputs trigger nothing, 1 quadrature - three pairs of trigger in signals are used to accept AB-signals for relative positioning, 2 coarse - trigger in signals are used to generate coarse steps
        '''
        ANC350lib.positionerTriggerModeIn(self.handle,mode)

    def triggerModeOut(self, mode):
        '''
        selects the mode of the output trigger signals. state: 0 disabled - inputs trigger nothing, 1 position - the trigger outputs reacts to the defined position ranges with the selected polarity, 2 quadrature - three pairs of trigger out signals are used to signal relative movement as AB-signals, 3 IcHaus - the trigger out signals are used to output the internal position signal of num-sensors
        '''
        ANC350lib.positionerTriggerModeOut(self.handle,mode)

    def triggerPolarity(self, triggerno, polarity):
        '''
        sets the polarity of the external trigger, triggerno: 0-5, polarity: 0 low active, 1 high active
        '''
        ANC350lib.positionerTriggerPolarity(self.handle,triggerno,polarity)

    def updateAbsolute(self, axis, position):
        '''
        updates target position for a *running* approach. function has lower performance impact on running approach compared to .moveAbsolute(). position units are in 'unit of actor multiplied by 1000' (generally nanometres)
        '''
        ANC350lib.positionerUpdateAbsolute(self.handle,axis,position)

def bitmask(input_array):
    '''
    takes an array or string and converts to integer bitmask; reads from left to right e.g. 0100 = 2 not 4
    '''
    total = 0
    for i in range(len(input_array)):
        if int(input_array[i]) != 0 and int(input_array[i])!=1:
            raise Exception('nonbinary value in bitmask, panic!')
        else:
            total += int(input_array[i])*(2**(i))
    return total

def debitmask(input_int,num_bits = False):
    '''
    takes a bitmask and returns a list of which bits are switched; reads from left to right e.g. 2 = [0, 1] not [1, 0]
    '''
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
    from hyperion import _logger_format

    import time

    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

    with Anc350() as anc:
        anc.initialize()

        #-------------------------------
        #controlling the stepper
        #-------------------------------

        #filename = 'C:\\Program Files\\Attocube positioners\\ANC350_GUI\\general_APS_files\\ANPx101res.aps'
        filename = 'q'
        anc.load(0, filename)

        ax = {'x': 0, 'y': 1, 'z': 2}
        # define a dict of axes to make things simpler

        # instantiate positioner as anc
        print('-------------------------------------------------------------')
        print('capacitances:')
        for axis in sorted(ax.keys()):
            print(axis, anc.capMeasure(ax[axis]))
        print('-------------------------------------------------------------')
        # print('setting static amplitude to 2V')
        # anc.staticAmplitude(2000)
        # # set staticAmplitude to 2V to ensure accurate positioning info
        # print('-------------------------------------------------------------')


        #for closed loop positioning the Amplitude Control needs to be set in Step Width mode, nr. 2
        print('setting Amplitude Control to StepWidth mode, which seems to be the close loop one')
        anc.amplitudeControl(0,2)

        #you need to set the amplitude, max 60V
        #at room temperature you need 30V for x and y and 40V for z
        #at low temperature that is higher, 40V or even 50V
        #higher amplitude influences step size though
        anc.amplitude(0,30000)      #30V
        print('amplitude is ',anc.getAmplitude(0),'mV')

        print('so the step width is ',anc.getStepwidth(0),'nm')


        #you also need to set the frequency
        #higher means more noise and faster (= less precise?)
        anc.frequency(0,1000)
        print('frequency is ',anc.getFrequency(0),'Hz')

        print('so the speed is ',anc.getSpeed(0),'nm/s')


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

        # #nr. 2: with a step, the stepwidth was determined by the amplitude and frequency
        # #so the step is order of magnitude 300 nm
        #
        # print('-------------------------------------------------------------')
        # print('moving 10 single steps of stepwidth, determined by set amplitude and frequency')
        #
        # #forward 0, backward 1
        # #but you have to give it time, because it won't tell you that it's not finished moving yet
        # for ii in range(10):
        #     anc.moveSingleStep(0,0)
        #     time.sleep(0.5)
        #     print(ii,': we are now at ',anc.getPosition(0),'nm')
        #
        # #nr. 3: with a step that you give it by ordering a relative move
        # #but this one takes a very long time
        #
        # print('-------------------------------------------------------------')
        # print('moving to a relative position, 5um back')
        # anc.moveRelative(0,-5000)
        #
        # time.sleep(1)
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
        #     time.sleep(1)
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
        #
        #
        # #-------------------------------
        # #controlling the scanner
        # #-------------------------------
        #
        # # filename = 'q'
        # # anc.load(0, filename)
        #
        #
        # #you need to set the mode to INT
        # #this means you can apply a voltage of 0-140V to the piezo
        #
        # print('-------------------------------------------------------------')
        # print('now we start with the SCANNER')
        # anc.intEnable(3,True)
        # print('is the scanner on INT mode? ',anc.getIntEnable(3))
        #
        # #this one has only one way to make a step: put a voltage
        #
        # print('-------------------------------------------------------------')
        # print('moving something by putting 50V')
        # anc.dcLevel(0,50000)
        # print('put a DC level of ',anc.getDcLevel(0),'mV')
        # print('no way of knowing when and if we ever arrive')
        #
        # #but no idea how we know whether it arrived at its position







