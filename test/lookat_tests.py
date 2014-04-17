# -*- coding: utf-8 -*-
"""
Tests for lookat.py

to run:
  1) enter test directory
  2) add directory with lookat.py to path (use setup.sh)
  3) run ''nosetests''

"""
from nose.tools import assert_equal, assert_less, assert_raises
from lookat import *

def test_globallists():
    assert_equal(type(gFiles), list)
    assert_equal( len(gFiles), 0)
    assert_equal(type(gTrees), list)
    assert_equal( len(gTrees), 0)
    assert_equal(type(gCanvs), list)
    assert_equal( len(gCanvs), 0)
    assert_equal(type(gHistos), list)
    assert_equal( len(gHistos), 0)

def test_addfile():
    """ add the file with test data """
    add_file('test_input.root')
    assert_equal(len(gFiles), 1)
    assert_equal(type(gFiles[-1]), TFile)

def test_load():
    """ load the tree in the file """
    load('advanced_tree')
    assert_equal(len(gTrees), 1)
    assert_equal(type(gTrees[-1]), TTree)
    assert_equal(gTrees[-1].GetName(), "advanced_tree")

def test_createchain():
    """ load the test data into a chain """
    create_chain('simple_tree', ['test_input.root'])
    assert_equal(len(gFiles), 1)
    assert_equal(len(gTrees), 2)
    assert_equal(type(gTrees[-1]), TChain)
    assert_equal(gTrees[-1].GetName(), "simple_tree")

def test_getbranchlist():
    """ check the content of the last tree """
    assert_equal( ['int_leaf', 'double_leaf'], get_branch_list() )

def test_draw():
    """ create a simple plot

    This creates a new canvas, root improves the binning and ignores the
    default value.

    """
    draw('int_leaf')
    assert_equal(len(gCanvs), 1)
    assert_equal(len(gHistos), 1)
    assert_equal(gHistos[-1].GetName(), "myHist_0")
    assert_less(gHistos[-1].GetNbinsX(), 40)
    for i in range(1,11):
        assert_equal(gHistos[-1].GetBinContent(i), 20)
    ### add a second histogram in same binning
    draw('double_leaf*5')
    assert_equal(len(gCanvs), 1)
    assert_equal(len(gHistos), 2)

def test_drawratio():
    draw_ratio()
    assert_equal(type(gHistos[-1]), RatioTHnF)
    assert_equal(gHistos[-1]._ratio.GetBinContent(1), 2.0)
    assert_equal(gHistos[-1]._ratio.GetBinContent(5), 2.0)
    assert_equal(gHistos[-1]._ratio.GetBinContent(6), 0.0)

def test_createweightstring():
    w_str = create_weight_string(gHistos[-1].ratio_thnf)
    assert_equal(w_str, "(2.000*(0.00 <= double_leaf*5 && double_leaf*5 < 1.00)+2.000*(1.00 <= double_leaf*5 && double_leaf*5 < 2.00)+2.000*(2.00 <= double_leaf*5 && double_leaf*5 < 3.00)+2.000*(3.00 <= double_leaf*5 && double_leaf*5 < 4.00)+2.000*(4.00 <= double_leaf*5 && double_leaf*5 < 5.00)+0.000*(5.00 <= double_leaf*5 && double_leaf*5 < 6.00)+0.000*(6.00 <= double_leaf*5 && double_leaf*5 < 7.00)+0.000*(7.00 <= double_leaf*5 && double_leaf*5 < 8.00)+0.000*(8.00 <= double_leaf*5 && double_leaf*5 < 9.00)+0.000*(9.00 <= double_leaf*5 && double_leaf*5 < 10.00)+0.000*(10.00 <= double_leaf*5 && double_leaf*5 < 11.00))")

def test_cleanup():
    """ make sure global lists get cleaned properly """
    ### make sure nothing gets cleaned
    cleanup(True)
    assert_equal(len(gCanvs), 1)
    assert_equal(len(gHistos), 3)
    ### now simulate closing of canvas
    gCanvs[-1].Close()
    gCanvs[-1]._canv = None
    assert_equal(str(gCanvs[-1]), "<CanvasHandler object -- empty shell only!>")
    # and check garbage collection again
    cleanup()
    assert_equal(len(gCanvs), 0)
    assert_equal(len(gHistos), 3)
    cleanup(True)
    assert_equal(len(gCanvs), 0)
    assert_equal(len(gHistos), 0)

