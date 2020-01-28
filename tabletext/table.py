#!/usr/bin/env python3
# Tools for data that can be represented as tables with row and columns.

"""
Tools for translating delimited text to and from Python typed values.

This module uses the Python csv package as the foundation for more
elaborate operations with CSV text. csv.reader.

The features added by this module are:
    Readers and Writers that are aware of the column layout of the text.
    Conversion of field (column) values from string to type on input
        and from type to string on output.
    Operators to modify the column layout of the text.
    Control and verification of column headings in the first line of
        text.
    A 'Delim' class to support other forms of delimited text such as
        tab-separated fields

The Column class supports input and output of the rows of a table that
is defined in text as rows and columns.  Each row is delimited as fields
that correspond to columns of the table.  The field values are strings
of text but can be of other types, such as int, when stored internally
by the application. Conversions between string values and typed internal
values is automatic.

Each column has a description consisting of four items:

    Heading             A string (which may be empty) for the heading
                        top of the column.
    Input Function      A lambda function that converts a string value
                        the value type stored by the application.
    Output Function     A lambda function that converts a value from the
                        type stored by to application to the string
                        representation required in the text
    Column name         A unique name, required for each column, that
                        meets the requirements for Python identifiers
                        and does not start or end with an underscore.

Except for the optional column headings, none of the column information
appears in the text.  Instead, all of the information is held by the
application.

Input and output can be with or without column headings.  Headings can
be verified on input, but are not verified on output. The options for
managing headings are identified from the enumeration Column.Policy:

    Column.Policy.NO_HEADING:       No headings
    Column.HEADING_NO_CHECK:        Headings, but no check
    Column.HEADING_EASY_CHECK:      Headings, check when input
                                        Any sequence of whitespace is
                                        equivalent to a single space.
                                        Leading and trailing ignored.
    Column.HEADING_EXACT_CHECK:     Headings, check when input
                                        Every character must match

The input readers are:

    Column.ListInput        Read each row as list of typed values
    Column.DictInput        Read each row as dictionary of typed values
    Column.NamedInput       Read each row as named tuple of typed values

    The readers can be configured to accept short rows (missing fields
    at the end) and will set the corresponding input values to None.

The output writers are:

    Column.ListOutput       Output list of typed values as a row
    Column.DictOutput       Output dictionary of typed values as a row
    Column.NamedOutput      Output named tuple of typed values as a row

    The output writers require rows with a value for every column (no
    short rows).  Values can be set to None for any column with an
    output function that accepts None.

The column operators, which create new instances, are:

    append(columns)         Append columns to the right
    changeheadings(name_heading_pairs)
                            Change the headings of specified columns
    rename(name_pairs)      Change the names of specified columns
    remove(names)           Remove specified columns
    select(names)           Choose a subset of columns and specify order

Security

This module uses run-time compilation with eval() to support flexible
input, output, and type conversion.  Consequently, this module should
only be used with code and data from trusted sources.
"""

# Python 3
import sys
import ast          # support for using ast.literal_eval() in lambda functions
import collections
import csv
from enum import Enum
import keyword
import re
import types

