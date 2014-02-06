#!/usr/bin/ipython -i
# pylint: disable-msg=E0611, W0602, W0611, W0614, C0103
""" lookat - quickly inspect the content of root files

Copyright 2013, Nicola Chiapolini, nicola.chiapolini@physik.uzh.ch

License: GNU General Public License version 2,
         or (at your option) any later version.

lookat provides a simple command-line interface for the most common tasks
when inspecting a root file. It defines several helpful functions reducing
the amount of typing needed during data exploration.
Several global lists provide access to previously created objects.

"""

import atexit
from lookat.canvashandler import CanvasHandler
from ROOT import TFile, TChain, TTree
from ROOT import TH1F, TH2F
from ROOT import gDirectory
from ROOT import gPad
from ROOT import kRed, kBlue, kGreen, kBlack
try:
# pylint: disable-msg=W0401
    from lookat_helper import *
# pylint: enable-msg=W0401
except ImportError:
    pass
from math import log, exp, sqrt

gCanvs  = []
gFiles  = []
gHistos = []
gTrees  = []

TH1F.SetDefaultSumw2()
TH2F.SetDefaultSumw2()
gWorkspace = TFile('workspace.root', 'recreate')

def active_canvas():
    """ get active canvas

    Finde the CanvasHandler containing the active pad

    """
    cleanup()
    active_name = gPad.GetCanvas().GetName()
    for canv in gCanvs:
        if canv.GetName() == active_name:
            return canv

def active_pad():
    """ get active pad

    Finde the PadHandler containing the active pad

    """
    cleanup()
    active_name = gPad.GetName()
    for canv in gCanvs:
        for pad in canv.pads.itervalues():
            if pad.GetName() == active_name:
                return pad

