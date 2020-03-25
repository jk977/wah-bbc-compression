'''
Unit tests for BBC implementation.
'''

import itertools as it
import unittest as ut

import lib.bbc as bbc

from lib.bitstring import BitString
from lib.bbc import BBC
from lib.util import all_bits


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
        gap_max: Final = all_bits(15)

        for i in range(gap_max + 1):
            # test within the max length
            self.assertEqual(gap_length('00000000' * i), i)

        for i in range(1, 11):
            # test over the max length
            n = gap_max + i
            self.assertEqual(gap_length('00000000' * n), gap_max)

    def test_literals_length(self):
        for i in range(100):
            # test strings without literals
            zeroes = '0' * i
            ones = '1' * i
            offs = ('00100000' + '00000100') * i

            self.assertEqual(literals_length(zeroes), 0)
            self.assertEqual(literals_length(ones), 0)
            self.assertEqual(literals_length(offs), 0)

        a = '00000011'
        b = '10000001'
        c = '10001001'
        d = '10011001'
        e = '11111111'

        for literal in a, b, c, d, e:
            # test single-byte literals
            self.assertEqual(literals_length(literal), 1)

        for literal in a, b, c, d, e:
            for i in range(100):
                # test multi-byte literals
                self.assertEqual(literals_length(literal * i), i)

    def test_dirty_bit_pos(self):
        pass

    def test_create_atom(self):
        pass

    def test_compress(self):
        pass


if __name__ == '__main__':
    ut.main()