class Column(object):
    """
    Define format and type conversions for the input of formatted and
    delimited text as a table of rows and columns of values, and for
    output of a table as text fromatted into columns of rows and values.

    A 'Column' object can be initialized with a list or tuple of column
    descriptions.  Each column desciption is a list or tuple of four
    items:

        [   heading (any text, or an empty string),
            input function (lambda x: convert text to internal type),
            output function (lambda x: convert internal type to text),
            column name (nonblank)
            ]

        The column name must be unique to each column, must start with a
        letter, not end with an underscore, and contain only letters,
        digits and underscores.

        See the __init__ docstring for more info.

    The 'Column' object has methods for selecting a subset of columns,
    for obtaining column names and instance data as either lists, or
    strings of delimited fields, for saving data to delimited files and
    for loading data from delimited files.

    A Column object, after initialization, is immutable.  Changes to a
    Column object will produce a new Column object.
    """

    # Class data: regular expressions for column name generator
    # One lowercase ASCII letter, followed by lowercase letters, digits,
    # underscores, but with no underscore at either end.
    _re_nowordchar = re.compile(r"[^a-zA-Z0-9_]+")
    _re_space = re.compile(r"\s+")
    _re_multiunder = re.compile(r"_{2,}")
    _re_noleading = re.compile(r"^[_\d]+")
    _re_notrailing = re.compile(r"_+$")

    @classmethod
    def createcolumnname(cls, text):
        '''
        Strip disallowed characters to produce a column name.

        Creates a valid Python identifier that does not begin or end
        with an underscore.  text must contain at least one character
        that becomes an ASCII letter when converted to lowercase.
        '''
        # Names will be used as item names in collections.namedtuple,
        # so must not begin with underscores.
        ident = cls._re_noleading.sub("",
                    cls._re_notrailing.sub("",
                        cls._re_multiunder.sub("_",
                            cls._re_nowordchar.sub("",
                                cls._re_space.sub("_",
                                                        text.lower())))))
        if not cls.isvalidcolumnname(ident):
            raise ValueError("Cannot convert to valid column name: "
                                + repr(text))
        if keyword.iskeyword(ident):
            ident = ident + "_v"
        return ident

    # Class data: regular expressions for column name
    # One ASCII letter, followed by letters, digits, underscores, but
    # with no underscore at either end.  Uppercase is OK.
    _re_identifier = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

    @classmethod
    def isvalidcolumnname(cls, text):
        """
        Indicate whether text is a valid column  name.

        A string is a valid column name if it begins with an ASCII
        letter, continues with ASCII letters (lowercase or uppercase),
        ASCII digits, and underscores, and it does not end with an
        underscore.
        """
        if text.startswith("_") or text.endswith("_"):
            return False
        return False if cls._re_identifier.fullmatch(text) is None else True

    @classmethod
    def eval_lambda_function(cls, func_str):
        '''
        Evaluate and validate a lambda expression.
\
        func_str is a string that should evaluate as a lambda funcition.
        '''
        if not func_str.lstrip().startswith('lambda'):
            raise ValueError(''.join(["Not a lambda expression: ",
                                    repr(func_str)]))
        try:
            func = eval(func_str)           # compile lambda function
            if not isinstance(func, types.LambdaType):
                raise TypeError("Not a function: " + repr(func_str))
        except (SyntaxError, TypeError) as e:
            # Failure to parse correctly will be caused by bad input.
            raise ValueError(''.join(["Not valid source code for a Python",
                                " lambda function: ", repr(func_str)])
                            ) from e
        return func

    # __class__._Policy - how headings should be managed.  Easy check strips
    # leading and trailing whiterspace, converts other sequences of whitespace
    # to a single space character before comparing headings.
    Policy = Enum("Policy", " ".join(["NO_HEADING",
                                    "HEADING_NO_CHECK",
                                    "HEADING_EASY_CHECK",
                                    "HEADING_EXACT_CHECK"]))

    def __init__(self, columns, headingpolicy=None):
        """
        Create a Column instance from another object.

        heading policy is one of:
            None                default (see beloe)
            Column.Policy.NO_HEADING
            Column.Policy.HEADING_NO_CHECK
            Column.Policy.HEADING_EASY_CHECK
            Column.Policy.HEADING_EXACT_CHECK
        See the module docstring for more information

        Parameter 'columns' is:
            another instance of the class
                default headingpolicy is column.Policy
        or
            an iterable (list, tuple, ) of quadruples of column heading,
                    input function (lambda), output function (lambda)
                    and column name (for use as a variable name)
                default headingpolicy is Column.HEADING_EXACT_CHECK
        The order of the columns will be the same as the order in the
        other column instance or the order of the quadruples produced by
        the iterable.

        The input and output functions do any necessary type conversion
        between the external string value and the internally stored
        data.

        Example of column properties for 4 columns to hold strings,
        nullable strings, integers and lists:

        [
            #   Heading
            #       Input Function
            #           Output Function
            #               Column name

            [   "String",
                    "lambda x: str(x)",
                        "lambda x: '' if x is None else str(x)",
                            "string_v"],
            [   "Nullable String",
                    "lambda x: None if x == '' else str(x)"",
                        "lambda x: '' if x is None else str(x)",
                            "nullable_string"],
            [   "Integer",
                    "lambda x: None if x == '' else int(x)",
                        "lambda x: '' if x is None else str(x)",
                            "integer_v"],
            [   "List",
                    "lambda x: None if x == '' else eval(x)",
                        "lambda x: '' if x is None else repr(x)",
                            "list_v"]
        ]

        Column properties would be defined to suit the application.  For
        example, None and '' might be used to represent the absence of a
        numeric value internally (None) and externally (empty string).
        """
        super().__init__()
        if headingpolicy and not isinstance(headingpolicy, __class__.Policy):
            raise ValueError("Invalid heading policy: " + repr(headingpolicy))
        # Create a subclass of NamedTuple for properties of each column
        # when invoked as a function, behaves like a class object
        self._ColProperty = collections.namedtuple("_ColProperty",
                    ["infunc", "outfunc", "heading"])
        # initialize from another instance or from an iterable of iterables
        if isinstance(columns,type(self)):
            # from another instance - make deep copy to avoid shared data
            self._column = collections.OrderedDict(columns._column.items())
            if headingpolicy:
                self._headingpolicy = headingpolicy
            else:
                self._headingpolicy = columns._headingpolicy
        else:
            try:
                self._column = self._columndictionary(columns)
            except Exception as e:
                raise RuntimeError(
                        "While initializing column definition") from e
            if headingpolicy:
                self._headingpolicy = headingpolicy
            else:
                self._headingpolicy = self.Policy.HEADING_EXACT_CHECK
        # attributes with cached values
        # Some of the operators create an instance with no column definitions
        # and then add definitions.  Attributes that depend on the column
        # definitions must exist on first reference but cannot be set to final
        # values until all of the column definitions exist.
        self._NamedRow = None       # returned by self.NamedRow()


    def _columndictionary(self, initdata):
        """
        Create column dictionary from an iterable of iterables of str.

        The iterables must not themselves be type str.

        As of 2019-05-10, the inner iterable produces four items:
            Heading as text
            input function as text for a lambda function
            output function as text for a lambda function
            column name as text
        The corresponding dictionary entry is
            columnname:[inputfunction, outputfunction, heading]
        """
        if isinstance(initdata, str):
            raise ValueError("Intializer is type str")
        column_dictionary = collections.OrderedDict()
        for init in initdata:           # for each column
            if isinstance(init, str):
                raise ValueError("Column description is type str")
            item = [j for j in init]    # convert iterator or generator to list
            # index errors would really be data errors
            if len(item) < 4:
                raise ValueError("Less than 4 items in column description: "
                                + repr(item))
            # item 0, column heading
            column_heading = item[0]
            # allow blank headings, treat missing as blank
            if column_heading is None:
                column_heading = ""
            # items 1 and 2, input and output functions
            infunc = self.eval_lambda_function(item[1])
            outfunc = self.eval_lambda_function(item[2])
            # item 3, column names
            column_name = item[3]
            if column_name in column_dictionary:
                raise ValueError("Duplicate column name: " + column_name)
            if not __class__.isvalidcolumnname(column_name):
                raise ValueError("Invalid column name: " + column_name)
            column_dictionary.setdefault(column_name,
                    self._ColProperty(infunc=infunc,
                                        outfunc=outfunc,
                                        heading=column_heading))
        return column_dictionary

    def __str__(self):
        """
        Names of columns.
        """
        return (__class__.__name__ + ".names=" + repr(self.names()))

    def __len__(self):
        """
        Number of columns.
        """
        return len(self._column)

    def _infunc(self, name):
        return self._column[name].infunc

    def _outfunc(self, name):
        return self._column[name].outfunc

    def _inputlocation(self, line_num):
        """
        Report input location as line offset from beginning.
        """
        return ''.join(["Input line ", str(line_num), ":"])

    def _outputlocation(self, line_num):
        """
        Report output location as line offset from beginning.
        """
        return ''.join(["Output line ", str(line_num), ":"])

    @property
    def names(self):
        """
        Column names as a list of strings.
        """
        return [name for name in self._column.keys()]
    
    def heading(self, name):
        """
        Return the heading of the named column.

        Heading may be an empty string.  Two or more columns could have
        the same heading.
        """
        return self._column[name].heading

    @property
    def headingpolicy(self):
        """
        One of the enumeration Column.Policy:
            Policy.NO_HEADING           No headings
            Policy.HEADING_NO_CHECK     Required headings
            Policy.HEADING_EASY_CHECK   Headings verified, any swqu3ence
                                            of whitespace is equivalent
                                            to ' '
            Policy.HEADING_EXACT_CHECK  Headings verified, exact match
        """
        return self._headingpolicy

    @property
    def NamedRow(self):     # returns a class object for creating instances
        """
        NamedRow class object - creates named tuple of column values.

        NamedRow is a subclass of collections.namedtuple. The item names
        are the same as the column names, and are in the same order.

        Usage:
            NamedRow()
            NamedRow(row)
            NamedRow(name=value, ... )

        If name=value pairs are given, all the column names must be
        included.

        If row is given, it must be an iterable producing the same
        number of values as there are columns in the table.

        If row is not given, the tuple will have the same number of
        items  as there are columns in the table.  Each item will be set
        to None.
        """
        # create namedtuple subclass factory on first invocation, see __init__
        if not self._NamedRow:
            self._NamedRow = collections.namedtuple("NamedRow", self.names)
        return self._NamedRow

    def append(self, columns):
        """
        Append the columns of a second instance to the right of the
        columns in this instance (self).

        Returns a new instance with the additional columns.

        A new column must not have the same name as an original
        column.
        """
        new_instance = self.__class__(self)
        for name in columns._column:
            if name in self._column:
                raise ValueError("Duplicate column name: " + repr(name))
            new_instance._column.setdefault(name, columns._column[name])
        return new_instance

    def changeheadings(self, name_heading_pairs):
        """
        Change the headings of selected columns in place.

        Returns a new instance with the changed columns, all columns in
        original order.  Changes can be given in any order.

        Parameter 'name_heading_pairs' is a list or other iterator of
        string pairs:
            ("column_name", "new heading")
        or
            ["column_name", "new heading"]
        """
        # refuse strings because str is an iterable that we do not handle.
        if isinstance(name_heading_pairs, str):
            raise ValueError("Changes must be iterable of string pairs: "
                            + repr(name_heading_pairs))
        new_instance = self.__class__([])
        change_dict = dict()
        for (name, newhead) in name_heading_pairs:
            if not name in self._column:
                raise ValueError("Column name does not exist: " + repr(name))
            if not isinstance(newhead, str):
                raise ValueError("New heading must be str: " + repr(newhead))
            change_dict.setdefault(name, newhead)
        for (name, v) in self._column.items():
            if name in change_dict:
                new_instance._column.setdefault(name,
                                new_instance._ColProperty(
                                        infunc=v.infunc,
                                        outfunc=v.outfunc,
                                        heading=change_dict[name]))
            else:
                new_instance._column.setdefault(name, v)
        return new_instance

    def remove(self, names):
        """
        Remove a subset of columns.

        Returns a new instance with the remaining columns.

        Parameter 'names' is a list or other iterator of strings.
        Each string must be an existing column name.
        """
        if isinstance(names, str):
            raise ValueError("names must be an iterator of string")
        new_instance = self.__class__(self)
        for name in names:
            if not name in new_instance._column:
                raise ValueError("Heading not present: " + repr(name))
            del new_instance._column[name]
        return new_instance

    def rename(self, name_pairs):
        """
        Change the names of selected columns in place.

        Returns a new instance with the changed columns, all columns in
        original order.  Changes can be given in any order.

        Parameter 'heading_name_pairs' is a list or other iterator of
        string pairs:
            ("old_name", "new_name")
        or
            ["old_name", "new_name"]

        "old_name" must be the name of an existing column,
        "new_name" must not duplicate a name to the left of the column
        currently being renamed.  New name must begin with a letter
        continue with letters, digits and underscores, but must not end
        with an underscore.
        """
        # refuse strings because str is an iterable that we do not handle.
        if isinstance(name_pairs, str):
            raise ValueError("Changes must be iterable of string pairs: "
                            + repr(name_pairs))
        new_instance = self.__class__([])
        name_dict = dict()
        for (oldname, newname) in name_pairs:
            if not oldname in self._column:
                raise ValueError("Column does not exist: " + repr(oldname))
            if not self.isvalidcolumnname(newname):
                raise ValueError("New column name is invalid: "
                                + repr(newname))
            name_dict.setdefault(oldname,newname)
        for name in self.names:
            if name in name_dict:
                newname = name_dict[name]
            else:
                newname = name
            if newname in new_instance._column:
                raise ValueError("Duplicate new column name: " + repr(newname))
            new_instance._column.setdefault(newname, self._column[name])
        return new_instance

    def select(self, names):
        """
        Create a subset (or a full copy) of columns.

        Returns a new instance with the selected columns, in the
        same order as the specified names.

        Parameter 'names' is a list or other iterator of strings.
        Each string must be the name of an existing column and must
        appear only once.
        """
        if isinstance(names, str):
            raise ValueError("names must be an iterator of string")
        for name in names:
            if not name in self._column:
                raise ValueError("Column does not exist: " + repr(name))
        new_instance = self.__class__([])
        for name in names:
            if name in new_instance._column:
                raise ValueError("Duplicate name: " + repr(name))
            new_instance._column.setdefault(name, self._column[name])
        return new_instance


    def ListInput(self, rowreader, shortrowsallowed=False, headingpolicy=None):
        """
        Create reader instance to input lists of typed values.

        Each list will contain itesm in the same order as the columns,
        one item for each column.  Each item will have the type (like
        str or int) that is required for use within the application,

        rowreader is an iterable (like csv.reader) that produces an
        iterable of strings from each line of text input to the
        rowreader

        shortrowsallowed specifies whether a row can be shorter than
        the number of columns.  Missing values are set to None to
        produce a row of full length. 

        headingpolicy is one of:
            None (default to self.headingpolicy),
            Column.Policy.NO_HEADING,
            Column.Policy.HEADING_NO_CHECK,
            Column.Policy.HEADING_EASY_CHECK,
            Column.Policy.HEADING_EXACT_CHECK
        See the module docstring for more info.

        When headingpolicy is NO_HEADING, input will commence when the
        first data list is requested.  Otherwise, the column headings
        will be read immediately.  If the headings are checked and fail
        verification, an exception will be raised immediately.
        Otherwise, input will continue when the first data dictionary is
        requested.

        Usage:
            reader = ListInput(rowreader, shortrowsallowed, headingpolicy)

            for datalist in reader:
                do_something(datalist)

            datalist = next(reader)
            do_something(datalist)

        The number of input lines read (including any headings) will be
        available at any time during the life of the reader:

            input_lines = reader.line_num

        The column headings will be available at any time during the
        life of the reader:

            input_headings = reader.headingrow

        When headingpolicy is NO_HEADING, the headings will be None.
        Otherwise, the column headings will be as read from the input,
        whether or not those headings match the headings defined for
        each column.
        """
        return self.__class__._ListInput(self, rowreader, shortrowsallowed,
                                        headingpolicy)

    class _ListInput(object):
        """
        Reader to input lists of typed values from lists of strings.
        """
        def __init__(self, column, rowreader, shortrowsallowed, headingpolicy):
            self._headings = [column.heading(name) for name in column.names]
            self._infunc = [column._infunc(name) for name in column.names]
            self._inputlocation = column._inputlocation
            self._rowreader = rowreader
            self._re_whitespace = re.compile(r"\s+")
            self._line_num = 0
            if headingpolicy == None:
                self._headingpolicy = column.headingpolicy
            else:
                if isinstance(headingpolicy, column.Policy):
                    self._headingpolicy = headingpolicy
                else:
                    raise ValueError("Invalid heading policy: "
                                    + repr(headingpolicy))
            if self._headingpolicy == column.Policy.NO_HEADING:
                # finished, first row should be data
                self._headingrow = None
                return
            try:
                row = next(self._rowreader)
                # It is OK to have no heading when input is empty, but
                # any text from first line of input should be headings.
                # convert iterable or generator to tuple for multiple use
                self._headingrow = tuple(r for r in row)
                if self._headingpolicy == column.Policy.HEADING_NO_CHECK:
                    # first row is headings, but no check required
                    pass
                elif (self._headingpolicy == column.Policy.HEADING_EASY_CHECK
                        and (self._compressedtuple(h for h in self._headings)
                                == self._compressedtuple(self._headingrow))):
                    # first row is headings that match except for whitespace
                    pass
                elif (self._headingpolicy == column.Policy.HEADING_EXACT_CHECK
                        and  (tuple(h for h in self._headings)
                                == tuple(self._headingrow))):
                    # first row is headings that match including whitespace
                    pass
                else:
                    # failed either becuase heading is not correct or because
                    # headingpolicy is a value that was not included in test
                    raise ValueError(''.join([
                                self._inputlocation(self._line_num),
                                " Error reading headings\nExpected ",
                                repr([h for h in self._headings]),
                                "\nReceived ", repr([r for r
                                                         in self._headingrow]),
                                "Heading Policy: ", repr(headingpolicy)])
                                )
                # headings OK, ready for next line which should be data
                self._line_num += 1
            except StopIteration:
                # Defer any action until the attempt to read first row of
                # data (second line of text) raises another StopIteration.
                pass

        def _compresswhitespace(self, text):
            """
            Remove extra whitespace from a single string.

            Replace all sequences of whitespace by single space, remove
            leading and trailing spaces.
            """
            return  self._re_whitespace.sub(' ', text).strip()

        def _compressedtuple(self, items):
            """
            Remove extra whitespace from each string in an
            iterable of strings, return the results as a tuple.

            Replace all sequences of whitespace by single space, remove
            leading and trailing spaces.
            """
            return tuple(self._compresswhitespace(j) for j in items)

        @property
        def line_num(self):
            """
            This is the number of rows of text that have been read.

            It is also the number of the next row waiting to be read,
            counting from line 0 as the first line.  The count includes
            the heading row if there is one, even though the heading row
            is not returned.

            In CSV text with multiline values, the row coun may be less
            than the line count.
            """
            return self._line_num
    
        @property
        def headingrow(self):
            '''
            Return headings as read from input.

            Returns None if no headings (whenfirst row is data or input is
            empty).

            The headings may not be the same as the headings in the column
            definition/
            '''
            return self._headingrow

        def __iter__(self):
            return self

        def __next__(self):
            """
            Return a line as a list of typed values.
            """
            rowvalues = None
            try:
                row = next(self._rowreader)
                data = [r for r in row] # convert iterator or generator to list
                if len(data) < len(self._headings):
                    if self._shortrowsallowed:
                        for n in range(len(data), len(self._headings)):
                            data[n] = None
                    else:
                        raise ValueError("Expected " + len(self._headings)
                                    + " items, got " + len(row))
                # Convert string values to typed internal values.
                rowvalues = [f(d) for f, d in zip(self._infunc, data)]
                self._line_num += 1
            except SyntaxError as e:
                # Syntax error: eval() or ast.literal_eval() from within
                # self._infunc(), will be caused by an input string that does
                # not parse as a valid Python expression.
                raise ValueError(
                        ''.join([self._inputlocation(self._line_num),
                                " unable to parse incoming text as a Python",
                                " expression"])
                                ) from e
            except Exception as e:
                # Any other error can be forwarded with some additional info.
                raise RuntimeError(self._inputlocation(self._line_num)
                                 + " Error reading data."
                                 ) from e
            return rowvalues


    def ListOutput(self, rowwriter, headingpolicy=None):
        """
        Create writer instance to output list (or other iterable) of
        typed values.

        Each list or iterable must have an item for each column, as many
        items as there are columns. The items are anononymous, but each
        item must be of the type expected by the corresponding column.
        Upon output, each item will be converted from the type used by
        the application to a string of text.

        rowwriter is an object (like cvs.writer) with a writerow method
        that accepts an iterator of strings.

        headingpolicy is one of:
            None (default to self.headingpolicy),
            Column.Policy.NO_HEADING,
            Column.Policy.HEADING_NO_CHECK,
            Column.Policy.HEADING_EASY_CHECK,
            Column.Policy.HEADING_EXACT_CHECK
        See the module docstring for more info.

        When headingpolicy is NO_HEADING, output will commence with the
        first data list.  Otherwise, the column headings will be written
        immediately and output will continue with the first data list.

        Usage:
            writer = ListOutput(rowreader, headingpolicy)

            for datalist in iterable:
                writer.write(datalist)

            writer.writerows(iterable_of_datalist)
        """
        return self.__class__._ListOutput(self, rowwriter, headingpolicy)

    class _ListOutput(object):

        def __init__(self, column, rowwriter, headingpolicy=None):
            self._headings = [column.heading(name) for name in column.names]
            self._outfunc = [column._outfunc(name) for name in column.names]
            self._outputlocation = column._outputlocation
            self._rowwriter = rowwriter
            self._line_num = 0      # not intended for external use
            # headings not checked on output, so the checked write
            # options have the same effect as unchecked write option.
            if headingpolicy != column.Policy.NO_HEADING:
                try:
                    self._rowwriter.writerow(self._headings)
                    self._line_num += 1
                except Exception as e:
                    raise RuntimeError(''.join([
                                self._outputlocation(self._line_num),
                                " Error writing column headings."])
                                 ) from e

        def writerow(self, row):
            """
            Write list of values to output, converting to string
            as necessary.
            """
            try:
                # convert iterator or generator to a reusable list, reject str
                if isinstance(row, str):
                    raise ValueError(''.join(["Row data must be list, tuple",
                                     " or other iterable, but not str"]))
                data = [r for r in row] # convert iterator or generator to list
                if len(data) != len(self._headings):
                    raise ValueError("Expected " + len(self.headings)
                                    + " items, got " + len(data))
                self._rowwriter.writerow(
                                [f(d) for (f, d) in zip(self._outfunc, data)])
                self._line_num += 1
            except Exception as e:
                raise RuntimeError(''.join([
                                 self._outputlocation(self._line_num),
                                 " Error writing data."])
                                 ) from e

        def writerows(self, data):
            """
            Output zero or more lists of values as rows of text.
            """
            for row in data:
                self.writerow(row)


    def DictInput(self, rowreader, shortrowsallowed=False, headingpolicy=None):
        """
        Create reader instance to input ordered dictionaries of typed
        values.

        The keys of the items in each dictionary will be the same as the
        names of the columns and the items will be in the same order as
        the columns.  Each item will have the type (like str or int)
        that is required for use within the application,

        rowreader is an iterable (like csv.reader) that produces an
        iterable of strings from each line of text input to the
        rowreader

        shortrowsallowed specifies whether a row can be shorter than
        the number of columns.  Missing values are set to None to
        produce a row of full length. 

        headingpolicy is one of:
            None (default to self.headingpolicy),
            Column.Policy.NO_HEADING,
            Column.Policy.HEADING_NO_CHECK,
            Column.Policy.HEADING_EASY_CHECK,
            Column.Policy.HEADING_EXACT_CHECK
        See the module docstring for more info.

        When headingpolicy is NO_HEADING, input will commence when the
        first data dictionary is requested.  Otherwise, the column
        headings will be read immediately.  If the headings are checked
        and fail verification, an exception will be raised immediately.
        Otherwise, input will continue when the first data dictionary is
        requested.

        Usage:
            reader = DictInput(rowreader, shortrowsallowed, headingpolicy)

            for dictionary in reader:
                do_something(dictionary)

            dictionary = next(reader)
            do_something(dictionary)

        The number of input lines read (including any headings) will be
        available at any time during the life of the reader:

            input_lines = reader.line_num

        The column headings will be available at any time during the
        life of the reader:

            input_headings = reader.headingrow

        When headingpolicy is NO_HEADING, the headings will be None.
        Otherwise, the column headings will be as read from the input,
        whether or not those headings match the headings defined for
        each column.
        """
        return self.__class__._DictInput(self, rowreader, shortrowsallowed,
                                        headingpolicy)

    class _DictInput(object):

        def __init__(self, column, rowreader, shortrowsallowed, headingpolicy):
            self._names = column.names
            self._inputlocation = column._inputlocation
            self._listinput = column.ListInput(rowreader, shortrowsallowed,
                                                headingpolicy)
            # ListInput will discard headings, so we get line count from
            # ListInput instance instead of counting lines in this instance.
            self._line_num = self._listinput.line_num

        @property
        def line_num(self):
            """
            This is the number of lines that have been read.
            """
            return self._line_num
    
        @property
        def headingrow(self):
            '''
            Return headings as read from input.

            Returns None if no headings (whenfirst row is data or input is
            empty).

            The headings may not be the same as the headings in the column
            definition/
            '''
            return self._listinput.headingrow

        def __iter__(self):
            return self

        def __next__(self):
            """
            Return a line as an ordered dictionary of typed values.
            """
            row = next(self._listinput)     # get row and check length
            data = (collections.OrderedDict([(h, r) for h, r
                                        in zip(self._names, row)]))
            self._line_num = self._listinput.line_num
            return data


    def DictOutput(self, rowwriter, headingpolicy=None):
        """
        Create writer instance to output dictionaries of typed values.

        Each dictionary must have a keyed item for each column.  The
        key of each item must be the same as the column name of the
        corresponding column.  Upon output, each item will be converted
        from the type used by the application to a string of text.

        rowwriter is an object (like cvs.writer) with a writerow method
        that accepts an iterator of strings.

        headingpolicy is one of:
            None (default to self.headingpolicy),
            Column.Policy.NO_HEADING,
            Column.Policy.HEADING_NO_CHECK,
            Column.Policy.HEADING_EASY_CHECK,
            Column.Policy.HEADING_EXACT_CHECK
        See the module docstring for more info.

        When headingpolicy is NO_HEADING, output will commence with the
        first data dictionary.  Otherwise, the column headings will be
        written immediately and output will continue with the first
        data dictionary.

        Usage:
            writer = DictOutput(rowreader, headingpolicy)

            for dictionary in iterable:
                writer.write(dictionary)

            writer.writerows(iterable_of_dictionary)
        """
        return self.__class__._DictOutput(self, rowwriter, headingpolicy)

    class _DictOutput(object):

        def __init__(self, column, rowwriter, hasheadings):
            self._names = column.names
            self._outputlocation = column._outputlocation
            self._listoutput = column.ListOutput(rowwriter, hasheadings)
            # ListOutput will write headings, so we get line count from
            # ListOutput instance instead of counting lines in this instance.
            self._line_num = self._listoutput._line_num

        def writerow(self, dictionary):
            """
            Write the values for each key of the dictionary to the
            corresponding named columns, converting internal values to
            strings as necessary.
            """
            try:
                self._listoutput.writerow(
                                    dictionary[name] for name in self._names)
                self._line_num = self._listoutput._line_num
            except KeyError as e:
                raise ValueError(''.join(
                                [self._outputlocation(self._line_num),
                                " dictionary is missing values for one or",
                                " more columns of output.",
                                "\nColumn names:\n",
                                repr(self._names),
                                "\nDictionary names:\n",
                                repr(dictionary.keys())
                                ])
                                 ) from e

        def writerows(self, dictionaryiterator):
            """
            Write the values for each key of each dictionary to the
            corresponding named columns, converting internal values to
            strings as necessary.
            """
            for dictionary in dictionaryiterator:
                self.writerow(dictionary)


    def NamedInput(self, rowreader, shortrowsallowed=False,
                    headingpolicy=None):
        """
        Create a reader instance to input namedtuples of typed values.

        The names of the items in each namedtuple will be the same as
        names of the columns and the items will be in the same order as
        the columns.  Each item will have the type (like str or int)
        that is required for use within the application,

        rowreader is an iterable (like csv.reader) that produces an
        iterable of strings from each line of text input to the
        rowreader

        shortrowsallowed specifies whether a row can be shorter than
        the number of columns.  Missing values are set to None to
        produce a row of full length. 

        headingpolicy is one of:
            None (default to self.headingpolicy),
            Column.Policy.NO_HEADING,
            Column.Policy.HEADING_NO_CHECK,
            Column.Policy.HEADING_EASY_CHECK,
            Column.Policy.HEADING_EXACT_CHECK
        See the module docstring for more info.

        When headingpolicy is NO_HEADING, input will commence when the
        first data tuple is requested.  Otherwise, the column headings
        will be read immediately.  If the headings are checked and fail
        verification, an exception will be raised immediately.
        Otherwise, input will continue when the first data tuple is
        requested.

        Usage:
            reader = NamedInput(rowreader, shortrowsallowed, headingpolicy)

            for namedtuple in reader:
                do_something(namedtuple)

            namedtuple = next(reader)
            do_something(namedtuple)

        The number of input lines read (including any headings) will be
        available at any time during the life of the reader:

            input_lines = reader.line_num

        The column headings will be available at any time during the
        life of the reader:

            input_headings = reader.headingrow

        When headingpolicy is NO_HEADING, the headings will be None.
        Otherwise, the column headings will be as read from the input,
        whether or not those headings match the headings defined for
        each column.
        """
        return self.__class__._NamedInput(self, rowreader, shortrowsallowed,
                                            headingpolicy)

    class _NamedInput(object):

        def __init__(self, column, rowreader, shortrowsallowed, headingpolicy):
            # self._names = column.names
            self._inputlocation = column._inputlocation
            self._listinput = column.ListInput(rowreader, shortrowsallowed,
                                                headingpolicy)
            self.NamedRow = column.NamedRow
            # ListInput will discard headings, so we get line count from
            # ListInput instance instead of counting lines in this instance.
            self._line_num = self._listinput.line_num

        @property
        def line_num(self):
            """
            This is the number of lines that have been read.
            """
            return self._line_num
    
        @property
        def headingrow(self):
            '''
            Return headings as read from input.

            Returns None if no headings (whenfirst row is data or input is
            empty).

            The headings may not be the same as the headings in the column
            definition.
            '''
            return self._listinput.headingrow

        def __iter__(self):
            return self

        def __next__(self):
            """
            Return a line as an ordered dictionary of typed values.
            """
            row = next(self._listinput)     # get row and check length
            data = self.NamedRow._make(row)
            self._line_num = self._listinput.line_num
            return data


    def NamedOutput(self, rowwriter, headingpolicy=None):
        """
        Create writer instance to output namwd tuples of typed values.

        Each namedtuple must have a named item for each column.  The
        name of each item must be the same as the column name of the
        corresponding column.  Upon output, each item will be converted
        from the type used by the application to a string of text.

        rowwriter is an object (like cvs.writer) with a writerow method
        that accepts an iterator of strings.

        headingpolicy is one of:
            None (default to self.headingpolicy),
            Column.Policy.NO_HEADING,
            Column.Policy.HEADING_NO_CHECK,
            Column.Policy.HEADING_EASY_CHECK,
            Column.Policy.HEADING_EXACT_CHECK
        See the module docstring for more info.

        When headingpolicy is NO_HEADING, output will commence with the
        first data tuple.  Otherwise, the column headings will be
        written immediately and output will continue with the first
        data tuple.

        Usage:
            writer = NamedOutput(rowreader, headingpolicy)

            for namedtuple in iterable:
                writer.write(namedtuple)

            writer.writerows(iterable_of_namedtuple)
        """
        return self._NamedOutput(self, rowwriter, headingpolicy)

    class _NamedOutput(object):

        def __init__(self, column, rowwriter, headingpolicy):
            self._names = column.names
            self._outputlocation = column._outputlocation
            self._listoutput = column.ListOutput(rowwriter, headingpolicy)
            # ListOutput will write headings, so we get line count from
            # ListOutput instance instead of counting lines in this instance.
            self._line_num = self._listoutput._line_num

        def writerow(self, namedtuple):
            """
            Write the named items of the tuple to the corresponding
            named columns, converting internal values to strings as
            necessary.
            """
            rowdictionary = namedtuple._asdict()
            try:
                self._listoutput.writerow(
                                rowdictionary[name] for name in self._names)
                self._line_num = self._listoutput._line_num
            except KeyError as e:
                raise ValueError(''.join([
                                self._outputlocation(self._line_num),
                                " namedtuple is missing values for one or",
                                " more column names.",
                                "\nColumn names:\n",
                                repr(self._names),
                                "\ntuple names:\n",
                                repr(rowdictionary.keys())
                                ]) ) from e

        def writerows(self, namedtupleiterator):
            """
            Write the named items of each tuple to the corresponding
            named columns, converting internal values to strings as
            necessary.
            """
            for namedtuple in namedtupleiterator:
                self.writerow(namedtuple)


