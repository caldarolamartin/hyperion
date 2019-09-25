# -*- coding: utf-8 -*-
"""
=====================
Beam Flags Instrument
=====================

Instrument for homebuilt Arduino based beam flags.
Designed to work with Arduino running:
    qnd_simple_double_flag_controller.ino
    "QND Simple Double Flag Controller, version 0.1, date 2019-09-17"

"""
import logging
from hyperion.instrument.base_instrument import BaseInstrument
import time
from hyperion import ur

class BeamFlagsInstr(BaseInstrument):
    """ Example instrument. it is a fake instrument

    """
    def __init__(self, settings = {'port':'COM4', 'dummy': True,
                                   'controller': 'hyperion.controller.generic.generic_serial/GenericSerialController'}):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Class BeamFlags created.')

        self.settings = settings

        # temporary lines for auto completion while developing:
        from hyperion.controller.generic.generic_serial_contr import GenericSerialController
        self.controller = GenericSerialController(settings={'port':'COM4'})

        # Note that flag names need to be 1 character long
        if 'flag_names' not in self.settings:
            self.settings['flag_names'] = ['1','2']

        # Note that flag states need to be 1 character long
        if 'states' not in self.settings:
            self.settings['states'] = ['r','g'];

        self.flag_states = {}
        for name in self.settings['flag_names']:
            self.flag_states[name] = None

        if 'actuator_timeout' not in self.settings:
            self.settings['actuator_timeout'] = 0.3;

        # In order to keep track of the state of the flags (because they can be altered outside
        # the control of the python code), one could keep sending queries to the device, but I
        # recommend this alternative method:
        # If self._use_passive_queries is True, the Arduino will send new state info when the
        # state is altered through toggle button. This instrument will then read this state
        # information from the Serial Buffer In whenever the state is required.
        self._use_passive_queries = False  # True recommended

    def initialize(self):
        """ Starts the connection to the device"
        """
        self.logger.debug('Opening connection to device.')
        self.controller.initialize()
        time.sleep(1.6)
        #self.controller.read_lines()

        #__use_passive_queries = self._use_passive_queries
        #self._use_passive_queries = False
        self.update_all_states()
        self._announce(self._use_passive_queries) # make sure "announce" is true


    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.debug('Closing connection to device.')
        self.controller.finalize()

    def idn(self):
        """ Identify command

        :return: identification for the device
        :rtype: string

        """
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn()

    def _announce(self, state):
        """
        Setting announce true in the Arduino, makes sure it will write
        toggle states to the serial buffer when they're changed manually.

        :param state: True of False
        :type state: bool
        """

        if state:
            self.controller.write('at')
        else:
            self.controller.write('af')

        self._use_passive_queries = state

    def update_all_states(self):
        """
        Queries all flag states and updates this Instruments internal flag states.
        Returns if any internal state has changed.

        :return: true if any state has changed
        :rtype: bool
        """

        changed = False
        for key in self.flag_states:
            before = self.flag_states[key]
            after = self.get_specific_flag_state(key)
            if after != before:
                changed = True

        self.logger.debug('changes while updating all states = {}'.format(changed))

        return changed

    def get_specific_flag_state(self, flag_name):
        """
        Query the state of a specific flag.
        Also updates this Instruments internal state
        if the flag name occurs in the dictionary.
        (Does not check for valid flag_name)

        :param flag_name: the name of the flag
        :type flag_name: string
        :return: state of the flag
        :rtype: string
        """

        # If _use_passive_queries: don't actively query but rely on "passive updates"
        if flag_name in self.flag_states:
            if self._use_passive_queries and self.flag_states[flag_name] in self.settings['states']:
                changed = self.passive_update_from_manual_changes()
                return self.flag_states[flag_name]

        state = self.controller.query(flag_name + '?')
        if len(state):
            state = state[-1]
        else:
            state = None
        if flag_name in self.flag_states:
            self.flag_states[flag_name] = state
        return state

    def passive_update_from_manual_changes(self):
        """
        When toggle switches are manually changed, the arduino
        will send messages like 1g or 2r.
        This method will read the Serial buffer in and update this
        Instruments internal state of the flags according to the
        last states found in the buffer.

        :return: if it changed any state
        :rtype: bool
        """
        lines_list = self.controller.read_lines()

        changed = False
        for name in self.settings['flag_names']:
            state_lines = [line for line in lines_list if (len(line) == 2 and line[0]==name and line[1] in self.settings['states'])]
            if len(state_lines):
                current_state = state_lines[-1][1]
                if self.flag_states[name] != current_state:
                    changed = True
                    self.flag_states[name] = current_state

        return changed

    def set_specific_flag_state(self, flag_name, flag_state):
        """
        INCOMPLETE
        NO CHECKS YET
        :param flag_name:
        :param flag_state:
        :return:
        """

        if self._use_passive_queries:
            changed = self.passive_update_from_manual_changes()
            if self.flag_states[flag_name] == flag_state:
                return

        self.controller.write(flag_name+flag_state)

    # Custom methods that assume the names of the flags are numbers.
    # The first state listed in settings['states'] will be converted to False
    # The second state listed in settings['states'] will be converted to True

    def set_flag(self, flag_number, bool_state):
        """
        Set flag using its number an bool state.

        :param flag_number:
        :type flag_number: int
        :param bool_state: flag state (True for 'g', False for 'r')
        :type bool_state: bool
        :return:
        """

        self.set_specific_flag_state(str(flag_number), self.settings['states'][1] if bool_state else self.settings['states'][0])

    def get_flag(self, flag_number):
        """
        Get flag state as bool. Identify flag by its number (in stead of string)

        :param flag_number: The number indicating the flag
        :type flag_number: int
        :return: True for 'g' and False for 'r', (None for other)
        """
        bool_state = None
        state = self.get_specific_flag_state( str(flag_number) )
        if state == self.settings['states'][1]:
            bool_state = True
        elif state == self.settings['states'][0]:
            bool_state = False
        return bool_state

    @property
    def f1(self):
        """
        """
        return self.get_flag(1)

    @f1.setter
    def f1(self, bool_state):
        self.set_flag(1,bool_state)

    @property
    def f2(self):
        """
        """
        return self.get_flag(2)

    @f2.setter
    def f2(self, bool_state):
        self.set_flag(2,bool_state)


if __name__ == "__main__":
    from hyperion import _logger_format, _logger_settings
    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    dummy = [False]
    for d in dummy:
        with BeamFlagsInstr(settings = {'port': 'COM4', 'dummy' : d,
                                   'controller': 'hyperion.controller.generic.generic_serial/GenericSerialController'}) as bf:
            bf.initialize()
            print( bf.idn() )
            bf.set_specific_flag_state('1','r')
            print( bf.get_specific_flag_state('1') )
            time.sleep( bf.settings['actuator_timeout'] )
            bf.set_flag(1, True)
            print( bf.get_flag(1))
            time.sleep(bf.settings['actuator_timeout'])
            bf.f1 = False
            print(bf.f1)
            time.sleep(bf.settings['actuator_timeout'])
            start_time = time.time()
            while (time.time() - start_time < 10):
                print(bf.flag_states)
                time.sleep(.2)
                if bf.passive_update_from_manual_changes():
                    print(bf.flag_states)


    print('done')