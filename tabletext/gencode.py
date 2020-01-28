#!/usr/bin/env python3
# Create code template for application that uses table.Column.

"""
Create code template for application that uses table.Column.

Input comes from an object with an iterator that provides a string
upon each call to __next__.

Output goes to an object with a writerow method that accepts a list
of strings.

When the module file is invoked as a script from the command line,
input comes from a list of files or from stdin output goes to stdout,
and exceptions go to stdout.  Input and output are CSV unless a field
delimiter is specified on the command line.

Note that multi-line values are only supported for CSV input and
CSV output.
"""

# Python 3
import sys
import collections
import csv
import getopt

# application
from tabletext import table


class GenCode(object):
    """
    Creates draft code for application that ues table.Column().

    Input comes from an object with an iterator that provides a string
    upon each call to __next__.

    Output goes to an object with a writerow method that accepts a list
    of strings.

    Can be used to produce a draft column definition from a list
    of column headings.  The draft can be manually updated and
    used as an initializer for table.Column().

    Invokes getcolumninfo() during initialization.
    """
    def __init__(self, rowreader, offset=0):
        """
        Invokes getcolumninfo() to initialize self._columndef.
        """
        super().__init__()
        self._columndef = self.getcolumninfo(rowreader, offset)

    def getcolumninfo(self, rowreader, offset=0):
        """
        Read text and return a list of column descriptions.  Create
        default values for items 1 to 3 (input conversion function,
        output conversion function, and column ID) when those items
        are blank.  Each nonblank item is left unchanged,
        
        rowreader gets incoming text for information to create a
        description of column in row- and column- oriented text.
        The text can be in CSV format or some other delimited text from
        which rowreader can sequentially extract lists of strings.
        Each list must have at least (offset + 4) items, see below.

        rowreader is an object with an iterator that generates lists of
            strings (str).
       
        Defaults:
            Blank or    New Value
            missing                 purpose

            row[0]      Unchanged
                                    Optional column heading
            row[1]      "lambda x: None if x == '' else str(x)"
                                    convert input to internal type
            row[2]      "lambda x: '' if x is None else str(x)"
                                    convert internal type to str
            row[3]      Generated column name
                                    unique headings required as ID

        The default functions can be replaced in the input by by other
        functions. For example, to input and output lists:
            row[1]      "lambda x: eval(x)"     convert incoming text
                                                    to an internal list
            row[2]      "lambda x: repr(x)"     output text to recreate
                                                    an internal list
        The functions will not be changed by this program because they
        are nonblank.
        
        Note that multi-line values are only supported when rowreader
        is a csv.reader, and only for headings (first column).

        Note that the use of eval() can make an application vulnerable
        to bad data, and that an application using eval() should only
        receive data from trusted sources.  When possible,
        ast.literal_eval() should be used instead of eval().
        """
        columndef = list()
        namedict = dict()
        row_num = 0
        for row in reader:
            if not isinstance(row, list):
                raise ValueError("rowreader must produce list")
            for i in range(len(row), 4):    # Convert missing values to empty.
                row.append('')
            try:
                heading = row[0].strip()
                infunc = row[1].strip()
                outfunc = row[2].strip()
                colname = row[3].strip()
                # check that strings are valid code for lambda functions
                throwaway_function = table.Column.eval_lambda_function(infunc)
                throwaway_function = table.Column.eval_lambda_function(outfunc)
                # Blank names and duplicate names not allowed.
                if not table.Column.isvalidcolumnname(colname):
                    raise ValueError("Invalid column name: " + repr(colname))
                if colname in namedict:
                    raise ValueError("Duplicate column name: " + repr(colname))
                namedict.setdefault(colname, None)
                columndef.append([heading, infunc, outfunc, colname])
            except Exception as e:
                raise RuntimeError("At row " + str(row_num) + ": " + repr(row)
                                ) from e
            row_num += 1
        return columndef

    def getcolumndef(self):
        """
        Return a list of column descripions.

        Each item in the list is a list of four strings describing one
        column:
        0       Columnn heading
        1       repr() of lampda function for input
        2       repr() of lampda function for output
        3       a python identifier for the column
        """
        return self._columndef

    def writecolumndef(self, writer):
        writer.write('\n'.join([
                "[",
                "    # Column descriptions, four items per column:",
                "    #   Column heading",
                "    #   Data input function, text to internal type",
                "    #   Data output function, internal type to text",
                "    #   Column Name, must be blank or unique",
                "    #\n"]))
        columndef = list()
        groupsep = ''  # outside list has no separator before first inside list
        for (n, description) in enumerate(self._columndef):
            writer.write(',\n'.join([       # an inside list. four items
                ''.join([groupsep,
                         "    [   # Column ", str(n), "\n",
                         "        ", repr(description[0])    ]),
                ''.join(["        ", repr(description[1])    ]),
                ''.join(["        ", repr(description[2])    ]),
                ''.join(["        ", repr(description[3]), "]"    ])
                ]))
            groupsep = ',\n'    # comma, newline between the inside lists
        writer.write('\n    ]\n')

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
        print("       Generate column initializer from column definition",
                file=sys.stderr)
        print("       -h|--help     print this message",
                file=sys.stderr)
        print("       --indelim=    input field delimiter",
                file=sys.stderr)
        print("       --outdelim=   output field delimiter",
                file=sys.stderr)
        print("       zero-length delimiters cause special handling",
                file=sys.stderr)
        print("       omit delimiters to specify CSV formatted text",
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
        # Not CSV, specify a delimiter
        outdelim = opt["--outdelim"]
        if len(outdelim) == 0:
            outdelim = None     # Delimiter is a single space
        rowwriter = table.Delim(outdelim).writer
    else:
        # CSV, use CSV default format
        rowwriter = csv.writer

    # Input data source
    if len(arg) > 0:
        textsource = open(arg[0], newline='')   # no line-end translation
    else:
        textsource = sys.stdin

    # Output a lists of lists that decribe the columns of a table.
    try:
        writer = rowwriter(sys.stdout)
        reader = rowreader(textsource)
        GenCode(reader).writecolumndef(sys.stdout)
    finally:
        if not textsource is sys.stdin:
            textsource.close()
