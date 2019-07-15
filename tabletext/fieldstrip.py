#!/usr/bin/env python3
# Strip leading and trailing space from each field of delimited text
# The delimiter is either a single character, like a comma or a tab, or "csv"
# "csv" indicates a "comma separated value" file of the kind accepted as input
# by Microsoft Excel or LibreOffice Calc

# Input: a single file or standard input
# Output: standard output 

# Python3
import sys
import collections
import csv
import getopt
import traceback

# application
from tabletext import table

class FieldStrip():
    """
    Trim leading and trailing spaces from every field of delimited text.
    """
    def __init__(self):
        pass

    @classmethod
    def strip(cls, rowreader, rowwriter):
        """
        Trim leading and trailing spaces from every field of delimited
        text.

        rowreader is an interator that provides a list or other
        interable of strings from each iteration (like
        csv.reader).

        rowwriter is an object with a write() method that accepts a
        single string.
        """
        for row in rowreader:
            rowwriter.writerow(r.strip() for r in row)

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
                            '-h',
                            ["help", "delim="])
    opt = collections.OrderedDict(optarg[0])
    arg = optarg[1]
    if "-h" in opt or "--help" in opt or len(arg) > 1:
        printlog(" ".join(["Usage: ", sys.argv[0],
                        "[-h|--help]",
                        "[--delim='x']",
                        "[filename]"]))
        printlog("       Strip leading and trailing spaces from each field of"
                + " delimited text")
        printlog("       -h|--help     print this message")
        printlog("       --delim=      field delimiter")
        printlog("       zero-length delimiter causes special handling")
        printlog("       omit delimiter to specify CSV formatted text")
        printlog("       See script for details")
        exit(code=2)

    # row reader factory for input, rowwriter factory for output
    if "--delim" in opt:
        delim = opt["--delim"]
        if len(delim) == 0:
            # input delimiter is any string of consecutive spaces
            # output delimiter is a single space
            delim = None      # Delimiter is any string of consecutive spaces
        rowreader = table.Delim(delim).reader
        rowwriter = table.Delim(delim).writer
    else:
        rowreader = csv.reader
        rowwriter = csv.writer

    # Input data source
    if len(arg) > 0:
        textsource = open(arg[0], newline='')   # no line-end translation
    else:
        textsource = sys.stdin

    try:
        writer = rowwriter(sys.stdout)
        reader = rowreader(textsource)
        FieldStrip().strip(reader, writer)
    finally:
        if not textsource is sys.stdin:
            textsource.close()