class RatioTHnF(object):
    """ class for ratio histograms """

    def __init__(self, h_num, h_denum, normalised):
        """ create a ratio histogram

        Creates containing the ratio of two input histograms
        The input histograms are weighted with the respective number of entries

        Parameters
        ----------
        h_num : THnF
            histogram used for numerator
        h_denum : THnF
            histogram used for denumerator
        normalised : Boolean
            if True, the histograms are weighted to an area of 1

        """
        self._pads       = []
        self._num        = h_num
        self._denum      = h_denum
        self._normalised = normalised
        res_name = _get_unique_hname("ratio_{0}")
        self._ratio = self._num.Clone()
        self._ratio.SetName(res_name)
        try:
            self._var_info = self._num.var_info
        except AttributeError:
            print "Warning: numerator histogram has no var_info attribute"
            print "         use set_varinfo('var') to set manually."
            self._var_info = None
        if type(self._ratio) == TH2F:
            self.get_content = self._get_content_2d
        else:
            self.get_content = self._get_content_1d
        weight_num   = 1.0
        weight_denum = 1.0
        if self._normalised:
            weight_num   = 1.0/h_num.GetSumOfWeights()
            weight_denum = 1.0/h_denum.GetSumOfWeights()
        self._ratio.Divide(h_num, h_denum, weight_num, weight_denum)
        self.update_color()

    @property
    def var_info(self):
        """ get var_info (variable filled) for this histogram

        """
        return self._var_info

    def set_varinfo(self, varinfo):
        """ set var_info

        var_info should contain the string used to TTree.Draw() the histogram.

        """
        self._var_info = varinfo

    def __repr__(self):
        """ get informativ string representation """
        out_string  = "<RatioTHnF object ("+self._num.GetName()+"/"
        out_string += self._denum.GetName()+")>"
        return out_string

    def clean_pads(self):
        """ remove dead PadHandler from the list of pads

        """
        for pad in self._pads:
            try:
                pad.GetName()
            except AttributeError:
                self._pads.remove(pad)

    def Draw(self, draw_opts):
        """ draw the ratio THnF and configure the layout

        Draws the ratio THnF on the active pad. The active pad is stored and
        the layout of uptimised for ratio plots.

        Parameters
        ----------
        draw_opts : string
            draw options for THnF.Draw()

        """
        self._ratio.Draw(draw_opts)
        self._ratio.SetStats(0)

        pad = active_pad()
        if not pad in self._pads:
            self._pads.append(pad)
        if self._normalised:
            pad.set_yrange(0, 2.1)
        pad.SetGrid()
        pad.Update()

    def set_yrange(self, y_min, y_max):
        """ set the y-range of this ratio THnF

        Updates each pad containig this ratio THnF with the given y-range

        Parameters
        ----------
        y_min : float
            min value for the y axis
        y_max : float
            max value for the y axis

        """
        self.clean_pads()
        for pad in self._pads:
            pad.set_yrange(y_min, y_max)

    def update_color(self):
        """ update the line color of the ratio THnF
        to match the one from the numerator THnF

        """
        self._ratio.SetLineColor( self._num.GetLineColor() )

    def GetName(self):
        """ get the name of the ratio THnF

        """
        return self._ratio.GetName()

    def SetName(self, name):
        """ get the name of the ratio THnF

        """
        return self._ratio.SetName(name)

    def Write(self):
        """ write the ratio TH1F or TH2F into the present directory

        """
        self._ratio.Write()

    def Delete(self):
        """ delete the ratio THnF

        """
        self._ratio.Delete()

    @property
    def bin_edges_x(self):
        """ get the edges of all bins in this histogram

        Returns
        -------
        edges : list
            list containing the edges of all bins
            e.g: [0,1,2,3,4,5] for [0,5] divided into 5 bins of equal width

        """
        edges = []
        n_bins = self._ratio.GetNbinsX()
        for i in range(1, n_bins ):
            edges.append(self._ratio.GetBinLowEdge(i) )
        edges.append(edges[-1]+self._ratio.GetBinWidth(n_bins))
        return edges

    get_content_docstring = """
    Parameters
    ----------
    evt : TTree event
        event to look up
    tree : TTree where this event was comming from

    Returns
    -------
    content : float
        content of bin containing evt

    """

    def _get_content_1d(self, evt):
        """ get content of bin containing the passed event

        helper function for 1d histograms

        """
        return self._ratio.GetBinContent(
                   self._ratio.FindFixBin( evt.__getattr__(self._var_info) )
               )

    def _get_content_2d(self, evt):
        """ get content of bin containing the passed event

        helper function for 2d histograms

        """
        var_y, var_x = self._var_info.split(':')
        return self._ratio.GetBinContent(  self._ratio.FindFixBin(
                    evt.__getattr__(var_x),
                    evt.__getattr__(var_y),
               ) )

    #pylint: disable-msg=E1101
    _get_content_1d.__doc__ += get_content_docstring
    _get_content_2d.__doc__ += get_content_docstring
    #pylint: enable-msg=E1101


def get_branch_list(names_only=True, tree=None):
    """ get list of branches in tree

    creates a python list with either the branch-names or branch-objects in
    the tree. You could use tree.Print() as well, but that might be longer
    then your output-buffer and goes to stdout directly.

    Parameters
    ----------
    names_only : boolean
        create a list with branch names only (if True, default) or with the
        branch objects (if False)
    tree : TTree
        create the list for this tree

    Returns
    -------
    branch_list : list of strings or TBranch
        list with choosen info on branches

    """
    if tree == None:
        tree = gTrees[-1]
    if names_only:
        branch_list = [b.GetName() for b in tree.GetListOfBranches()]
    else:
        branch_list = [b for b in tree.GetListOfBranches()]
    return branch_list

def cleanup(include_histos = False):
    """ remove unneeded entries from the global lists

    Removes old entries from gCanvs left behind when a canvas window is closed.
    If include_histos is True, removes all histograms that  are not conected
    with any pad too.

    Parameters
    ----------
    include_histos : boolean
        if true, cleanup histograms too (default: False)

    """
    for canv in gCanvs:
        if canv.canv == None:
            gCanvs.remove(canv)
    if include_histos:
        orphaned = list(gHistos)
        for canv in gCanvs:
            for pad in canv.pads.itervalues():
                for h in gHistos:
                    # check if histogram is linked with this canvas
                    # and remove it from ''orphaned'' if it is
                    print("trying "+h.GetName())
                    if pad.has_primitive( h.GetName() ):
                        orphaned.remove(h)
        for h in orphaned:
            gHistos.remove(h)
            try:
                h.Delete()
            except ReferenceError or AttributeError:
                pass

