# pylint: disable-msg=E0611, W0602, W0611, C0103
""" canvashandler.py - wrapper-objects for TCanvas and TPad

This file is part of lookat

Copyright 2013, Nicola Chiapolini, nicola.chiapolini@physik.uzh.ch

License: GNU General Public License version 2,
         or (at your option) any later version.

"""
from ROOT import TCanvas, TPad, TPaveText, TLegend
from ROOT import TH1F, TH2F, TEfficiency, TGraph, TGraphErrors, TGraphAsymmErrors
from ROOT import TMultiGraph
from ROOT import kRed, kGreen, kBlue, kCyan, kMagenta

em = 0.035

def _colorGenerator(i = 0):
    """ generator to create lists of useful root colors
    
    Parameters
    ----------
    i : int
       initial value of internal position-counter

    Returns
    -------
    color : int
       next color from internal list (restarting if necessary)

    
    Examples
    --------
    >>> nextColor = _colorGenerator(1).next
    >>> nextColor()  # kGreen = 416
    416

    >>> [nextColor() for _ in range(3)]  # kBlue = 600, kCyan = 432, kMagenta = 616
    [600, 432, 616]

    """
    base_colors = [kRed, kGreen, kBlue, kCyan, kMagenta]
    N = len(base_colors)
    while True:
        yield base_colors[i%N]
        i+=1


def _expand_multigraphs(in_list):
    while True:
        try:
            idx = map(type, in_list).index(TMultiGraph)
        except ValueError:
            break
        mg = in_list.pop(idx)
        for g in mg.GetListOfGraphs():
            in_list.insert(idx, g)
            idx += 1

_ts_default = [TH1F, TH2F, TGraph, TGraphErrors, TGraphAsymmErrors]
class TextStrategyDefault(object):
    def __init__(self, obj):
        if type(obj) not in _ts_default:
            raise TypeError("bad type passed")
        self._title = obj
        self._x     = obj.GetXaxis()
        self._y     = obj.GetYaxis()

    def set_title(self, title):
        """ update the title """
        self._title.SetTitle(title)

    def set_xlabel(self, xlabel, size):
        """ update the label on the x-axis """
        self._x.SetTitle(xlabel)
        self._x.SetTitleSize( size )

    def set_ylabel(self, ylabel, size):
        """ update the label on the y-axis """
        self._y.SetTitle(ylabel)
        self._y.SetTitleSize( size )

    def set_axes(self, size, ndiv, offset):
        """ rescale the axis labels """
        self._x.SetLabelSize(size)
        self._y.SetLabelSize(size)
        self._y.SetNdivisions( ndiv )
        self._x.SetTitleOffset( offset )
        self._y.SetTitleOffset( offset )

    def set_yrange(self, y_min, y_max):
        """ change the axis range """
        self._y.SetRangeUser(y_min, y_max)

_ts_efficiency = [TEfficiency]
class TextStrategyEfficiency(TextStrategyDefault):
    def __init__(self, obj):
        if type(obj) not in _ts_efficiency:
            raise TypeError("no TEfficiency object passed")
        self._title = obj
        self._x     = obj.GetPaintedGraph().GetXaxis()
        self._y     = obj.GetPaintedGraph().GetYaxis()

_ts_multigraph = [TMultiGraph]
class TextStrategyMultiGraph(TextStrategyDefault):
    def __init__(self, obj):
        if type(obj) not in _ts_multigraph:
            raise TypeError("no TEfficiency object passed")
        self._title = obj.GetHistogram()
        self._x     = obj.GetXaxis()
        self._y     = obj.GetYaxis()

_ts_types = _ts_default+_ts_efficiency+_ts_multigraph


