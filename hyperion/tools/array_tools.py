
import logging
import numpy as np
from hyperion import Q_



def array_from_pint_quantities(start, stop, step=None, num=None):
    """
    Generates an array from pint values.
    Use either step or num to divide the range up in steps. (If both are specified, step is used)
    Using num works similar to numpy.linspace(start, stop, num).
    Using step works somewhat similar numpy.arange(start, stop, step). Modifications are that the sign of step will be
    interpreted automatically. And the issue of a missing endpoint due to tiny floating point errors is mitigated.
    It returns a numpy array and the pint unit.

    :param start: The start value of the array
    :type start: pint.quantity
    :param stop: The end value for determining the array
    :type start: pint.quantity
    :param step: The stepsize between points
    :type start: pint.quantity
    :param num: Number of points generate
    :type start: int
    :return: The array and the unit
    :rtype: (numpy.array, pint.unit)
    """
    logger = logging.getLogger(__name__)

    unit = start.u
    sta = start.m_as(unit)
    sto = stop.m_as(unit)       # if stop doesn't have the same units as start it will result in an error

    if step != None:
        ste = step.m_as(unit)   # if step doesn't have the same units as start it will result in an error
        # fixing sign:
        if sto<ste and ste>0:
            ste = -ste

        # Tiny floating point errors sometimes cause the end-point not to be included. To mitigate this add a tiny
        # fraction times the step to the endpoint:
        sto += ste/1e9
        arr = np.arange(sta, sto, ste, float)

        # If the endpoint is almost equal to stop, just replace it with stop:
        if abs(sto - arr[-1]) < abs(ste*1e-9):
            arr[-1] = sto

    else:
        if num==None:
            logger.warning('Specify either step or num')
            arr = np.array([sta,sto])
        else:
            arr = np.linspace(sta,sto,num)

    return arr, unit

def array_from_string_quantities(start, stop, step=None, num=None):
    """
    Wrapper around array_from_pint_quantities() that converts string arguments to pint quantities.
    Arguments start, stop and step should be strings, num could be integer (or string of integer).
    See array_from_pint_quantities() for further details.
    """
    sta = Q_(start)
    sto = Q_(stop)
    if step == None:
        ste = None
    else:
        ste = Q_(step)

    return array_from_pint_quantities(sta, sto, ste, num)

def array_from_settings_dict(sweep_dict):
    """
    Wrapper around array_from_string_quantities().
    sweep_dict should contain 'start' and 'stop' key. And either 'step' or 'num' key.
    The values may have units (that can be interpreted by pint).
    See array_from_string_quantities() and array_from_pint_quantities() for further details.

    :param sweep_dict: Dictionary containing start, stop and step or num keys
    :return: (numpy.array, pint.unit)
    """
    if 'start' not in sweep_dict:
        logger.error('sweep dictionary should contain key start')
    if 'stop' not in sweep_dict:
        logger.error('sweep dictionary should contain key stop')
    if 'step' in sweep_dict:
        return array_from_string_quantities(sweep_dict['start'], sweep_dict['stop'], step=sweep_dict['step'])
    elif 'num' in sweep_dict:
        return array_from_string_quantities(sweep_dict['start'], sweep_dict['stop'], num=sweep_dict['num'])
    else:
        return array_from_string_quantities(sweep_dict['start'], sweep_dict['stop'])