def add_file(name):
    """ open root file 'name'

    A new TFile-object for 'name' is created and added to gFiles.

    Parameters
    ----------
    name : string
        name (and path) of the file to open

    Returns
    -------
    the_file : TFile
        newly created file-object

    """
    global gFiles
    gFiles.append( TFile( name ) )
    print(name+" added to gFiles.")
    gWorkspace.cd()
    return gFiles[-1]

def load(name, from_file=None):
    """ load TTree 'name'

    Loads 'name' from the last added file (or from_file if specified) and
    appends it to gTrees.

    Parameters
    ----------
    name : string
        name (and path) of the tree to load
    from_file : TFile
        file to get tree from (default: gFiles[-1])

    Returns
    -------
    the_tree : TTree
        newly loaded tree-object

    """
    global gTrees
    if from_file == None:
        from_file = gFiles[-1]
    gTrees.append( from_file.Get( name ) )
    return gTrees[-1]

def create_chain(name, files):
    """ create TChain for 'name'-trees and add files

    A new chanin with the given name is created, all specified files are added
    and the chain is appended to gTrees.

    Parameters
    ----------
    name : string
        name (and path) of the tree to load
    files : list of TFiles
        files to add to chain

    Returns
    -------
    the_tree : TChain
        new chain-object

    """
    global gTrees
    chain = TChain(name, "")
    for f in files:
        chain.Add(f)
    gTrees.append( chain )
    print("added new chain")
    print("   "+str(files))
    return gTrees[-1]

def put_texts(title=None, xlabel=None, ylabel=None):
    """ add title, x-label and y-label to active canvas

    Change title, x-label and y-label for the active canvas.

    Parameters
    ----------
    title : strings
        new title for canvas
    xlabel : strings
        new x-label for histograms
    ylabel : strings
        new y-label for histograms

    """
    gCanvs[-1].put_texts(title, xlabel, ylabel)


def canvas(name = ""):
    """ create a new canvas

    Creates a new CanvasHandler for a canvas with given name and appends the
    handler to gCanvs. Additionally garbage-collects previously closed canvases

    Returns
    -------
    the_canvas : TCanvas
        new canvas-object

    """
    cleanup()
    global gCanvs
    gCanvs.append( CanvasHandler( name ) )
    return gCanvs[-1]

def th1f(h_name, binning):
    """ create a new empty histogram

    Creates an empty histogram with the given name and binning. SumW2 is called
    to make uncertainties for weighted histograms are handled correctly.
    The histogram is appended to gHistos.

    Parameters
    ----------
    h_name: string
        name for new histogram
    binning : 3-tuple or list
        if a tuple: (n_bins, lower_edge, upper_edge)
        if a list:  edges of bins

    Returns
    -------
    the_histo : TH1F
        new th1f-object

    """
    if type(binning) == tuple:
        gHistos.append(
            TH1F(h_name, h_name, binning[0], binning[1], binning[2])
        )
    else:
        try:
            import numpy
            bin_edges = numpy.array([e for e in binning], dtype=numpy.float64)
            n_bins = len(bin_edges)-1
            gHistos.append( TH1F(h_name, h_name, n_bins, bin_edges) )
        except TypeError:
            raise RuntimeError("histogram configuration not recognised!")
    gHistos[-1].Sumw2()
    return gHistos[-1]

def sel(var, low, high):
    """ create selection string for var in range (low, high)

    returns the selection string "low < var && var < high", low and high will
    have a precision of 2 decimal places, such that the string can be used as
    title too.

    Parameters
    ----------
    var : string
        variable to cut on
    low : float
        lower edge of selection range
    high : float
        higher edge of selection range

    Returns
    -------
    sel : string
        selection string

    """
    return "{1:.2f} < {0:s} && {0:s} < {2:.2f}".format(var, low, high)

def normalise():
    """ normalise histograms on active canvas

    Scales all histograms on the active canvas to have an integral of 1. Adds
    a corresponding y-axis label

    """
    for h in active_pad().get_primitives(TH1F):
#        h.Sumw2()
        h.Scale(1/h.Integral())
    put_texts(ylabel = "normalised to unity")

