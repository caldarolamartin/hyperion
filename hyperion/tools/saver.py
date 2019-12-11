# -*- coding: utf-8 -*-
"""

WORK IN PROGRESS <<<<<<<<<<<<<<<<<<<<<<<<<<

Created on Mon Dec  2 13:33:11 2019

@author: aopheij


The idea for saving is to have:
    - One BaseSaver class that holds only basic functionality and version compatability.
    - Multiple different versions classes that can inherit from BaseSaver and from eachother.
    - One wrapper function that returns the right saver version.

from hyperion.tools import Saver
datastore = Saver('filename.h5', version=0.1)

"""
# import hyperion
import os
import logging
import h5py
import time

from hyperion.tools.saving_tools import name_incrementer

class BaseSaver:
    """
    Base class to handle a few basic
    """

    # Default version to use
    default_version = 0.1

    # Valid version identifier floats:
    #    valid_versions = [0.1, 0.02, 0.01]
    # Compatability: per version specify which range of old (and new) versions are silimar enough
    #    file_version_compatability = {
    #            0.10: valid_versions,
    #            0.02: [v for v in valid_versions if 0.01<=v<=0.02],
    #            0.01: [0.01] }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('BaseSaver init')

    @classmethod
    def valid_versions(cls):
        """ Returns dictionary of valid versions of Saver classes. """
        valid = {}
        for sub in BaseSaver.__subclasses__():
            valid[sub.version] = sub
        return valid

    @classmethod
    def compatible(cls, v1, v2):
        """ Returns tuple of two bools
        (v2 is in backward compatibility list of v1, v2 is in forward compatibility list of v1)
        """
        valid = BaseSaver.valid_versions()
        if v1 not in valid.keys():
            raise Exception('{} is not a known valid version'.format(v1))
        if v2 not in valid.keys():
            raise Exception('{} is not a known valid version'.format(v2))
        b1 = valid[v1].backward_compatible
        # If the compatibility list b1 is str 'all', then generate list of all lower valid number:
        if type(b1) is str and b1[0].lower() == 'a':
            b1 = [v for v in sorted(valid.keys()) if v < v1]
        f1 = valid[v1].forward_compatible
        # If the compatibility list f1 is str 'all', then generate list of all higher valid number
        if type(f1) is str and f1[0].lower() == 'a':
            f1 = [v for v in sorted(valid.keys()) if v > v1]
        # Make sure that a version is compatible with itself:
        b1.append(v1)
        f1.append(v1)
        return v2 in b1, v2 in f1

    @classmethod
    def test_file(self, folder, filename=None):
        """
        Tests if file exist and if it's hyperion type:
        Returns None if folder doesn't exist
        Returns 0 if file doesn't exist
        Returns -1 if file exist and can't be read or is not hyperion type
        Returns hyperion version number if file exist and is of hyperion type

        :param folder: (str) the folder or the full path (if no filename given)
        :param filename: (str) filename (or omit if already included in folder)
        :return: (int of float) status or version number
        """
        if filename is None:
            filename = os.path.basename(folder)
            if '.' in filename:
                folder = os.path.dirname(folder)
            else:
                raise 'A complete path or a folder and filename is required'

        # Just in case the folder is actually a file:
        if os.path.isfile(folder):
            self.logger.warning('Folder is actually a file.')
            return None
        if not os.path.isdir(folder):
            return None
        file_path = os.path.join(folder, filename)
        if not os.path.isfile(file_path):
            return 0
        else:
            try:
                h5 = h5py.File(file_path, 'r')
                if 'hyperion_file_version' in h5.attrs:
                    status = h5.attrs['hyperion_file_version']
                else:
                    status = -1
                h5.close()
            except:
                status = -1
        return status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.h5.close()

    def close(self):
        self.h5.close()


def Saver(*args, version=BaseSaver.default_version, **kwargs):
    """
    Wrapper to use different classes based on the version.
    If an unknown version is specified, the newest will be used.
    See the different versions for details on how to use them.
    """
    # Get all child classes of BaseSaver and their version number:
    versions = [cl.version for cl in BaseSaver.__subclasses__()]
    if version not in versions:
        invalid = version
        version = sorted(versions)[-1]
        logging.getLogger(__name__).warning('Unknown version {}, using {} instead'.format(invalid, version))
    return BaseSaver.__subclasses__()[versions.index(version)](*args, **kwargs)


