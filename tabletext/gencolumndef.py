#!/usr/bin/env python3
# Copy a column definition, replacing blanks by defaults.

# Defaults to CSV format, can be used for other delinited text formats.

"""
Copy a column definition, replacing blanks by defaults.

Can be used to create an initializer for table.Column().

Requires an object that reads lists of strings and an object that
writes lists of objects that can be written as strings.

Script version defaults to CSV format, but can be used for other
delimited text formats.
"""

# python3
import sys
import collections
import csv
import getopt

# application
from tabletext import table

class GenColumnDef(object):

    def __init__(self):
        super().__init__()

    def setdefaults(self, rowreader, rowwriter):
        """
        Copy a column definition, replacing blanks by defaults.

        Can be used to produce a draft column definition from a list
        of column headings.  The draft can be manually updated and
        used as an initializer for table.Column().

        An incoming table definition produced by rowreader is modified
        by increasing the number of columns if necessary, and placing
        default data in columns 1, 2, 3 (counting from zero) when the
        incoming data is blank or was missing.  Incoming nonblank data
        is not changed.  First column (0) must be nonblank, and values
        must be unique.

        rowreader is an object with an iterator that generates lists of
            strings (str).
        rowwriter is an object that accepts a list of items that have
            type 'str'.
        
        Raises TypeError if rowreader produces an object that is not a
            list.
        Raises ValueError if the list has no items or the first item is
            blank
        
        Defaults:
            Blank or    New Value               purpose
            missing
            row[0]      Raises ValueError       unique headings
                                                    required as ID
            row[1]      "lambda x: x"           convert input to
                                                    internal type
            row[2]      "lambda x: str(x)"      convert internal type
                                                    to str

        The default functions can be manually replaced by other
        functions. For exampple, to input and output lists:
            row[1]      "lambda x: eval(x)"     convert incoming text
                                                    to an internal list
            row[2]      "lambda x: repr(x)"     output text to recreate
                                                    an internal list
        
        Note that multi-line values are only supported when rowreader
        is a csv.reader and rowwriter is a csv.writer, and only for
        headings (first column).
        """
        names = dict()
        for row in reader:
            try:
                if not isinstance(row, list):
                    raise ValueError("rowreader must produce list")
                for i in range(len(row), 4):  # Convert missing values to empty
                    row.append('')
                heading = row[0]        # no check
                if row[1] == '':
                    infunc = "lambda x: None if x == '' else x"
                else:
                    infunc = row[1]
                # check will evaluate to Python lambda function
                Throw_away_func = table.Column.eval_lambda_function(infunc)
                if row[2] == '':
                    outfunc = "lambda x: '' if x is None else str(x)"
                else:
                    outfunc = row[2]
                # check will evaluate to Python lambda function
                Throw_away_func = table.Column.eval_lambda_function(outfunc)
                # generate column name if blank, check for duplicates
                name = row[3]
                if name == '':
                    try:
                        # create name from heading
                        name = table.Column.createcolumnname(heading)
                    except ValueError as e:
                        # failed to create name --> default name
                        name = "column_" + str(len(names))
                    if name in names:
                        # duplicate name --> default name
                        name = "column_" + str(len(names))
                else:
                    if not table.Column.isvalidcolumnname(name):
                        raise ValueError("Invalid column name: " + repr(name))
                if name in names:
                    # duplicate name --> abort
                    raise ValueError(''.join(["Duplicate column name: ",
                                            repr(name)]))
                names.setdefault(name, None)
                rowwriter.writerow([heading, infunc, outfunc, name])
            except Exception as e:
                raise e.__class__("At input: " + repr(row)) from e

if __name__ == "__main__":
    """
    Run as a script if invoked from shell command line.
    
    Input from stdin a single file, output to stdout as an enumerated,
    replacing blank or missing values by default values.

    Note that multi-line values are only supported for CSV input and
    CSV output.
    """

    # Get the processing options and the optional file name.
    optarg = getopt.getopt(sys.argv[1:],
                            "h",
                            ["help", "indelim=", "outdelim="])
    opt = collections.OrderedDict(optarg[0])
    arg = optarg[1]
    if "-h" in opt or "--help" in opt or len(arg) > 1:
        print(" ".join(["Usage: ", sys.argv[0],
                        "[-h|--help]",
                        "[--indelim='x']",
                        "[--outdelim='y']",
                        "[filename]"]),
                file=sys.stderr)
        print("       Extract first line as headings",
                file=sys.stderr)
        print("       -h|--help     print this message",
                file=sys.stderr)
        print("       --indelim=    input field delimiter (CSV if omitted)",
                file=sys.stderr)
        print("       --outdelim=   output field delimiter (CSV if omitted)",
                file=sys.stderr)
        print("       --skip=       "
                    + "mumber of leading columns to skip (default 0)",
                file=sys.stderr)
        print("       omitted delimiters specify CSV formatted text",
                file=sys.stderr)
        print("       See script for details",
                file=sys.stderr)
        exit(code=2)

    # Create a row reader factory for input.
    if "--indelim" in opt:
        indelim = opt["--indelim"]
        if len(indelim) == 0:
            indelim = None      # Delimiter is any string of consecutive spaces
        rowreader = table.Delim(indelim).reader
    else:
        rowreader = csv.reader

    # Create a row writer factory for output.
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

    # No column heads in the output, output is only data

    # Extract and enumerate headings, one heading per output row.
    try:
        writer = rowwriter(sys.stdout)
        reader = rowreader(textsource)
        GenColumnDef().setdefaults(reader, writer)
    finally:
        if not textsource is sys.stdin:
            textsource.close()
