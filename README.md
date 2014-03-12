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


Documentation
-------------
All functions are fully documented using docstrings. To access the
documentation from the terminal use

    $ pydoc lookat
    $ pydoc lookat.canvashandler

Probably more useful is to access the documentation from within
IPython, e.g.

    >>> draw?


Installation
------------
*Depends*

  * ROOT <http://root.cern.ch>
  * IPython <http://ipython.org/>

*Setup*

Run setup.sh. This adds the package to the python path and creates
an alias lookat for the executable.


Configuration
-------------
If you add a file lookat_helper.py at a place where python can find it (i.e. in
PYTHONPATH), lookat will import all names from the file. This is useful to define
frequently used variables like standard selections.

