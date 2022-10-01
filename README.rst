Converter for CalculiX FRD files
################################

:date: 2022-10-01
:tags: CalculiX, Python
:author: Roland Smith

.. Last modified: 2022-10-01T18:38:07+0200
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



