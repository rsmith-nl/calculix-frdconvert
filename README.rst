Converter for CalculiX FRD files
################################

:date: 2022-10-01
:tags: CalculiX, Python
:author: Roland Smith

.. Last modified: 2022-10-01T20:02:47+0200
.. vim:spelllang=en

On several occasions, the author has written small scripts to extract data
from CalculiX's FRD files and manipulate them in some way.

Having done that quick and dirty several times, the author decided to do this
properly and write software that could read all the node-related data from an
FRD file and save it in formats that are easy for programming languages to
read.

The ``frdconvert`` software is written in Python, so it supports converting to
Python's native ``pickle`` format. But ``json`` and ``sqlite3`` output are
also supported. The latter two should be readable by many programming
languages.

``frdconvert`` has been written so that it can be used as a Python module
*and* as a standalone program.
It uses only modules from the Python standard library.


Usage as a module
-----------------

.. code-block:: python

    import frdconvert as frd

    data = frdconvert.read_frd("test/job.frd")
    frdconvert.write_sqlite(data, "test/job.db")

The ``data`` is a dictionary with the keys being the names of the sections
present in the FRD-file.
The possible names of the sections are listed in ``NODE_RELATED`` near the top
of ``frdconvert.py``.
Each of the values in ``data`` is again a dictionary.
The values in these underlying dictionaries are tuples of ``float``.
The keys are the number of the node that the tuple belong to.
Note that node numbers do not have to start at 1!


Usage as a standalone program
-----------------------------

This program is meant to be used from a terminal (``POSIX`` operating system)
or ``cmd``-window (ms-windows).
In the examples below ``>`` represents the command-prompt.

Converting an frd file to json::

    > frdconvert.py -j --log=info test/job.frd
    INFO: file “test/job.frd” contains 365432 lines.
    INFO: extracting NODES
    INFO: extracting DISP
    INFO: extracting MESTRAIN
    INFO: extracting FORC
    INFO: extracting ZZSTR
    INFO: writing JSON file “test/job.json”

Showing the online help::

    > frdconvert.py -h
    usage: frdconvert.py [-h] (-j | -p | -s) [-l] [-v] [--log {debug,info,warning,error}] [file ...]

    Extract the node-related data from a CalculiX FRD file and save it in formats suitable for use with
    programming languages. Currently supports JSON, sqlite3 and pickle (for Python) output formats.

    positional arguments:
    file                  one or more files to process

    optional arguments:
    -h, --help            show this help message and exit
    -j, --json            save FRD file contents in JSON format
    -p, --pickle          save FRD file contents in pickle format
    -s, --sqlite          save FRD file contents in sqlite3 database format
    -l, --license         print the license
    -v, --version         show program's version number and exit
    --log {debug,info,warning,error}
                            logging level (defaults to 'warning')

