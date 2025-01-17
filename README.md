# pyfind
A Simple Indexer and Search Tool

This is the result of my annoyance with existing tools to find file based on metadata on internal or external disks.
The indexer used in modern operating systems, in windows or macos, is really not particularly smart, invasive and
cannot be used with offline disks.

This tool is very simple, use scan.py to scan your filesystem, launch it on the root folder, like

> python3 scan.py /Volumes/NameOfDisk/

it create a fs.db file that you can rename as your NameOfDisk.db, and store where you want. The scan is very fast, it scan a 2TB disk in few seconds.

Use search.py to search for files that meet several critera, I prefer to search on an interval of date, using the modified date. 
You can get help with -h:

''''
> python3 printdb.py -h

usage: printdb.py [-h] [-s {0,1,2}] [-o OFFSET] [-t TYPE]
                  start end name [filter ...]
positional arguments:
  start                 start date
  end                   end date
  name                  filename
  filter                filter
options:
  -h, --help            show this help message and exit
  -s {0,1,2}, --sort {0,1,2}
                        sort order
  -o OFFSET, --offset OFFSET
                        year offset
  -t TYPE, --type TYPE  file type
''''

So, for example:

> python3 search.py 01/03/2024 04/05/2024

simply print all file (last modified) between the first of March 2024, and 04 May. 

The sorting can be changed with -s, with 1 = sort by path, and 2 = sort by increasing size.

The -o <k> offset is usefull to shift the dates by <k> years, so you don't have to change the dates to search in a larger interval.

The -t type allow to specify a file name extension and filter the resul only to file with that extension. 

The filter at the end is a list of names, that can start eventually with '^', it filter the result by including only the path that have [any] of the name in it, or exclude the ones that start with '^'.

