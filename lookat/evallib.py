# pylint: disable-msg=E0611, W0611, W0613
""" evallib.py - helper functions to process TFormulas with pythons eval() function

This file is part of lookat

Copyright 2013, Nicola Chiapolini, nicola.chiapolini@physik.uzh.ch

License: GNU General Public License version 2,
         or (at your option) any later version.

"""
from ROOT import TH1F, TH2F, TMath
gImports = []

def add_tmath(names):
    """ add a TMath function to the list of functions loaded before evaluating

    When ROOT evaluates TFormulas, i.e. in TTree.Draw(), the names from TMath
    are available. To use python's eval() instead, these names must be imported
    into python.

    Parameters
    ----------
    names : string or list of strings
        names to bring from TMath into python

    """
    if type(names) == list:
        gImports.extend( names )
    else:
        gImports.append( names )

def get_1d(hist, val_str, evt):
    """ get content of bin containing the passed event

    helper function for 1d histograms

    Parameters
    ----------
    hist : TH1F
        histogram from which to get the content
    val_str : string
        string describing variable filled into hist
        branches need to be written as evt.<<branch_name>>
    evt : TTree entry
        event to find bin for

    Returns
    -------
    ret_val : double
        content into which evt would fall

    """
    return hist.GetBinContent(
               hist.FindFixBin( eval(val_str) )
           )

def get_2d(hist, val_str, evt):
    """ get content of bin containing the passed event

    helper function for 2d histograms

    Parameters
    ----------
    hist : TH1F
        histogram from which to get the content
    val_str : string
        string describing variable filled into hist
        branches need to be written as evt.<<branch_name>>
        ATTENTION: the order for 2d histograms is y_values:x_values!
    evt : TTree entry
        event to find bin for

    Returns
    -------
    ret_val : double
        content into which evt would fall

    """
    val_y, val_x = val_str.split(':')
    return hist.GetBinContent(  hist.FindFixBin(
                eval(val_x),
                eval(val_y)
           ) )

def prepare_eval(var_str, tree, prefix="evt."):
    """ translate a ROOT TFormula into an pyzthon eval() expression

    Prepends all branch names in ''var_str'' with ''prefix'', i.e. turning
    particle_pt into evt.particle_pt by default.

    Parameters
    ----------
    var_str : string (TFormula)
        string of variable filled into hist (unchanged)
    tree : TTree
        used to get list of all branch-names
    prefix : string
        prefix for branch-names, i.e. loop-variable (default: 'evt.')

    Returns
    -------
    val_str : string
        string describing variable defined by var_str

    """
    branches = [b.GetName() for b in tree.GetListOfBranches()]
    var_parts = var_str.split(":")
    ret_val = []
    for part in var_parts:
        part = "1*"+part
        for branch in branches:
            part = part.replace(branch, "$"+branch)
        part_list = part.split("$")
        try:
            while True:
                part_list.remove('')
        except ValueError:
            pass
        ret_val.append(prefix.join(part_list).lstrip("1*"))
    return ":".join(ret_val)

def fill_corr_eval(h_out, var, h_eff, eff_var, tree, select=""):
    """ fill events from ''tree'' into ''h_out'' weighted by ''h_eff''

    fill ''var'' into the histogram ''h_out'' and weight each event with the
    inverse of its efficiency given in ''h_eff''.

    Parameters
    ----------
    h_out : TH1F
        histogram to fill
    var : string (TFormula)
        variable to fill into h_out
    h_eff : TH1F or TH2F
        efficency histogram used to look up weights
    eff_var : string (TFromula)
        variable(s) used in h_eff
    tree : TTree
        tree to take events from
    select : string
        selection to appy (default: "")

    """
    for imp in gImports:
        globals()[imp] = eval("TMath."+imp)
    h_type = type(h_eff)
    if h_type == TH1F:
        get = get_1d
    elif h_type == TH2F:
        get = get_2d
    else:
        raise NotImplementedError(
          "type off h_eff ("+str(h_type)+") not supported")
    eval_var = prepare_eval(var, tree)
    eval_eff = prepare_eval(eff_var, tree)
    h_out.var_info = var
    for evt in tree.CopyTree(select):
        eff = get(h_eff, eval_eff, evt)
        h_out.Fill(eval(eval_var), 1./eff )