def legend(labels, colors=None, pos=None):
    """ create a legend for the active canvas

    Add a legend to the active canvas, labeling the histograms and changing
    their color if specified. Makes sure ratio plots connected with the
    relevant histograms get updated as well.

    Parameters
    ----------
    labels : list of strings
        labels for the histograms (in same order as they were drawn)
    colors : list of TColors
        line-colors to set for the histograms
    pos : iterable with four float-entries
        postion of the legend, (x_min, y_min, x_max, y_max) in [0, 1]

    Returns
    -------
    the_legend : TLegend
        new legend-object

    """
    l = active_canvas().add_legend(labels, colors, pos)
    for h in gHistos:
        if type(h) == RatioTHnF:
            h.update_color()
    return l

def get_legend():
    """ get legend of active canvas

    Returns
    -------
    the_legend : TLegend
        legend-object of active canvas

    """
    return active_canvas().legend

def _get_unique_hname(h_name):
    """ get a unique histogram name based on h_name

    Parameters
    ----------
    h_name : string
        base for histogram name. {0} will be replaced by a unique number.
        If the pattern is missing, the number will be appended at the end.

    Returns
    -------
    name : string
        histogram name that does not exist in gDirectory yet

    """
    if h_name.find('{0}') == -1:
        h_name += '_{0}'
    n = len(gHistos)
    while True:
        name = h_name.format(n)
        if type(gDirectory.Get(name)) != TH1F:
            break
        n += 1
    return name

def _prepare_drawopts(n_dim = 1):
    """ determine correct drawing option

    if the active pad has a 1D-histogram, add further 1D histograms to the
    existing axes. Otherwise draw new axes.

    Parameters
    ----------
    n_dim : int
        dimensions of the new histogram

    Returns
    -------
    draw_opts : string
        draw options for the Draw() functions

    """
    if n_dim == 2:
        draw_opts = "colz"
    else:
        draw_opts = "same"
        try:
            active_pad().get_primitives(TH1F).next()
        except StopIteration:
            draw_opts = "Ep"
    return draw_opts

def draw(var, select="", h_name="myHist_{0}", h_cfg=None, tree=None):
    """ create a histogram for given variable ''var''

    Creates a canvas if non exists. If this will be the first histogram on the
    active canvas, create axis. Otherwise draw histogram into the existing
    axis.
    If a new histogram is created, it is appended to gHistos.

    Parameters
    ----------
    var : string
        variable to plot, the root syntax of var1:var2 can be used to create
        2d histograms
    select : string
        selection/weight to appy (default: "")
    h_name : string
        name of histogram to fill. If present a '{0}' pattern will be replaced
        by a unique number. If a histogram 'h_name' exists already, it will be
        replaced. To append to an existing histogram start the name with '+'.
        ( default: "myHist_{0}" )
    h_cfg : string
        histogram configuration as used by TTree.Draw() ( default: "(40)" )
        Root might decide to ignore this setting (e.g. for variables with
        only a few distinct values.)
    tree : TTree
        tree to take events from (default: gTrees[-1])

    Returns
    -------
    the_histo : TH1F or TH2F
        new histogram-object

    """
    global gHistos, gCanvs, gTrees
    cleanup()
    if len(gCanvs) == 0:
        canvas()
    gCanvs[-1].cd()
    ### check dimensions
    n_dim = var.count(':')+1
    if n_dim > 2:
        raise NotImplementedError("draw() supports 1- and 2-D histograms only")
    ### prepare histogram binning
    if h_cfg == None:
        if n_dim == 1:
            h_cfg = "(40)"
        elif n_dim == 2:
            h_cfg = ""
    if h_name[0] == "+":
        h_cfg = ""
    ### prepare name-string for Draw methode
    name = h_name
    if h_name.find('{0}') != -1:
        name = _get_unique_hname(h_name)
    ### prepare draw option
    draw_opts = _prepare_drawopts(n_dim)
    ### draw
    if tree == None:
        tree = gTrees[-1]
    tree.Draw(var+'>>'+name+h_cfg, select, draw_opts)
    ### store histogram
    if name[0] != "+":
        h = gPad.GetPrimitive(name)
        gHistos.append(h)
    else:
        h = gPad.GetPrimitive(name[1:])
    h.var_info = var
    put_texts(xlabel=var)
    return h

