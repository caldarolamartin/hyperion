# -*- coding: utf-8 -*-
"""
    ============
    Cobolt 08NLD
    ============
    This is the controller for the Cobotl laser 08NLD


    Based on the driver for laser 06-01 series by Vasco Tenner, available in lantz.drivers.laser.cobolt08NLD

    :copyright: 2020by Hyperion Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from pyvisa import constants
from lantz.core import Action, Feat
from lantz.core import MessageBasedDriver
import lantz.core.log


class Cobolt08NLD(MessageBasedDriver):
    """
    controller class for the driver COBOLT 08-NLD Series laser.
    This class has all the methods to communicate using serial.


    """
    DEFAULTS = {'ASRL': {'write_termination': '\r',
                         'read_termination': '\r',
                         'baud_rate': 115200,
                         #'databits': 8,
                         'parity': constants.Parity.none,
                         'stop_bits': constants.StopBits.one,
                         'encoding': 'ascii',
                         }}

    @Feat(read_once=True)
    def idn(self):
        """Get serial number
        """
        ans = self.query('gsn?')[1:]
        sn = ans
        return dict(manufacturer='COBOLT', model='08-NLD', serialno=sn, softno='N/A', wavelength=785)

    def initialize(self):
        super().initialize()
        self.mode = 'PC'
        self.ctl_mode = self.mode

    # ENABLE LASER METHODS
    @Feat(values={True: '1', False: '0'})
    def enabled(self):
        """Method for turning on the laser. Requires autostart disabled.
        """
        ans = self.query('l?')
        return ans[-1]

    @enabled.setter
    def enabled(self, value):
        self.query('l' + value)

    @Feat(values={True: '1', False: '0'})
    def autostart(self):
        """Autostart handling
        """
        ans = self.query('@cobas?')
        return ans[-1]

    @autostart.setter
    def autostart(self, value):
        self.query('@cobas ' + value)

    @Action()
    def restart(self):
        """Forces the laser on without checking if autostart is enabled.
        """
        self.query('@cob1')

    @Feat(values={True: '1', False: '0'})
    def ksw_enabled(self):
        """Handling Key Switch enable state
        """
        ans = self.query('@cobasky?')
        return ans[1:]

    @ksw_enabled.setter
    def ksw_enabled(self, value):
        """ Key switch status

        """
        self.query('@cobasky ' + value)

    # LASER INFORMATION METHODS
    @Feat()
    def operating_hours(self):
        """Get Laser Head operating hours
        """
        return self.query('hrs?')[1:]

    @Feat(values={'Interlock open': '1', 'OK': '0'})
    def interlock(self):
        """Get interlock state
        """
        return self.query('ilk?')[1:]

    # LASER'S CONTROL MODE AND SET POINT

    @Feat(values={'PC', 'CC'})
    def ctl_mode(self):
        """To handle laser control modes: PC means constant power and CC constant current
        """
        return self.mode

    @ctl_mode.setter
    def ctl_mode(self, value):
        if value == 'CC':
            self.query('ci')
            self.mode = 'CC'
        elif value == 'PC':
            self.mode = 'PC'
            self.query('cp')

    @Feat(units='mA')
    def current_sp(self):
        """Get drive current
        """
        return float(self.query('i?'))

    @current_sp.setter
    def current_sp(self, value):
        self.query('slc {:.1f}'.format(value))

    @Feat(units='mW')
    def power_sp(self):
        """To handle output power set point (mW) in constant power mode
        """
        return 1000 * float(self.query('p?'))

    @power_sp.setter
    def power_sp(self, value):
        self.query('p {:.5f}'.format(value / 1000))

    # LASER'S CURRENT STATUS

    @Feat(units='mW')
    def power(self):
        """Read output power
        """
        return 1000 * float(self.query('pa?'))

    @Feat(values={'Temperature error': '1', 'No errors': '0',
                  'Interlock error': '3', 'Constant power time out': '4'})
    def status(self):
        """Get operating fault
        """
        return self.query('f?')[1:]

    @Action()
    def clear_fault(self):
        """Clear fault
        """
        self.query('cf')

    # MODULATION MODES
    @Action()
    def enter_mod_mode(self):
        """Enter modulation mode
        """
        self.query('em')

    @Feat(values={True: '1', False: '0'})
    def digital_mod(self):
        """digital modulation enable state
        """
        return self.query('gdmes?')[1:]

    @digital_mod.setter
    def digital_mod(self, value):
        self.query('gdmes ' + value)

    @Feat(values={True: '1', False: '0'})
    def analog_mod(self):
        """analog modulation enable state
        """
        return self.query('games?')[1:]

    @analog_mod.setter
    def analog_mod(self, value):
        self.query('sames ' + value)

    @Feat(values={True: '1', False: '0'})
    def analogli_mod(self):
        """analog modulation enable state
        """
        return self.query('galis?')[1:]

    @analogli_mod.setter
    def analogli_mod(self, value):
        self.query('salis ' + value)

    @Feat(values={'Waiting for key': '1', 'Off': '0', 'Continuous': '2',
                  'On/Off Modulation': '3', 'Modulation': '4', 'Fault': '5',
                  'Aborted': '6'})
    def mod_mode(self):
        """Returns the current operating mode
        """
        return self.query('gom?')[1:]

if __name__ == '__main__':
    lantz.log.log_to_screen(lantz.log.DEBUG)
    from hyperion import Q_
    from lantz.qt import start_test_app

    with Cobolt08NLD.via_serial('5') as inst:

        print('Identification: {}'.format(inst.idn))
        print('Enabled = {}'.format(inst.enabled))
        print('used hours = {} hs'.format(inst.operating_hours))
        print('Laser mode: {}'.format(inst.ctl_mode))
        print('Laser interlock state: {}'.format(inst.interlock))
        print('Autostart status: {}'.format(inst.autostart))
        print('Power setpoint: {}'.format(inst.power_sp))
        inst.power_sp = Q_(150,'milliwatt')
        print('Power setpoint: {}'.format(inst.power_sp))
        inst.power_sp = 200
        print('Power setpoint: {}'.format(inst.power_sp))
        print('Output power now: {}'.format(inst.power))

        # this is to get an automatic GUI to test the code
        start_test_app(inst)
