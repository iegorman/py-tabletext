#!/usr/bin/env python3
# Extract column heads from CSV or other delimited line data.

"""
Extract column heads from CSV or other delimited line data.

Can be used with 'columndef.py' and 'codegen.py' to produce an initial
draft of column definitions for 'table.Column'.

Class 'Headings' extracts heads as a list of strings.
Script outputs heads as an enumerated list of strings.

Input and Output can be in CSV format or other column- or field-
oriented delimited text data.  Multiline values are only supported
when reading CSV and outputting CSV.
"""

import sys
import csv
import collections
import getopt

from tabletext import table

class Headings(object):
    """
    Extract column heads from CSV or other delimited line data.

    Class extracts heads as a list of strings.

    Input and Output can be in CSV format or other column- or field-
    oriented delimited text data.  Multiline values are only supported
    when reading CSV and outputting CSV.
    """

    def __init__(self):
        pass

    def read(self, rowreader):
        """
        Return a list of headings from CSV or delimited text data.

        Returns a list of string values from the first row of CSV data
        or delimited data.  The list will be empty if there is no first
        row.  Any heading string may have length zero.

        rowreader is a csv.reader or any object with an iterator that
        produces a list of strings or a tuple of strings from each
        iteration.
        """
        heads = []      # if no first row, return empty list
        for heads in rowreader:
            break
        return heads


if __name__ == "__main__":
    """
    Run as a script if invoked from shell command line.
    
    Input from stdin or a single file, output to stdout as an
    enumerated list of heads, one head per line.

    Note that multi-line values are only supported for CSV input and
    CSV output.
    """

    def printlog(text):
        print(text, file=sys.stderr)

    # Get the processing options and the optional file name.
    optarg = getopt.getopt(sys.argv[1:],
                            "h",
                            ["help", "noenum", "indelim=", "outdelim="])
    opt = collections.OrderedDict(optarg[0])
    arg = optarg[1]
    if "-h" in opt or "--help" in opt or len(arg) > 1:
        printlog(" ".join(["Usage: ", sys.argv[0],
                        "[-h|--help]",
                        "[--noenum]",
                        "[--indelim='x']",
                        "[--outdelim='y']",
                        "[filename]"]))
        printlog("       Extract first line as headings")
        printlog("       -h|--help     print this message")
        printlog("       --noenum      do not enumerate the headings")
        printlog("       --indelim=    input field delimiter")
        printlog("       --outdelim=   output field delimiter")
        printlog("       zero-length delimiters cause special handling")
        printlog("       omit delimiters to specify CSV formatted text")
        printlog("       See script for details")
        exit(code=2)

    # row reader factory for input
    if "--indelim" in opt:
        indelim = opt["--indelim"]
        if len(indelim) == 0:
            indelim = None      # Delimiter is any string of consecutive spaces
        rowreader = table.Delim(indelim).reader
    else:
        rowreader = csv.reader

    # row writer factory for output
    if "--outdelim" in opt:
        outdelim = opt["--outdelim"]
        if len(outdelim) == 0:
            outdelim = None     # Delimiter is a single space
        rowwriter = table.Delim(outdelim).writer
    else:
        rowwriter = csv.writer

    # Input data source
    if len(arg) > 0:
        textsource = open(arg[0], newline='')   # no line-end translation
    else:
        textsource = sys.stdin

    # Extract and optionally enumerate headings, one heading per output row
    try:
        writer = rowwriter(sys.stdout)
        reader = rowreader(textsource)
        heads = Headings().read(rowreader(textsource))
        if "--noenum" in opt:
            # bare text headings, single column, no column heads in output
            for head in heads:
                writer.writerow([head])
        else:
            # enumerated heads, first output line identifies columns
            writer.writerow(["Column", "Heading"])
            for (n, head) in enumerate(heads):
                writer.writerow([n, head])
    finally:
        if not textsource is sys.stdin:
            textsource.close()
