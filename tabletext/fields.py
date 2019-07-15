#!/usr/bin/env python3
#  Build a summary of data in line- and column-oriented text data.
#
# The default input format is CSV, both other formats can be chosen.
#
# Produces a file for each column of the table, listing all cell values and
# Their frequency of occrrence,
#
# Also outputs a file lisitnf all line lengths (number of fields or columns)
# and their frequency of occurrence. 

# Python 3
import sys
import collections
import getopt
import csv

# Application
from tabletext import table


class Fields(object):
    """
    Build a summary of data in line- and column-oriented text data.

    Each line comes in as a delimited list, each delimited item
    the value of one cell in a table of rows and columns.

    A summary os produced for the entire text (which may be the contents
    of a file, and for each column of the table represented by the text.

    The text summary is a dictionary of field counts (as key), and the
    number of lines (as value) having each field count. The dictionary
    is in order by the first occurrence of each field count.

    Each column summary is a dictionary of field values (as key), and
    the number of lines containing that field value.  Each dictionary is
    in order by the first occurrence of each field value.
    """
    def __init__(self, maxcolumns=None):
        # dictionary keyed by column count, value=number of occurrences,
        # one entry for each different line length as measured in columns
        self._columns = collections.OrderedDict()
        # dictionaries keyed by field value, value=number of occurrences,
        # one dictionary for each column
        self._fieldvalues = list()
        self._maxcolumns = maxcolumns
        # for exception reporting
        self.rowcount = int(0)

    def addrow(self, row):
        """
        Include another data row in the summary.

        Row is a list or tuble of strings.
        """
        data = [r for r in row]     # convert iterator or generator to list
        # add an entry for the row length if necessary
        if not len(data) in self._columns:
            self._columns.setdefault(len(data), int(0))
        # add this row to the count for rows of the same length
        self._columns[len(data)] += 1
        if self._maxcolumns and self._maxcolumns < len(data):
            raise ValueError("Row " + str(rowcount) + ": row length="
                            + len(data) + " exceeds maximum length="
                            + str(self._maxcolumns))
        # add more columns if necessary
        for i in range(len(self._fieldvalues), len(data)):
            self._fieldvalues.append(collections.OrderedDict())
        # add each column value to the count for the same value in that column
        for (val, column) in zip(data, self._fieldvalues):
            if not val in column:
                column.setdefault(val, int(0))
            column[val] += 1

    def addrows(self, rowreader):
        for row in rowreader:
            self.addrow(row)

    @property
    def columns(self):
        """
        Return dictionary showing distribution of line lengths.

        The dictionary is in order by first occurrence of eadh line
        length.
        """
        return self._columns

    @property
    def fieldvalues(self):
        """
        Return list of dictionaries: distributions of column values.

        The list is in order by the left-to-right position of the
        columns.

        Each dictionary is in order by first occurrence of eadh field
        value.
        """
        return self._fieldvalues


if __name__ == "__main__":
    """Run as a script if invoked from shell command line."""

    def printlog(text):
        print(text, file=sys.stderr)

    # Get the processing options and the optional file name.
    optarg = getopt.getopt(sys.argv[1:],
                            "h",
                            ["help", "outdir=", "indelim=", "outdelim="])
    opt = collections.OrderedDict(optarg[0])
    arg = optarg[1]
    if "-h" in opt or "--help" in opt or len(arg) > 1:
        printlog(" ".join(["Usage: ", sys.argv[0],
                        "[-h|--help]",
                        "[--outdir=directory]",
                        "[--indelim='x']",
                        "[--outdelim='y']",
                        "[filename]"]))
        printlog("       Extract first line as headings")
        printlog("       -h|--help     print this message")
        printlog("       --outdir=     output directory (instead of current)")
        printlog("       --indelim=    input field delimiter")
        printlog("       --outdelim=   output field delimiter")
        printlog("       zero-length delimiters cause special handling")
        printlog("       omit delimiters to specify CSV formatted text")
        printlog("       See script for details")
        exit(code=2)


    # create a row reader factory for input
    if "--indelim" in opt:
        indelim = opt["--indelim"]
        if len(indelim) == 0:
            indelim = None      # Delimiter is any string of consecutive spaces
        rowreader = table.Delim(indelim).reader
    else:
        rowreader = csv.reader

    # create a row writer factory for output
    if "--outdelim" in opt:
        outdelim = opt["--outdelim"]
        if len(outdelim) == 0:
            outdelim = None     # Delimiter is a single space
        rowwriter = table.Delim(outdelim).writer
        suffix = '.txt'
    else:
        rowwriter = csv.writer
        suffix = '.csv'

    if "--outdir" in opt:
        dir = opt["--outdir"].lstrip(r'\/') + '/'
    else:
        dir = ""

    # Define an input data source
    if len(arg) > 0:
        textsource = open(arg[0], newline='')   # no line-end translation
    else:
        textsource = sys.stdin

    columndist = "columns.txt"
    prefix = "column_"
    numformat = lambda x: '{0:03d}'.format(x)

    summary = Fields(maxcolumns=100)
    summary.addrows(rowreader(textsource))

    # Write text summary to a file
    # list field counts and number of lines for each count
    with open(dir + prefix + "columncounts" + suffix, 'w') as f:
        writer = rowwriter(f)
        writer.writerow(["Number of columns", "Number of Rows"])
        for (count, freq) in summary.columns.items():
            writer.writerow([str(count), str(freq)])

    # Write each column summary to its own file
    # list the dictionary of field values and counts
    for (n, d) in enumerate(summary.fieldvalues):
        filepath = ''.join([dir, prefix, numformat(n), suffix])
        with open(filepath, 'w') as f:
            writer = rowwriter(f)
            writer.writerow(["Count", "Column Value"])
            for (v, c) in d.items():
                writer.writerow([str(c), str(v)])
