lookat
======

Quickly inspect the content of ROOT files


Description
-----------
Lookat provides a simple command-line interface for the most common tasks
when inspecting a root file. It defines several helpful functions reducing
the amount of typing needed during data exploration.
Several global lists provide access to previously created objects.


Example Usage
-------------
Open a root file for inspection

    $ lookat test_input.root

Load a tree

    >>> load('simple_tree')

create two histograms for two leaves (on same pad)

    >>> draw('int_leaf')
    >>> draw('double_leaf*5')

add a pad showing the ratio of the latest two histograms

    >>> draw_ratio()


Installation
------------
*Depends*

  * ROOT <http://root.cern.ch>
  * IPython <http://ipython.org/>

*Setup*

Run setup.sh to add the package to the python path and add an alias for lookat.


Configuration
-------------
If you add a file lookat_helpers.py at a place where python can find it (i.e. in 
PYTHONPATH), lookat will import all names from the file. This is useful to define 
frequently used variables like standard selections.

