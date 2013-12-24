# coding: utf-8

from numpy import zeros
from scipy.stats import norm
from ROOT import TFile
from ROOT import TTree
file = TFile( 'test_input.root', 'recreate' )
s_tree = TTree("simple_tree", "simple tree for testing purposes")
i_arg = zeros(1, dtype=int)
d_arg = zeros(1, dtype=float)
s_tree.Branch('int_leaf', i_arg, 'int_leaf/I')
s_tree.Branch('double_leaf', d_arg, 'double_leaf/D')
for i in range(10):
    for _ in range(20):
        i_arg[0] = i
        d_arg[0] = 0.1*i
        s_tree.Fill()

a_tree = TTree("advanced_tree", "tree proper variables for testing purposes")
nr_arg    = zeros(1, dtype=int)
gauss_arg = zeros(1, dtype=float)
a_tree.Branch('nr_leaf', i_arg, 'nr_leaf/I')
a_tree.Branch('gauss_leaf', d_arg, 'gauss_leaf/D')
vals = norm().rvs( size = 100000 )
for i, v in enumerate(vals):
    i_arg[0] = i
    d_arg[0] = v
    a_tree.Fill()
file.Write()
file.Close()

