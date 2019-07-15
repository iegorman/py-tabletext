#!/usr/bin/env python3
# Demo reading good and bad data, writing data

'''
Examples of how to read good and bad data, write good data.

Files "demo_01.input.txt" and "demo_01.input.ok.empty.txt" can be used
as good input to illustrate how to read and write good data.  Input is
read as one list per line of input, as one dictionary per line of input
or as one named tuple per line of input.  In each case, the internal
form of data storage is shown, and the data is sent back out again as
text.

Files "demo_01.input.bad.*.txt" can be used as input to illustrate how
the program reacts to input data errors.

File "demo_01.columndef.csv" was used as input to program
"tabletext.table.codegen.py" to produce the table initializer for this
file.
'''

# Python 3
import sys
import collections
import csv
import getopt

# Application
from tabletext import table

class Demo_01(object):

    def __init__(self):
        self.column = table.Column(
            [
                # Column descriptions, four items per column:
                #   Column heading
                #   Data input function, text to internal type
                #   Data output function, internal type to text
                #   Column name
                #
                [   # Column 0
                    'String',
                    'lambda x: x',
                    "lambda x: '' if x is None else x",
                    'string_v'],
                [   # Column 1
                    'Nullable String',
                    "lambda x: None if x == '' else x",
                    "lambda x: '' if x is None else x",
                    'nullable_string'],
                [   # Column 2
                    'Integer',
                    "lambda x: None if x == '' else int(x)",
                    "lambda x: '' if x is None else str(x)",
                    'integer_v'],
                [   # Column 3
                    'Float',
                    "lambda x: None if x == '' else float(x)",
                    "lambda x: '' if x is None else str(x)",
                    'float_v'],
                [   # Column 4
                    'Boolean',
                    "lambda x: None if x == '' else eval(x)",
                    "lambda x: '' if x is None else str(x)",
                    'logical'],
                [   # Column 5
                    'List',
                    "lambda x: None if x == '' else eval(x)",
                    "lambda x: '' if x is None else repr(x)",
                    'list_v']
                ])

    def getinput(self, rowreader):
        inputdata = list()
        for row in rowreader:
            inputdata.append(row)
        return inputdata

    def putoutput(self, rowlist, rowwriter):
        for row in rowlist:
            rowwriter.writerow(row)

if __name__ == "__main__":
    """
    Run as a script if invoked from shell command line.
    
    Input from stdin or a single file, output to stdout.
    """

    # Get the processing options and the optional file name.
    optarg = getopt.getopt(sys.argv[1:],
                            "h",
                            ["help"])
    opt = collections.OrderedDict(optarg[0])
    arg = optarg[1]
    if "-h" in opt or "--help" in opt or len(arg) > 1:
        print(" ".join(["Usage: ", sys.argv[0],
                        "[-h|--help]",
                        "filename"]),
                file=sys.stderr)
        print("       Demonstrate input, output, and error reporting",
                file=sys.stderr)
        print("       -h|--help     print this message",
                file=sys.stderr)
        print("       if input file not given, will read standard input",
                file=sys.stderr)
        print("       See script for details",
                file=sys.stderr)
        exit(code=2)

    # Input data source
    if len(arg) > 0:
        textsource = open(arg[0], newline='')   # no line-end translation
    else:
        textsource = sys.stdin
    inputtext = list()
    for line in textsource:
        inputtext.append(line)
    
    divider = "-" * 79

    print("\nInput text:")
    print(divider)
    for line in inputtext:
        sys.stdout.write(line)
    print(divider)

    demo_01 = Demo_01()

    print("\nRepresentation of internal data after reading lines as lists:")
    inputdata = demo_01.getinput(demo_01.column.ListInput(
                                                        csv.reader(inputtext)))
    print(divider)
    for row in inputdata:
        print(repr(row))
    print(divider)

    print("\nOutput of data stored internally as lists:")
    print(divider)
    demo_01.putoutput(inputdata, demo_01.column.ListOutput(
                                                    csv.writer(sys.stdout)))
    print(divider)

    print("\nRepresentation of internal data after reading lines as"
            + " dictionaries:")
    inputdata = demo_01.getinput(demo_01.column.DictInput(
                                                        csv.reader(inputtext)))
    print(divider)
    for row in inputdata:
        print(repr(row))
    print(divider)

    print("\nOutput of data stored internally as dictionaries:")
    print(divider)
    demo_01.putoutput(inputdata, demo_01.column.DictOutput(
                                                    csv.writer(sys.stdout)))
    print(divider)

    print("\nRepresentation of internal data after reading lines as"
            + " named tuples:")
    inputdata = demo_01.getinput(demo_01.column.NamedInput(
                                                        csv.reader(inputtext)))
    print(divider)
    for row in inputdata:
        print(repr(row))
    print(divider)

    print("\nOutput of data stored internally as named tuples:")
    print(divider)
    demo_01.putoutput(inputdata, demo_01.column.NamedOutput(
                                                    csv.writer(sys.stdout)))
    print(divider)