def draw_ratio(h_num = None, h_denum = None, canv = None, normalised = True):
    """ create a ratio plot

    Parameters
    ----------
    h_num : THnF
        histogram to use for numerator
    h_denum : THnF
        histogram to use for denumerator
    canv : CanvasHandler
        canvas where ratio should be draw on
    normalised : Boolean
        if True, the histograms are weighted to an area of 1 (default: True)

    Returns
    -------
    the_histo : RatioTHnF
        new ratio-object

    """
    global gPad
    old_pad = gPad.GetPad(0)
    if h_num == None:
        h_num = gHistos[-1]
    if h_denum == None:
        h_denum = gHistos[-2]
    if canv == None:
        canv = active_canvas()
    draw_opts = "same"
    if canv.cd_ratio():  # cd_ratio() returns true if new pad was created
        draw_opts = "Ep"
    if type(h_num) == TH2F:
        canv.full_pad("ratio")
        draw_opts = "colz"
    ratio = RatioTHnF(h_num, h_denum, normalised)
    ratio.Draw(draw_opts)
    gHistos.append(ratio)
    canv.canv.cd()
    gPad.Update()
    old_pad.cd()
    return ratio

def draw_corrected(var, h_eff, select="", h_cfg=None, tree=None):
    """ create a 1D histogram for ''var'' corrected for an efficiency effect

    creates a histogram for ''var'' and weight each event with the inverse of
    its efficiency. The histogram name is fixed as "h_<<var>>_<<nr>>".

    Parameters
    ----------
    var : string
        name of tree-branch to plot
    h_eff : RatioTHnF
        efficency histogram used to look up weights
    select : string
        selection to appy (default: "")
    h_cfg : string
        histogram configuration as used by TTree.Draw()
        ( default: same as h_eff, if same variable
                   40 bins, auto range otherwise)
    tree : TTree
        tree to take events from (default: gTrees[-1])

    Returns
    -------
    the_histo : TH1F
        new histogram-object

    """
    if tree == None:
        tree = gTrees[-1]
    if h_cfg == None:
        if h_eff.var_info == var:
            h_cfg = h_eff.bin_edges_x
        else:
            h_cfg = ( 40, tree.GetMinimum(var), tree.GetMaximum(var) )
    name = _get_unique_hname("h_"+var+"_{0}")
    h = th1f( name, h_cfg )
    h.var_info = var
    put_texts(xlabel=var)
    for evt in tree.CopyTree(select):
        try:

            h.Fill(evt.__getattr__(var), 1./h_eff.get_content(evt) )
        except ZeroDivisionError:
            print "Warning: event with 0 efficiency, skipping!"
    ### ensure canvas after the loop has finished
    cleanup()
    if len(gCanvs) == 0:
        canvas()
    gCanvs[-1].cd()
    do = _prepare_drawopts(1)
    h.Draw(do)
    return h

def save_objects(filename, objects=None, option="recreate"):
    """ save a set of root objects into a file

    saves all objects in the passed list into the given root file.

    Parameters
    ----------
    filename : string
        the filename to use (including extension)
    objects : list or single object
        root objects to save (default: gHistos)
        all objects musts provide a Write() method.
    option : string
        option passed as 2nd argument to the TFile constructor (default: "new")
    """
    if objects == None:
        objects = gHistos
    elif not type(objects) == list:
        objects = [objects]
    outfile = TFile(filename, option)
    assert outfile.IsWritable(), filename+" is not writable"
    for h in objects:
        h.Write()
    outfile.Close()

def exit_handler():
    """ prevent segfault from ROOT when deleting pads """
    cleanup()
    for c in gCanvs:
        c.Close()
    print 'GoodBye!'
atexit.register(exit_handler)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("\nmissing command-line argument, no file loaded!")
        print("use:\n  add_file( '<file>')\n  load( '<tree>' )")
        print("or:\n  create_chain( '<name>', [<files>] )\nto get started.")
    else:
        print
        add_file( sys.argv[1] )

        print("use:\n  load( '<tree>' )\nto load a tree.\n")
        gFiles[-1].ls()
