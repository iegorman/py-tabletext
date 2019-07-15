# tabletext
Manage tables formatted as delimited text.

This package includes three separate parts:
* Simple scripts to explore unknown text and get some knowledge of specifice format and the range of values in the different columns of the table represented by the text.
* Simple scripts to create a draft definition of the table.  The draft definition can be edited using knowledge gained from exploration of the text and can be used to create an initialization for the table code used in the application.
* Code for the Python classes that will be used to support formatted text tables in the application.

The package supports CSV and other forms of delimited text.  CSV is the default when no other format is specified.

# Potential Security Problem
The package supports the use of eval() to translate input data from str (text) to other Python types.  Any application using that feature should accept data only from trusted sources.

# Summary Description

## Application Support
Code to support application use of tables formatted as text
* [table.py](./table.py) -- input and output of table rows
    * Input row of text as lists, dictionaries or named tuples of typed value
        * ListInput -- list of table cell values
        * DictInput -- dictionary of table cell values keywed by column name
        * NamedInput -- named (by column name) tuple of table cell values
    * Output of lists, dictionaries or named tuples of typed values as row of text
        * ListOutput -- list of table cell values
        * DictOuput -- dictionary of table cell values keywed by column name
        * NamedOuput -- named (by column name) tuple of table cell values
    * Alter the columns of a table
        * append -- Append columns to the right of a table
        * changeheadings -- Change the headings of specified columns
        * rename -- Change the names of specified columns
        * remove -- Remove specified columns
        * select -- Choose a subset of columns and specify order

## Scripts for Exploring Formatted Text Tables
* [fields.py](./fields.py) -- Provide summary information about a table
* [fieldstrip.py](./fieldstrip.py) -- strip leading and trailing spaces from each cell value
* [headings.py](./headings.py) -- List the cell values from first row, each on a separate line

## Scripts Generating Table Column Descriptions
* [gencode.py](./gencode.py) -- generate a table initializer from a table definition
* [gencolumndef.py](./gencolumndef.py) -- generate draft table definition from a list of column headings

If the table definitions are in CSV format (the defrault), they can be edited in a spreadsheet.  All table definitions can be editted in a text editor.