class PadHandler(object):
    """ class to manage an indiviual pad

    simplifies handling of labels, titles and dimensions.

    """

    def __init__(self, name, dim=(0, 0, 1, 1) ):
        """ initialise a new pad

        Parameters
        ----------
        name : string
            name for this pad
        dim : float [0, 1]
            x_min, y_min, x_max, y_max
            coordinates of lower left and upper right corner in
            fraction of canvas size (NDC-coordinates)
            default: (0, 0, 1, 1)

        """
        self._title      = ""
        self._xlabel     = ""
        self._ylabel     = ""
        self._text_strategy = None

        self._pad = TPad(name, name, dim[0], dim[1], dim[2], dim[3], 4000)
        self._pad.Draw()

    def cd(self):
        """ activate this TPad

        """
        self._pad.cd()

    def SetPad(self, dim):
        """ change the dimensions of this pad

        Parameters
        ----------
        dim : float [0, 1]
            x_min, y_min, x_max, y_max
            coordinates of lower left and upper right corner in
            fraction of canvas size (NDC-coordinates)
            default: (0, 0, 1, 1)

        """
        self._pad.SetPad(dim[0], dim[1], dim[2], dim[3])

    def SetLogy(self):
        """ show logarithmic y axis on this TPad

        """
        self._pad.SetLogy()

    def GetName(self):
        """ get the name of this TPad

        """
        return self._pad.GetName()

    def SetGrid(self):
        """ show a grid on this TPad

        """
        self._pad.SetGrid()

    def set_text_strategy(self):
        """ set the text strategy

        Raises
        ------
        StopIteration error, if no suitable object is found

        """
        text_obj = self.get_primitives(_ts_types).next()
        if type(text_obj) == TEfficiency:
            self._text_strategy = TextStrategyEfficiency(text_obj)
        elif type(text_obj) == TMultiGraph:
            self._text_strategy = TextStrategyMultiGraph(text_obj)
        else:
            self._text_strategy = TextStrategyDefault(text_obj)

    def Update(self):
        """ Update this pad

        Makes sure this pad contains a histogram and then calls all relevant
        update funtions.

        """
        self._pad.Update()
        try:
            self.set_text_strategy()
        except StopIteration:
            self._pad.Update()
            return
        self._update_title()
        self._update_xlabel()
        self._update_ylabel()
        self._update_axes()
        self._pad.Update()

    def full_pad(self):
        """ scale this pad to fill the full canvas

        """
        self.cd()
        self._pad.SetPad(0, 0, 1, 1)
        self._pad.SetTopMargin(0.1)
        self._pad.SetRightMargin(0.1)
        self._pad.SetBottomMargin(0.1)
        self._pad.SetLeftMargin(0.1)
        self.Update()

    def hide_pad(self):
        """ hide this pad from the canvas

        We hide pads by placing them outside the visible area

        """
        self._pad.SetPad(0, -0.9, 1, -0.1)

    def _calc_size(self, size):
        """ calculate the size value (in Root fractions)

        Calculates the fraction-size needed to get a given font size on a
        selected pad.

        Parameters
        ----------
        size : float
            font size in units of default font size (em)
        pad : TPad or string
            pad to calculate fraction-size for
            (a string is interpreted as a key in the _pads-dict)

        Returns
        -------
        fraction_size : float
            size value as used by Root functions

        """
        return 1/self._pad.GetHNDC()*em*size

    def set_yrange(self, y_min, y_max):
        """ set the y-range of this pad

        Updates the y-axis of the main histogram on this pad with the given
        y-range.

        Parameters
        ----------
        y_min : float
            min value for the y axis
        y_max : float
            max value for the y axis

        """
        try:
            self.set_text_strategy()
        except StopIteration:
            print "No suitable TextStrategy found"
            return
        self._text_strategy.set_yrange(y_min, y_max)
        self._pad.Update()

    def set_title(self, title):
        """ set the title for this PadHandler

        """
        self._title = title

    @property
    def title(self):
        """ the title stored for this PadHandler

        """
        return self._title

    def set_xlabel(self, xlabel):
        """ set the x-label for this PadHandler

        """
        self._xlabel = xlabel

    @property
    def xlabel(self):
        """ the x-label stored for this PadHandler

        """
        return self._xlabel

    def set_ylabel(self, ylabel):
        """ set the y-label for this PadHandler

        """
        self._ylabel = ylabel

    @property
    def ylabel(self):
        """ the y-label stored for this PadHandler

        """
        return self._ylabel

    def _update_title(self, size=1.5):
        """ update the title on this pad

        updates the title of the first histogram on the TPad with the value
        stored by this PadHandler. Adjusts the font size if needed.

        Parameters
        ----------
        size : float
            font size in units of default font size (em)

        """
        self._text_strategy.set_title(self._title)
        self._pad.Update()
        try:
            text = self.get_primitives(TPaveText).next()
            text.SetY1NDC( text.GetY2NDC() - (1/self._pad.GetHNDC()*em*size ) )
        except StopIteration:
            pass

    def _update_xlabel(self, size=1):
        """ update the label on the x-axis for this pad

        updates the x-label of the first histogram on the TPad with the value
        stored by this PadHandler. Adjusts the font size if needed.

        Parameters
        ----------
        size : float
            font size in units of default font size (em)

        """
        self._text_strategy.set_xlabel(self._xlabel, self._calc_size(size) )

    def _update_ylabel(self, size=1):
        """ update the label on the y-axis for this pad

        updates the y-label of the first histogram on the TPad with the value
        stored by this PadHandler. Adjusts the font size if needed.

        Parameters
        ----------
        size : float
            font size in units of default font size (em)

        """
        self._text_strategy.set_ylabel(self._ylabel, self._calc_size(size) )

    def _update_axes(self):
        """ rescale the axis labels for this pad

        updates the axis from the first histogram on the TPad with reasonable
        values for different layout parameters

        """
        ndiv   =  500+int( 10*self._pad.GetHNDC() )
        size   = self._calc_size(1)
        offset = 1.2*self._pad.GetHNDC()
        self._text_strategy.set_axes( size, ndiv, offset )

    def get_primitives(self, with_type = None):
        """ yield primitives of given type reachable from this pad

        Creates a generator that iterates over the list of primitives from this
        TPad. In each step the next object of given type is returned.

        Parameters
        ----------
        with_type: type
            type of objects to return (default: TH1F)

        Yields
        ------
        the_object : object
            next object with type specified by with_type

        """
        if with_type == None:
            with_type = [TH1F, TH2F]
        elif type(with_type) != list:
            with_type = [with_type]
        try:
            primitives = self._pad.GetListOfPrimitives()
        except ReferenceError:
            raise ReferenceError("No active Pad!")
        for p in primitives:
            if type(p) in with_type:
                yield p

    def has_primitive(self, name):
        """ find primitive with given name

        Checks if a a primitive with the given name exists on this TPad.

        Parameters
        ----------
        name : string
            name of the object to look for

        Returns
        -------
        ret_val : boolean
            True if primitive with given name exists

        """
        try:
            self._pad.GetPrimitive(name).GetName()
            return True
        except ReferenceError or AttributeError:
            return False



