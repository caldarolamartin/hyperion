""""
=====
Types
=====

This is a collection of types.
Note that DefaultDict and ActionDict are used by base_experiment, base_guis and saving_tools. Don't modify them!

:copyright: by Hyperion Authors, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.

"""
import copy
from hyperion import logging

class DefaultDict(dict):
    """
    Special dictionary (inherits from dict).
    When accessing key of this dict it will return obj.default_dict[key] if obj.main_dict[key] doesn't exist.
    Writing and deleting always act on main_dict.
    Methods like keys(), values(), items() act on the combined list (where main_dict supersedes default_dict in case of duplicate values).
    Original default_dict is never changed. Also attempted changes to default_dict after creation of obj are ignored.

    :param main_dict: primary dictionary
    :type main_dict: dict
    :param default_dict: dictionary with default values that will be returned if key is not present in main_dict (defaults to {})
    :type default_dict: dict
    :param ReturnNoneForMissingKey: flag indicating if None should be returned if an unknown key is requested (defaults to False)
    :type ReturnNoneForMissingKey: bool
    :returns: DefaultDict object which can mostly be used and accessed as a regular dict
    :rtype: DefaultDict object

    :Example:

    obj = DefaultDict(main_dict, [default_dict, , ReturnNoneForMissingKey] )
    """

    def __init__(self, main_dict, default_dict={}, ReturnNoneForMissingKey = False):
        # self.logger = logging.getLogger(__name__)
        self.__ReturnNoneForMissingKey = ReturnNoneForMissingKey
        self.__logger = logging.getLogger(__name__)
        combined = copy.deepcopy(default_dict)
        combined.update(main_dict)
        super().__init__(combined)

        self.main_dict = main_dict
        self.default_dict = copy.deepcopy(default_dict)


    def __getitem__(self, key):
        if key in self.main_dict:
            return self.main_dict[key]
        elif key in self.default_dict:
            return self.default_dict[key]
        elif self.__ReturnNoneForMissingKey:
            # self.__logger.debug('Key {} not in main and not in default: returning None because ReturnNoneForMissingKey=True'.format(key))
            return None
        else:
            # self.__logger.error('DefaultDict: key not found: {}'.format(key))
            raise KeyError(key)

    def __setitem__(self, key, value):
        self.main_dict[key] = value
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if key in self.main_dict:
            del self.main_dict[key]
        super().__delitem__(key)

    def __repr__(self):
        # return self.__dict__.__repr__()
        return {'main_dict':self.main_dict, 'default_dict':self.default_dict}.__repr__()

    def __str__(self):
        return self.__repr__().__str__()


class ActionDict(DefaultDict):
    def __init__(self, actiondict, types={}, exp=None):
        """
        Creates a DefaultDict from actiondict and actiontype (which can be passed through types or exp).
        When accessing a key of the ActionDict onbject returned it returns the value from actiondict if key is present.
        Otherwise value from actiontype if actiontype can be found and key is present. Otherwise returns None.
        Actiontypes can be passed in types or extracted from exp.
        Note: the actiondict must contain a key 'Type' that points to the name of the actiontype.
        Note: if both types and exp are specified, types is used.

        :param actiondict: dict following the Action dictionary format (typically retrieved from a Measurement in a config file)
        :type actiondict: dict
        :param types: dict of action type dicts containing default values. (typically retrieved from an ActionType in a config file) (optional, defaults to {})
        :type types: dict of dicts
        :param exp: experiment object containing .properties['ActionTypes']) (optional, defaults to None)
        :type types: BaseExperiment
        :returns: DefaultDict object which can mostly be used and accessed as a regular dict
        :rtype: DefaultDict object

        seealso:: DefaultDict
        """
        # self.logger = logging.getLogger(__name__)
        if types == {} and exp is not None:
            types = exp.properties['ActionTypes']

        if 'Type' in actiondict and actiondict['Type'] in types:
            actiontype = types[actiondict['Type']]
        else:
            actiontype = {}
        super().__init__(actiondict, actiontype, ReturnNoneForMissingKey=True)

