"""
========
UI tools
========

We group many functions useful for when building GUIS.

"""
import logging
from numpy import log10
from hyperion import Q_


def add_pint_to_combo(comboBox_units, manual_list=None):
    """
    When GUI has a QComboBox with units, this function can convert the display texts of the units to pint units and
    stores them inside the combobox object. (Run this function once).
    It is possible to manually specify the list to store, but it's safer to try automatic conversion.
    :param comboBox_units:
    :type comboBox_units: QComboBox
    :param manual_list: OPTIONAL list of pint units corresponding to the display units
    :type manual_list: list of pint units

    """
    logger = logging.getLogger(__name__)

    if manual_list is not None:
        comboBox_units.pint_units = manual_list
    else:
        # List of strings used in the combo box:
        units_combo = [comboBox_units.itemText(i) for i in range(comboBox_units.count())]
        # Try to convert the strings of the combo box to pint units:
        # If this fails user needs to fix it.
        try:
            # convert to pint units:
            pint_units = [Q_(un).units for un in units_combo]
            # logger.debug('{}'.format(units_pint))
        except:
            logger.error('Failed to convert units in combobox to pint units')
            raise ValueError
        try:
            # Try to convert all strings to the first unit. This will raise an error if it fails
            [Q_(un).m_as(pint_units[0]) for un in units_combo]
        except:
            logger.error('Combobox units appear not to be of the same dimensionality')
            raise ValueError

        comboBox_units.pint_units = pint_units

def pint_to_spin_combo(pint_quantity, doubleSpinBox, comboBox_units):
    """
    When a GUI has a combination of a Q(Double)SpinBox and a QComboBox that hold the numeric value and the unit
    respectively, this function can be used to easily put a pint quantity into  that combination.
    It is strongly recommended to use add_pint_to_combo(comboBox_units) before using this function!
    Complementary function is spin_combo_to_pint_apply_limits()

    :param pint_quantity: the pint quantity to write into the gui objects
    :type pint_quantity: pint quantity
    :param doubleSpinBox: the QDoubleSpinBox (or QSpinBox?) that holds the numeric value
    :type doubleSpinBox: QDoubleSpinBox (Maybe QSpinBox also works. Not tested)
    :param comboBox_units: the QComboBox that holds the units
    :type comboBox_units: QComboBox
    """

    if hasattr(comboBox_units, 'pint_units'):
        pint_units = comboBox_units.pint_units
    else:
        # otherwise try to create it on the fly:
        pint_units = [Q_(comboBox_units.itemText(i)).units for i in range(comboBox_units.count())]

    # Try to convert the pint quantity to one of the units in the comboBox.
    # If that succeeds set the combobox unit and the value in the doubleSpinBox
    try:
        # First try to match the combo unit to the one of pint_quantity:
        combo_index = pint_units.index(pint_quantity.units)
        value = pint_quantity.m_as(pint_units[combo_index])
    except ValueError:
        # If that fails find the unit that comes closest:
        v = list(log10([pint_quantity.m_as(un) for un in pint_units]))  # log10 of values converted to the combo units
        vp = [n for n in v if n >= 0]  # only the positive ones (i.e. prefer 200ms over 0.2s )
        if len(vp) == 0:  # if there are none, add the largest negative one
            vp = max(v)
        combo_index = v.index(min(vp))  # get the corresponding index

        # If that fails try to convert to one of the units in the middle of the list:
        # combo_index = int((len(combo_index) - 1) / 2) # OLD CODE
        try:
            value = pint_quantity.m_as(
                pint_units[combo_index])  # this will raise an error if the pint quantity is different dimensionality
        except ValueError:
            logger.error('Could not convert {} to one of: {}'.format(pint_quantity, units_pint))
            raise ValueError

    doubleSpinBox.setValue(value)
    comboBox_units.setCurrentIndex(combo_index)

def spin_combo_to_pint_apply_limits(doubleSpinBox, comboBox_units, pint_lower_limit=None, pint_upper_limit=None):
    """
    When a GUI has a combination of a Q(Double)SpinBox and a QComboBox that hold the numeric value and the unit
    respectively, this function can be used to convert the combined values to a pint quantity.
    In addition it applies limits if they are specified.
    Typically you'll make one function limit_and_apply_X in your gui code, and connect both

        >>> doubleSpinBox.valueChanged.connect(limit_and_apply_X)
        >>> comboBox_units.currentIndexChanged.connect(limit_and_apply_X)

    to this function. Inside limit_and_apply_X() you would use this function spin_combo_to_pint_apply_limits() to apply
    limits and convert it to a pint quantity

    It is strongly recommended to use add_pint_to_combo(comboBox_units) before using this function!
    Complementary function is pint_to_spin_combo()

    :param doubleSpinBox: Q(Double)SpinBox that holds the numeric value
    :param comboBox_units: QComboBox that holds the units
    :param pint_lower_limit: OPTIONAL pint quantity for the lower limit to apply
    :param pint_upper_limit: OPTIONAL pint quantity for the upper limit to apply
    :returns: pint quantity
    """

    logger = logging.getLogger(__name__)

    value = doubleSpinBox.value()
    combo_index = comboBox_units.currentIndex()

    # If available use the units_pint stored inside comboBox_units object (by pint_to_doubleSpin_plus_unit_combo)
    if hasattr(comboBox_units, 'pint_units'):
        pint_units = comboBox_units.pint_units
    else:
        # otherwise try to create it on the fly:
        pint_units = [Q_(comboBox_units.itemText(i)).units for i in range(comboBox_units.count())]

    new_quantity = value*pint_units[combo_index]
    logger.debug('new pint quantity: {}'.format(new_quantity))

    if pint_upper_limit is not None and new_quantity > pint_upper_limit:
        new_quantity = pint_upper_limit
        pint_to_spin_combo(new_quantity, doubleSpinBox, comboBox_units)

    if pint_lower_limit is not None and new_quantity < pint_lower_limit:
        new_quantity = pint_lower_limit
        pint_to_spin_combo(new_quantity, doubleSpinBox, comboBox_units)

    return new_quantity