class Saver_v0p1(BaseSaver):
    # IMPORTANT: When inheriting from other version, ALSO inherit from BaseSaver
    version = 0.1  # mandatory unique identification float
    # Specify version compatibilities (list of floats or 'all' or [])
    backward_compatible = 'all'
    forward_compatible = [0.2]

    def __init__(self, *args, write_mode = None, incrementor_settings = {}, default_folder = None, default_filename=None, **kwargs):
        super().__init__()
        self.logger.debug('init v0.1')
        self.__write_modes = ['increment', 'append_if_possible', 'overwrite', 'fail']
        self._default_write_mode = ['increment']
        self._write_mode = self._default_write_mode
        if write_mode is not None:
            self.write_mode = write_mode
        self.__file_is_open = False
        self.__append = False
        self.incrementor_settings = incrementor_settings
        self.default_folder = default_folder
        self.default_filename = default_filename


    @property
    def write_modes(self):
        return self.__write_modes

    @property
    def write_mode(self):
        return self._write_mode

    @write_mode.setter
    def write_mode(self, modes):
        if modes is None:
            self._write_mode = self._default_write_mode
            return
        elif type(modes) is str:
            modes = [modes]
        ret = []
        for m in modes:
            wmod = [wm for wm in self.__write_modes if wm[:len(m)]==m]
            if len(wmod)==0:
                self.logger.warning('{} is not a recognized mode. ignoring'.format(m))
            else:
                ret.append(wmod[0])
        if len(ret):
            self._write_mode = ret
        else:
            self.logger.warning('existing_file_mode not changed')

    def close(self):
        self.h5.close()
        self.__file_is_open = False
        self.__append = False

    def open_file(self, folder=None, filename=None):
        """

        :param folder: (str)
        :param filename: (str)
        :return: (bool) indicating file is open
        """

        if self.__file_is_open:
            self.logger.warning('First closing open file: {}'.format(self.filename))
            self.close()

        self.folder = self.default_folder if folder is None else folder
        if self.folder is None:
            self.logger.error('Folder and file need to be specified (either in open_file() or as default saver object')
            raise FileNotFoundError
        if filename is None:
            self.filename = os.path.basename(self.folder)
            if '.' in self.filename:
                self.folder = os.path.dirname(self.folder)
            else:
                self.filename = self.default_filename
            if self.filename is None:
                self.logger.error('Folder and file need to be specified (either in open_file() or as default saver object')
                raise FileNotFoundError
        else:
            self.filename = filename

        # In case use_number_for_first was not None:
        for wm in self._write_mode:
            if wm == 'fail' or wm == 'overwrite':
                break
            elif wm == 'increment':
                self.filename = name_incrementer(self.filename, [], **self.incrementor_settings)


        status = BaseSaver.test_file(self.folder, self.filename)
        if status is None:
            self.logger.debug('Creating directory: {}'.format(self.folder))
            os.makedirs(self.folder)
            status = 0
        if status > 0 and status not in BaseSaver.valid_versions():
            self.logger.warning('Existing file is of unknown hyperion format')
            status = -1
        if status:
            for wm in self._write_mode:
                if wm == 'fail':
                    status = -2
                    break
                elif wm == 'overwrite':
                    self.logger.info('Overwriting file: {}'.format(self.filename))
                    status = 0
                    break
                elif wm=='increment':
                    self.filename = name_incrementer(self.filename, os.listdir(self.folder), **self.incrementor_settings)
                    self.logger.info('New filename: {}'.format(self.filename))
                    status = 0
                    break
                elif status > 0 and wm == 'append_if_possible':
                    if  any(BaseSaver.compatible(self.version, status)):
                        self.logger.info('Opened existing file with intention to append: {}'.format(self.filename))
                        self.h5 = h5py.File(os.path.join(self.folder, self.filename), 'a')
                        self.h5.attrs['hyperion_file_version_append'] = self.version
                        self.__file_is_open = True
                        self.__append = True
                        return True
                    else:
                        self.logger.info("Incompatible: Saver version={} can't write to file of version={}".format(self.version, status))
                status = -2  # end of write_mode list reached without finding a solution
        if status == 0:
            self.h5 = h5py.File(os.path.join(self.folder, self.filename), 'w')
            self.h5.attrs['hyperion_file_version'] = self.version
            self.__file_is_open = True
            self.logger.debug('File created: {}'.format(self.filename))
            return True
        elif status == -2:
            self.logger.warning("File not opened")
            return False


class Saver_v0p2(Saver_v0p1, BaseSaver):
    # IMPORTANT: When inheriting from other version, ALSO inherit from BaseSaver
    version = 0.2  # mandatory unique identification float
    # Specify version compatibilities (list of floats or 'all' or [])
    backward_compatible = 'all'
    forward_compatible = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('init v0.2')


if __name__=='__main__':
    import os.path
    import hyperion

    folder = os.path.join(hyperion.parent_path, 'data')
    filename = 'test_02.h5'

    s = Saver(version=0.1)
    s = Saver(0.1)
