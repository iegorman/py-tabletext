# examples

## Data Input and Output

Script
 [demo_01.py](./demo_01.py)
illustrates input and output of rows of data from and to formatted text, using the default CSV format.

File
 [demo_01.input.csv](./demo_01.input.csv)
 is a correctly-formatted CSV text file that
 [demo_01.py](./demo_01.py)
 will process without exceptions. The file has several columns, most of which are to be stored as non-string types.

The empty file
 [demo_01.input.ok.empty.csv](./demo_01.input.ok.empty.csv)
 will be processed without exception. There will be no input or output because the file is completely empty (not even a line end).

The file
 [demo_01.input.bad.blank.csv](./demo_01.input.bad.blank.csv)
 will raise an exception because the blank first line does not contain the expected column headings.  The file contains a single line end, which represents a blank line.

Other files 'demo_01.input.bad.*.csv' will raise exceptions because they each have a table cell containing data that is not consistent with the table column specification in script 'demo_01.py'.

File
 The table column specification in script
 [demo_01.py](./demo_01.py)
 was created from the CSV file
 [demo_01.columndef.csv](./demo_01.columndef.csv}
 which was created in stages:
 * File
 [demo_01.input.csv](./demo_01.input.csv)
 was used as input to script
 [headings.py](../headings.py)
 to produce a list of headdings
 [demo_01.heads.csv](./demo_01.heads.csv)
 without enumeration (no sequence numbers).
 * The list of headings was used as input to script
 [gencolumndef.py](../tabletext/gencolumndef.py)
 to creade a draft specification file 'demo_02.columndef.draft.csv'.
 * The draft file was edited to produce the specification file
 [demo_02.columndef.csv](./demo_02.columndef.csv)
 * The edited specifcation file was used as input to script
 [gencode.py](../tabletext/gencode.py)
 to produce an initialiizer for class 'table.Column' in module
 [table.py](../tabletext/table.py)
 
## Re-arranging Columns in a Table

Script
 [demo_02.py](./demo_02.py)
 uses input file
 [demo_02.input.csv](./demo_02.input.csv)
 to illustrate how an application can re-arrange column definitions to produce new tables.

## Creating New Column Definitions
* [gencolumndef.py](../tabletext/gencolumndef.py)
 takes as input a table of one or more columns like
 [gencolumndef.input.head.csv](./gencolumndef.input.head.csv)
 and fills blank cells with defualt values to create a four-column table like
 [gencode.input.csv](./gencode.input.csv)
* The four-column table can be edited in a text editor or a spreadsheet before being used as input to
 [gencode.py](../tabletext/gencode.py)
 to create initialization code
* the 'gencode.input*.csv' files can be used as input to either
 [gencode.py](../tabletext/gencode.py)
 or
 [gencolumndef.py](../tabletext/gencolumndef.py)
 -- the 'gencode.input.bad.*.csv' files will raise exceptions.

