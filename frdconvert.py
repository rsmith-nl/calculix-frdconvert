#!/usr/bin/env python
# file: frdconvert.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2022 R.F. Smith <rsmith@xs4all.nl>
# SPDX-License-Identifier: MIT
# Created: 2022-10-01T10:01:55+0200
# Last modified: 2023-12-23T00:13:43+0100
"""
Extract the node-related data from a CalculiX FRD file and save it in formats
suitable for use with programming languages.

Currently supports JSON, sqlite3 and pickle (for Python) output formats.
"""

import argparse
import itertools as itt
import logging
import os
import pickle
import sys
import sqlite3

__version__ = "2023.12.23"
__license__ = f"""{os.path.basename(__file__)} {__version__}
Copyright © 2022 R.F. Smith

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice (including the next
paragraph) shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# These data are node-related.
# The first item, NODES is special. It contains the original positions of the
# nodes.
NODE_RELATED = (
    "NODES",
    "CP3DF",
    "CT3D-MIS",
    "CURR",
    "DEPTH",
    "DISP",
    "DTIMF",
    "ELPOT",
    "EMFB",
    "EMFE",
    "ENER",
    "ERROR",
    "FLUX",
    "FORC",
    "HCRIT",
    "M3DF",
    "MAFLOW",
    "MDISP",
    "MESTRAIN",
    "MSTRAIN",
    "MSTRESS",
    "NDTEMP",
    "PDISP",
    "PE",
    "PFORC",
    "PNDTEMP",
    "PS3DF",
    "PSTRESS",
    "PT3DF",
    "RFL",
    "SDV",
    "SEN",
    "STPRES",
    "STRESS",
    "STRMID",
    "STRNEG",
    "STRPOS",
    "STTEMP",
    "THSTRAIN",
    "TOPRES",
    "TOSTRAIN",
    "TOTEMP",
    "TS3DF",
    "TT3DF",
    "TURB3DF",
    "V3DF",
    "VELO",
    "VSTRES",
    "ZZSTR",
)


class _LicenseAction(argparse.Action):
    """Action class to print the license."""

    def __call__(self, parser, namespace, values, option_string=None):
        print(__license__)
        sys.exit()


def _main():
    """Entry point when frdconvert.py is called as a program."""
    args = _setup()
    for infn in args.files:
        contents = read_frd(infn)
        if args.json:
            write_json(contents, infn[:-4] + ".json")
        elif args.pickle:
            write_pickle(contents, infn[:-4] + ".pickle")
        elif args.sqlite:
            write_sqlite(contents, infn[:-4] + ".db")


def _setup():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="save FRD file contents in JSON format",
    )
    group.add_argument(
        "-p",
        "--pickle",
        action="store_true",
        help="save FRD file contents in pickle format",
    )
    group.add_argument(
        "-s",
        "--sqlite",
        action="store_true",
        help="save FRD file contents in sqlite3 database format",
    )
    parser.add_argument(
        "-l", "--license", action=_LicenseAction, nargs=0, help="print the license"
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "--log",
        default="warning",
        choices=["debug", "info", "warning", "error"],
        help="logging level (defaults to 'warning')",
    )
    parser.add_argument(
        "files", metavar="file", nargs="*", help="one or more files to process"
    )
    args = parser.parse_args(sys.argv[1:])
    logging.basicConfig(
        level=getattr(logging, args.log.upper(), None),
        format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    return args


def read_frd(path):
    """
    Read and return the data in an frd file as a dictionary of dictionaries.

    The return value is a dictionary with the keys being the names of the
    data sets present in the FRD-file.
    The values in the underlying dictionaries are tuples of ``float``.
    The keys are the number of the node that the tuple belong to.
    Note that node numbers do not have to start at 1!
    """
    with open(path) as file:
        lines = [ln.strip() for ln in file]
    logging.info(f"file “{path}” contains {len(lines)} lines.")
    ranges = _find_ranges(lines)
    contents = {}
    for name in ranges.keys():
        if name not in NODE_RELATED:
            continue  # skip
        first, last = ranges[name]
        contents[name] = _process_float_data(lines, first, last)
        logging.info(f"extracted {len(contents[name])} “{name}”")
    return contents


def _find_ranges(lines):
    """Find the start and end lines of the different data sets."""
    starts, ends = {}, {}
    for num, ln in enumerate(lines):
        # Node data is preceded by a “2C”-line.
        if ln.startswith("2C"):
            starts["NODES"] = num + 1
        # Element data is preceded by a “3C”-line
        if ln.startswith("3C"):
            starts["ELEMENTS"] = num + 1
        # All other data is preceded by a “-4” line.
        elif ln.startswith("-4"):
            items = ln.split()
            starts[items[1]] = num + 1
        # Data ends with a “-3”-line.
        elif ln.startswith("-3"):
            ends[next(reversed(starts.keys()))] = num 
    ranges = {name: (starts[name], ends[name]) for name in starts.keys()}
    del starts, ends
    return ranges


def _process_float_data(lines, first, last):
    """Convert node-related float data to a dictionary indexed by the node number."""
    data = {}
    while not lines[first].startswith("-1"):
        first += 1
    count = int(len(lines[first]) / 12)
    indices = [(c * 12, (c + 1) * 12) for c in range(1, count)]
    for ln in itt.islice(lines, first, last):
        num = int(ln[2:12])
        numbers = [float(ln[a:b]) for a, b in indices]
        data[num] = tuple(numbers)
    return data


def write_json(contents, name):
    """Write the contents dictionary to a JSON file."""
    logging.info(f"writing JSON file “{name}”")
    with open(name, "w") as outfile:
        outfile.write("{\n")
        items = [[name, data, "  },\n"] for name, data in contents.items()]
        items[-1][2] = "  }\n"
        for name, data, sep in items:
            outfile.write(f'  "{name}": ' + "{\n")
            buffer = ",\n".join(
                f'    "{node}": [{", ".join(str(f) for f in values)}]'
                for node, values in data.items()
            )
            outfile.write(buffer + "\n")
            outfile.write(sep)
        outfile.write("}\n")


def write_pickle(contents, name):
    """Write the contents dictionary to a pickle file."""
    logging.info(f"writing pickle file “{name}”")
    with open(name, "wb") as outfile:
        pickle.dump(contents, outfile)


def write_sqlite(contents, name):
    """Write the contents dictionary to a sqlite3 database."""
    # Remove existing database.
    if os.path.isfile(name):
        logging.info(f"removing existing database “{name}”")
        os.remove(name)
    # Write new database.
    logging.info(f"writing sqlite database “{name}”")
    with sqlite3.connect(name) as con:
        for name, data in contents.items():
            firstkey = next(iter(data.keys()))
            length = len(data[firstkey]) + 1
            tableq = f"CREATE TABLE {name}(node INTEGER PRIMARY KEY, "
            tableq += ", ".join(f"r{idx} REAL" for idx in range(1, length))
            tableq += ");"
            logging.debug(tableq)
            con.execute(tableq)
            con.commit()
            insq = f"INSERT INTO {name} VALUES (?, "
            insq += ", ".join("?" for idx in range(1, length))
            insq += ");"
            logging.debug(insq)
            con.executemany(insq, ((k, *v) for k, v in data.items()))
            con.commit()


if __name__ == "__main__":
    _main()