def test_badhistogram():
    """ create a null-pointer histogram and clean it again """
    # redirect the error message from ROOT to /dev/null
    import os, sys
    old_stderr = os.dup( sys.stderr.fileno() )
    devnull    = file( "/dev/null", "w" )
    os.dup2( devnull.fileno(), sys.stderr.fileno() )
    # try to create histogram from in-existant variable
    draw( "hello" )
    # resotre file stderr
    os.dup2( old_stderr, sys.stderr.fileno() )
    devnull.close()
    # check for new histogram and remove it
    assert_equal(len(gHistos), 1)
    cleanup(True)
    assert_equal(len(gHistos), 0)
    # clean up canvas created by draw
    gCanvs[-1].Close()
    gCanvs[-1]._canv = None
    cleanup()

def test_canvas():
    """ create a new canvas for the next tests """
    canvas()
    assert_equal(len(gCanvs), 1)
    assert_equal(str(gCanvs[0]), '<CanvasHandler object ("c1" with {c1_main} )>')

def test_draw_selected():
    """ draw only selected events, check h_cfg """
    draw('int_leaf', 'double_leaf < 0.5 || double_leaf > 0.8', h_cfg="(4,0,8)")
    assert_equal(len(gHistos), 1)
    assert_equal(gHistos[-1].GetName(), "myHist_0")
    assert_equal(gHistos[-1].GetBinContent(0),  0) # underflow bin
    assert_equal(gHistos[-1].GetBinContent(1), 40) # [0, 2)
    assert_equal(gHistos[-1].GetBinContent(2), 40) # [2, 4)
    assert_equal(gHistos[-1].GetBinContent(3), 20) # [4, 6)
    assert_equal(gHistos[-1].GetBinContent(4),  0) # [6, 8)
    assert_equal(gHistos[-1].GetBinContent(5), 20) # overflow bin

def test_canvas_name():
    """ create a new canvas for the next tests with a special name """
    canvas("gauss_canvas")
    assert_equal(len(gCanvs), 2)
    assert_equal(gCanvs[-1].GetName(), "gauss_canvas")

def test_th1f():
    """ create a predefined histogram """
    th1f("gauss_hist", (20, -4, 4) )
    assert_equal(len(gCanvs), 2)
    assert_equal(len(gHistos), 2)
    assert_equal(gHistos[-1].GetNbinsX(), 20)
    assert_equal(gHistos[-1].GetName(), "gauss_hist")

def test_draw_tree():
    """ fill the predefined histogram with events from a non standard tree """
    draw('gauss_leaf', 'nr_leaf % 2 == 0', h_name="+gauss_hist", tree=gTrees[0])
    assert_equal(gHistos[-1].GetName(), "gauss_hist")
    assert_equal(gHistos[-1].GetEntries(), 50000)
    assert_equal(gHistos[-1].GetNbinsX(), 20)

def test_draw_append():
    """ append events to existing histogram """
    draw('gauss_leaf', 'nr_leaf % 2 == 0', h_name="+gauss_hist", tree=gTrees[0])
    assert_equal(gHistos[-1].GetName(), "gauss_hist")
    assert_equal(gHistos[-1].GetEntries(), 100000)
    assert_equal(gHistos[-1].GetNbinsX(), 20)

def test_draw_replace():
    """ replace predefined histogram """
    draw('gauss_leaf', h_name="gauss_hist", tree=gTrees[0])
    assert_equal(gHistos[-1].GetName(), "gauss_hist")
    assert_equal(gHistos[-1].GetEntries(), 100000)
    assert_equal(gHistos[-1].GetNbinsX(), 40)

def test_legend():
    """ add a legend; change line color of last histogram to red """
    from ROOT import TLegend
    l = legend( ["my gauss"], [kRed] )
    assert_equal(type(l), TLegend)
    assert_equal(l, get_legend())
    assert_equal(gHistos[-1].GetLineColor(), kRed)

def test_puttexts():
    """ put title and axis labels """
    put_texts("Test Gauss", "x-axis", "y-axis")
    assert_equal(gHistos[-1].GetTitle(), "Test Gauss")
    assert_equal(gHistos[-1].GetXaxis().GetTitle(), "x-axis")
    assert_equal(gHistos[-1].GetYaxis().GetTitle(), "y-axis")