class Delim(object):
    """
    Factory to create readers and writers for non-CSV delimited data.

    Delim.reader() behaves similarly to csv.reader():
        Creates an iterator that extracts a list of substrings from each
            string produced by the source object.
        Requires a source object that is a iterable of single
            strings, with or without line-ends
        Has a line_num attribute to count the source strings.

        Usage:
            # reader can be any iterable that produces strings of text.
            # Line ends are allowed, but only at the end of text, where
            # they will be ignored.
            reader = Delim(delimiter).reader(line-iterator)

            for row in reader:
                do_something(row)

            row = next(reader)
            do_something(row)

            number_of_lines_read = reader.line_num

    Delim.writer() behaves similarly to csv.writer):
        Returns an object with a writerow() method that accepts an
            iterable of strings
        Requires a destination object with a write() method that
            accepts one string per invocation.
        Has a writerow() method that accepts a list or other iterable of
            strings.

        Usage:
            # textwriter can be any object with a write() method
            # that accepts type str.
            writer = Delim(delimiter).writer(textwriter)

            writer.writerow(iterable_of_str)
            writer.writerows(iterable_of_iterable_of_str)
    """
    def __init__(self, delimiter):
        """
        Initialize a factory for delimited reader and writer objects.

        delimiter is a string of one or more characters used as a column
        or field separator.  Zero-length string is no delimiter
        (entire line is a single field).  None is a special delimiter
        (single space for output, any sequence of consecutive spaces
        for input).
        """
        # on input, behaviour is as with str.split(delimiter)
        self.delimread = delimiter

        # on output, behaviour is as with delimiter.join([str for str in list])
        if delimiter:
            self.delimwrite = delimiter
        else:
            # None implies unspecified, so default to one space
            self.delimwrite = ' '

    def reader(self, textreader):
        """
        Create a reader that splits text lines and returns lists of str.

        Text is split at each delimiter unless the delimiter is an empty
        string (no delimiter).

        textreader is an iterable that returns a single string at each
        iteration.
        """
        return self._reader(textreader, self.delimread)

    class _reader(object):
        """
        Reader similar to CSV reader, but for delimited text.
        """
        def __init__(self, textreader, delim):
            self._line_num = 0
            self.textreader = textreader
            self.delim = delim

        def __iter__(self):
            return self

        def __next__(self):
            """
            Get next line as list of string, and count lines.
            """
            line = next(self.textreader)
            row = line.rstrip("\n\r").split(self.delim)
            self._line_num += 1
            return row

        @property
        def line_num(self):
            """
            Number of lines read before current line.
            """
            return self._line_num

    def writer(self, textwriter):
        """
        Create a writer that accepts lists of str and writes each list
        as a single string of fields (the list items) joined by a
        specified separator string (the delimiter).

        textwriter is an object with a write() method that accepts a
        single string at each invocation.
        """
        return self._writer(textwriter, self.delimwrite)

    class _writer(object):
        """
        Writer similar to CSV writer, but for delimited text.
        """
        def __init__(self, textwriter, delim):
            self.textwriter = textwriter
            self.delim = delim

        def writerow(self, row):
            self.textwriter.write(self.delim.join(str(r) for r in row) + "\n")

        def writerows(self, rows):
            for row in rows:
                self.writerow(row)


if __name__ == "__main__":
    """Run as a script when invoked from shell command line."""

    raise NotImplementedError("'" + sys.argv[0] 
                        + "' does not currently run as a standalone script")