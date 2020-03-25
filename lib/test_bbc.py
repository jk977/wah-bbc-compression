'''
Unit tests for BBC implementation.
'''

import itertools as it
import unittest as ut

import lib.bbc as bbc

from lib.bitstring import BitString
from lib.bbc import BBC


############################
# wrappers for BBC methods #
############################

def gap_length(index):
    return bbc.gap_length(BitString(index))


def literals_length(index):
    return bbc.literals_length(BitString(index))


def dirty_bit_pos(index):
    tail, encoded = bbc.dirty_bit_pos(BitString(index))
    return str(tail), encoded and str(encoded)


create_atom = bbc.create_atom


def compress(index):
    return str(BBC.compress(index))


class TestBBC(ut.TestCase):
    def test_gap_length(self):
        pass

    def test_literals_length(self):
        pass

    def test_dirty_bit_pos(self):
        pass

    def test_create_atom(self):
        pass

    def test_compress(self):
        pass


if __name__ == '__main__':
    ut.main()
