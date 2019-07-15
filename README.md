# py-tabletext
Tools for input, output and management of tables formatted as CSV or other delimited text with Python 3

Copyright (c) 2019, Ian E. Gorman<br>
All rights reserved.<br>
Released under
 [BSD 2-Clause License](./LICENSE)

This package supports input and output of text formatted as a table of rows and columns. Cell values from the text can be automatically converted to and from the types (such as int or float) used by an application.  Column headings, when used, can be managed and optionally validated by an application.  There are also some operators for simple changes in the column arrangement of tables.

Used with the Pythom 3 'csv' package, this package will support comma-separated-varianle (CSV) text.

Used with the included class 'table.Delim', this package will support tab-delimited text.

## Directories
* [tabletext](./tabletext/)
 -- package to support formatted text tables in applications
* [examples](./examples/)
 -- scripts and data to illustrate use of package 'tabletext'

# Potential Security Problem
 [tabletext.table](./tabletext/table.py)
 supports the use of eval() to translate input data from str (text) to other Python types.  Any application using that feature should accept data only from trusted sources.

# Alpha Version
Subsequent versions may not be backward-compatible with this version.
