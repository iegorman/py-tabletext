#!/usr/bin/env python3
# Demo modifying CSV table definitions and data.

'''
Examples of how to modify CSV table definitions and data.

File "demo_01.input.txt" can be used as good input to illustrate how to
read and write good data.  Input is read as one list per line of input,
and as one dictionary per line of input.  In each case, the internal
form of data storage is shown, and the data is sent back out again as
text.

Files "demo_01.input.*.txt" can be used as input to illustrate how the
program reacts to input data errors.

File "demo_02.columndef.csv" was used as input to program
"tabletext.table.codegen.py" to produce code for this file.

LibreOffice is a convenient editor for short CSV files.  CSV files
can be read into a LibreOffice spreadsheet (use the 'text' option on all
columns), edited, and written back to the same of a new CSV file.
'''

# Python 3
import sys
import collections
import csv
import getopt
import traceback

# Application
from tabletext import table

class Demo_02(object):

    def __init__(self):
        self.column = table.Column(
            [
                #   Column descriptions, four items per column:
                #   Column heading
                #   Data input function, text to internal type
                #   Data output function, internal type to text
                #   Column name
                #
                [   # Column 0
                    'Column 0',
                    'lambda x: x',
                    "lambda x: '' if x is None else str(x)",
                    'column_0'],
                [   # Column 1
                    'Column 1',
                    'lambda x: x',
                    "lambda x: '' if x is None else str(x)",
                    'column_1'],
                [   # Column 2
                    'Column 2',
                    'lambda x: x',
                    "lambda x: '' if x is None else str(x)",
                    'column_2'],
                [   # Column 3
                    'Column 3',
                    'lambda x: x',
                    "lambda x: '' if x is None else str(x)",
                    'column_3'],
                [   # Column 4
                    'Column 4',
                    'lambda x: x',
                    "lambda x: '' if x is None else str(x)",
                    'column_4']
                ])

if __name__ == "__main__":
    """
    Run as a script if invoked from shell command line.
    
    Input from stdin or a single file, output to stdout.
    """

    def succeeded():
        print("\nSucceeded\n")

    def failed():
        print("Failed, but should have succeeded\n")

    def failedAsExpected():
        print("Failed as expected\n")

    def shouldHaveFailed():
        print("\nSucceeded, but should have failed\n")

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

    divider = "-" * 79

    print("\nReading input text ...")
    print(divider)
    # Input data source
    if len(arg) > 0:
        textsource = open(arg[0], newline='')   # no line-end translation
    else:
        textsource = sys.stdin
    inputtext = list()
    for line in textsource:
        inputtext.append(line)
    
    print("\nInput text:")
    print(divider)
    for line in inputtext:
        sys.stdout.write(line)
    print(divider)

    demo_02 = Demo_02()

    # New reference to make code more readable; we will be using original and
    # revised column definitions.
    original_column = demo_02.column
    
    print("\nRepresentation of internal data after reading lines as"
            + " dictionaries:")
    rowreader = original_column.DictInput(csv.reader(inputtext))
    inputdata = [row for row in rowreader]
    print(divider)
    for row in inputdata:
        print(repr(row))
    print(divider)

    print("\nOutput of data stored internally as dictionaries:")
    print(divider)
    rowwriter = original_column.DictOutput(csv.writer(sys.stdout))
    rowwriter.writerows(inputdata)
    print(divider)

    print("\nOutput of data with Column 2 removed:")
    print(divider)
    revised_column = original_column.remove(["column_2"])
    rowwriter = revised_column.DictOutput(csv.writer(sys.stdout))
    rowwriter.writerows(inputdata)
    print(divider)

    print("\nOutput of data with Columns 0, 3, 4 selected:")
    print(divider)
    revised_column = original_column.select(
                            ["column_0", "column_3", "column_4"])
    rowwriter = revised_column.DictOutput(csv.writer(sys.stdout))
    rowwriter.writerows(inputdata)
    print(divider)

    print("\nOutput of data with Columns 0, 3, 4 selected in different order:")
    print(divider)
    revised_column = original_column.select(
                            ["column_0", "column_4", "column_3"])
    rowwriter = revised_column.DictOutput(csv.writer(sys.stdout))
    rowwriter.writerows(inputdata)
    print(divider)

    print("\nOutput of data with Columns 3 and 4 headings changed:")
    print(divider)
    heading_change = [["column_3", "Column III"], ["column_4", "Column IV"]]
    revised_column = original_column.changeheadings(heading_change)
    rowwriter = revised_column.DictOutput(csv.writer(sys.stdout))
    rowwriter.writerows(inputdata)
    print(divider)

    print("\nOutput of data with Columns 2 and 4 renamed, headings unchanged:")
    print(divider)
    heading_change = [["column_4", "column_E"], ["column_2", "column_C"]]
    revised_column = original_column.rename(heading_change)
    rowwriter = revised_column.DictOutput(csv.writer(sys.stdout))
    # New output data required when input data stored as dict or named tuple
    # because writing with different headings (dict) or names (tuple)
    # Could use original data when stored as list (no column headings or names)
    outputdata = list()
    for row in inputdata:
        newrow = dict()
        for (oldname, newname) in zip(original_column.names,
                                        revised_column.names):
            newrow.setdefault(newname, row[oldname])
        outputdata.append(newrow)
    rowwriter.writerows(outputdata)
    print("Column names before: " + repr(original_column.names))
    print("Column names after:  " + repr(revised_column.names))
    print(divider)

    print("\nOutput of data with Columns F and G appended:")
    print(divider)
    extra_column = table.Column([   [ "Column F",
                                      "lambda x: x",
                                      "lambda x: '' if x is None else str(x)",
                                      "column_f"],
                                    [ "Column G",
                                      "lambda x: x",
                                      "lambda x: '' if x is None else str(x)",
                                      "column_g"]
                               ])
    revised_column = original_column.append(extra_column)
    count = 0
    newdata = list()
    for row in inputdata:
        # deep copy old dictionary because new dictionary will be modified
        # we could modify and output the old dictionary if we wanted to
        new_dict = collections.OrderedDict(item for item in row.items())
        count += 1
        for col in ["f", "g"]:
            # add data for new columns to the new dictionary
            new_dict.setdefault("column_" + col, col + "-" + str(count))
        newdata.append(new_dict)
    rowwriter = revised_column.DictOutput(csv.writer(sys.stdout))
    rowwriter.writerows(newdata)
    print(divider)
