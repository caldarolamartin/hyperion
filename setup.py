import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Hyperion",
    version="0.1.dev",
    author="See Authors",
    license='BSD',
    description="A small package to control devices in the Kuipers lab",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/nanooptics-code/hyperion.git",
    python_requires='>=3.7',
    packages=setuptools.find_packages(),
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
        'pyserial'],
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