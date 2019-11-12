# -*- coding: utf-8 -*-
"""
============
Saving tools
============

This is a collection of useful methods used along hyperion.

NOT DONE YET

"""
from hyperion import root_dir, ur
import os
import sys


def name_incrementer(basename, list_of_existing, separator='_', fill_zeros=0, use_number_for_first=None,
                     only_larger_number=True):
    """
    This function is meant to avoid rewriting existing files.

    :param basename: The basename. May include extension.
    :param list_of_existing: List of names to avoid
    :param separator: Optional separator between basename and number, DEFAULT is '_'
    :param fill_zeros: If you set this to 4, numbers will look like 0012, 0013. Special case 0 (DEFAULT) will match the longest one in list_of_existing
    :param use_number_for_first: 0, 1, None. If the name does not occur yet it will get 0, 1 or no sufix, DEFAULT is None
    :param only_larger_number: If name_1 and name_3 exist and only_larger_number is True DEFAULT, name_4 will be suggested, otherwise name_2
    :return: The suggested name.
    """

    if basename.lower() in (name.lower() for name in list_of_existing):
        exact_match = True
    else:
        exact_match = False

    # identify and strip extension if there is one
    if '.' in basename:
        ext = '.' + basename.split('.')[-1].lower()
        extlen = len(ext)
        basename = basename[:(len(basename) - extlen)]
    else:
        ext = ''
        extlen = 0

    baselen = len(basename)
    seplen = len(separator)

    similar = [name.lower()[(baselen + seplen):(len(name) - extlen)] for name in list_of_existing if
               name.lower().startswith(basename.lower() + separator) and name.lower().endswith(ext)]

    # try to convert the suffixes to numbers
    # if succeeds: add the number to numbers, if fails: remove from similar list
    numbers = []
    maxlen = 0
    for index in range(len(similar) - 1, -1, -1):
        chunk = similar[index]
        try:
            numbers.insert(0, int(chunk))
            maxlen = max(maxlen, len(chunk))
        except:
            del (similar[index])

    if not exact_match:
        new_number = use_number_for_first
    else:
        new_number = 1

    if only_larger_number and len(numbers):
        new_number = max(numbers) + 1

    while new_number in numbers:
        new_number += 1

    if fill_zeros==0:
        fill_zeros = maxlen
    formatstring = separator + '{:0' + str(fill_zeros) + '}'
    if new_number is not None:
        basename += formatstring.format(new_number)

    return basename + ext


def create_filename(file_path):
    """ Creates the filename, so all the methods point to the same folder
    and save with the same name. The output does not include the extension but the input does.

    :param filename: config filename complete path (INCLUDING the extension)
    :type filename: string (path)

    :return: filename with a number appended so it would not be overwritten.
    :rtype: string

    """

    i = 0
    ext = file_path[-4:]  # Get the file extension (it assumes is a dot and three letters)
    filename = file_path[:-4]
    root_path = os.path.split(filename)[0]

    while os.path.exists(file_path):
        file_path = '{}_{:03}{}'.format(filename, i, ext)
        i += 1

    filename = file_path[:-4]

    return filename

def save_metadata(self):
    """ Saves the config file information with the same name as the data and extension .yml


    """
    self.create_filename(self.properties['config file'])

    self.logger.debug('Filename: {}'.format(self.filename))
    file_path = self.filename + '.yml'
    self.logger.debug('Complete file path: {}'.format(file_path))

    with open(file_path, 'w') as f:
        yaml.dump(self.properties, f, default_flow_style=False)

    self.logger.info('Metadata saved to {}'.format(file_path))


def save(self, data):
    pass