class CanvasHandler(object):
    """ class to manage a standard canvas (capable of ratio plots) """

    def __init__(self, name):
        """ initialise a new canvas

        Creates a new canvas with the main pad set to <name>_main

        Parameters
        ----------
        name : string
            name for this canvas (uses auto naming from root if missing)

        """
        self._canv     = None
        self._pads     = {}
        self._text_pad = "main"
        self._texts    = {'title': "", 'xlabel': "", 'ylabel': ""}
        self._em       = 0.035  # factor for default of text size
        self._legend   = None

        if name != "":
            self._canv  = TCanvas( name, name )
        else:
            self._canv  = TCanvas()
        self.add_pad( "main" )

    @property
    def canv(self):
        """ get associated TCanvas """
        return self._canv

    @property
    def pads(self):
        """ get dictionary of all associated PadHandler"""
        return self._pads

    def __repr__(self):
        """ get informativ string representation """
        out_string  = "<CanvasHandler object (\""
        try:
            out_string += self._canv.GetName()
        except AttributeError:
            return "<CanvasHandler object -- empty shell only!>"
        out_string += "\" with {"
        for pad in self._pads.itervalues():
            out_string += pad.GetName()+", "
        return out_string[:-2]+"} )>"

    def add_pad(self, name, x_min = 0, y_min = 0, x_max = 1, y_max = 1):
        """ add a new pad

        Parameters
        ----------
        name : string
            identifier for this pad
        x_min, y_min, x_max, y_max: float [0, 1]
            coordinates of lower left and upper right corner in
            fraction of canvas size (default: 0, 0, 1, 1)

        """
        self._canv.cd()
        pn = self._canv.GetName()+"_"+name
        self._pads[name] = PadHandler( pn, (x_min, y_min, x_max, y_max) )
        self.cd()

    def cd(self):
        """ activate main pad of this canvas

        """
        self._pads["main"].cd()

    def cd_ratio(self):
        """ activate ratio pad of this canvas

        If no ratio pad exists yet, the main pad is resized and a new pad is
        added.

        """
        new_pad = False
        if not self._pads.has_key("ratio"):
            ## setting up a new ratio-pad
            self._pads["main"].SetPad( (0, 0.3, 1, 1 ) )
            self.add_pad("ratio", y_max = 0.3)
            self._pads["ratio"].set_ylabel("ratio")
            new_pad = True
        self.Update()
        self._pads["ratio"].cd()
        return new_pad

    def full_pad(self, name):
        """ scale one pad to fill the full canvas

        Hides all other pads and readjust margins and text size

        Parameters
        ----------
        name : string
            pad to show in full canvas

        """
        pad = self._pads[name]
        pad.full_pad()
        self._text_pad = name
        self._texts['ylabel'] = pad.ylabel
        self.push_texts()
        for p_name, p_obj in self._pads.iteritems():
            if p_name != name:
                p_obj.hide_pad()
        self.Update()

    def push_texts(self):
        """ put texts on this canvas

        set title, x-label and y-label of correct pad to get a good layout

        Parameters
        ----------
        title : strings
            new title for canvas
        xlabel : strings
            new x-label for histograms
        ylabel : strings
            new y-label for histograms

        """
        ## store texts
        self._pads[self._text_pad].set_title(self._texts['title'])
        self._pads[self._text_pad].set_xlabel(self._texts['xlabel'])
        self._pads[self._text_pad].set_ylabel(self._texts['ylabel'])

    def put_texts(self, title=None, xlabel=None, ylabel=None):
        """ put texts on this canvas

        stores title, x-label and y-label and plots them on the proper pads and
        histograms respectively.

        Parameters
        ----------
        title : strings
            new title for canvas
        xlabel : strings
            new x-label for histograms
        ylabel : strings
            new y-label for histograms

        """
        ## store texts
        if title != None:
            self._texts['title']  = title
        if xlabel != None:
            self._texts['xlabel'] = xlabel
        if ylabel != None:
            self._texts['ylabel'] = ylabel
        self.push_texts()
        self.Update()

    @property
    def legend(self):
        """ get legend of this pad

        """
        return self._legend

    def add_legend(self, labels, colors=None, pos=None):
        """ create a legend for this canvas

        Add a legend to the main pad of this canvas, labeling the histograms
        and changing their color if specified. Makes sure ratio plots connected
        with the relevant histograms get updated as well.

        Parameters
        ----------
        labels : list of strings
            labels for the histograms (in same order as they were drawn)
        colors : list of TColors
            line-colors to set for the histograms
        pos : iterable with four float-entries
            postion of the legend, (x_min, y_min, x_max, y_max) in [0, 1]
            ( default: (0.8, 0.8, 1., 1.) )

        Returns
        -------
        the_legend : TLegend
            new legend-object

        """
        if pos == None:
            pos = (0.8, 0.8, 1, 1)
        if colors == None:
            nextColor = _colorGenerator().next
            colors = [nextColor() for _ in range(len(labels))]
        this_legend = TLegend(pos[0], pos[1], pos[2], pos[3])
        this_legend.SetFillColor(0)
        primitives = [p for p in self._pads["main"].get_primitives(_ts_types)]
        _expand_multigraphs(primitives)
        for i, h in enumerate(primitives):
            this_legend.AddEntry(h, labels[i])
            try:
                h.SetStats(False)
            except AttributeError:
                # TEfficiency has no stats
                pass
            try:
                h.SetMarkerColor(colors[i])
                h.SetLineColor(colors[i])
            except IndexError:
                pass
        this_legend.Draw()
        self._pads["main"].Update()
        if self._legend != None:
            self._legend.Delete()
        self._legend = this_legend
        return this_legend

    def SetLogy(self):
        """ use logarithmic y-axis on main pad

        """
        self._pads["main"].SetLogy()

    def GetName(self):
        """ get the name of the canvas from this handler

        """
        return self._canv.GetName()

    def Update(self):
        """ update all pads of this canvas

        """
        for pad in self._pads.itervalues():
            pad.Update()

    def SaveAs(self, filename):
        """ save this canvas to a file

        Parameters
        ----------
        filename : string
            if the filename includes an extension (the last 4 characters
            contain a '.'), the given file will be created.
            Otherwise the canvas will be saved as PDF and CXX, adding the
            correct extension to filename.

        """
        if filename[-4:].find('.') != -1:
            self._canv.SaveAs( filename )
        else:
            self._canv.SaveAs( filename+".pdf" )
            self._canv.SaveAs( filename+".cxx" )

    def Close(self):
        """ Close the canvas from this handler

        """
        try:
            self._canv.Close()
        except AttributeError:
            pass

