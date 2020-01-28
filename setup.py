import struct
import setuptools
version = '0.4'

# list of required packages
install_requires = [
        'numpy>=1.16',
        'scipy',
        'sphinx',
        'pyqtgraph==0.10.0',
        'lantz_core',
        'lantz_drivers',
        'lantz_qt',
        'lantz_sims',
        'pyvisa-py',
        'pyserial',
        'pynput'
        'netcdf4>=1.4',
        'pip>=19',
        'xarray']

# this is to check if the system is 32 or 64 bits and add the 32bit dependencies
if struct.calcsize("P")*8 ==32:
    install_requires.append('pywin32')

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Hyperion",
    version="{}".format(version),
    author="See Authors",
    license='BSD',
    description="A small python package to control devices in the Kuipers lab @ TU Delft",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/nanooptics-code/hyperion.git",
    python_requires='>=3.7',
    packages=setuptools.find_packages(),
    install_requires = install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
    ],
)