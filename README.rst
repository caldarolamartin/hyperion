========
Hyperion
========

Installing (develop version)
----------------------------

TODO: how to install for user, not developer

It's easiest, safest and cleanest to install these in their own environment. 
We use conda_. Make sure you have an up-to-date
version  of ``conda`` installed – either from Anaconda_ or miniconda_.

To make sure ``conda`` is up-to-date, run::

    conda update -n base -c default conda

Depending on how old your (ana)conda install is, you might have to specify ``root``
instead of ``base``. You *might* have to run this multiple times. It's prudent
(and possibly necessary) to update all other packages in your base environment
as well. Then, in this directory (where ``environment.yml`` lives), run::

    conda env create

to install all the dependencies in a new environment called ``hyperion``. If
you already have a ``hyperion`` environment, make sure it's up-to-date with::

    conda env update
    
Before working you need to **Enter the environment**::
    
    conda activate hyperion

Then you need to install the hyperion package, you should do

    pip install -e .

Check that the installation is correct by doing

    conda list

You should see a list of all the packages installed in the environment, including hyperion.

To keep a close track of the version off **all** the packages that were installed, you
should run

    conda env export > environment_output/pc-YOURPCNAME.yml

replacing YOURPCNAME for the name of your PC.

Finally, in order to have the documentation, you need to create a folder called ``doc/build`` and run

	sphinx-build -b html docs/source/ docs/build/

This will create a series of html files with the documentation for the project
in the folder doc/build, you should start at index.html
