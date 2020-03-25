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

def _gap_length(index):
    return bbc.gap_length(BitString(index))


def _literals_length(index):
    return bbc.literals_length(BitString(index))


def _dirty_bit_pos(index):
    return bbc.dirty_bit_pos(BitString(index))


def _create_atom(gap_count, is_dirty, special, literal=None):
    return str(bbc.create_atom(gap_count, is_dirty, special, literal))


def _compress(index):
    return str(BBC.compress(index))


##############
# unit tests #
##############

class TestBBC(ut.TestCase):
    def test_gap_length(self):
        gap_max: Final = all_bits(15)

        for i in range(gap_max + 1):
            # test within the max length
            self.assertEqual(_gap_length('00000000' * i), i)

        for i in range(1, 11):
            # test over the max length
            n = gap_max + i
            self.assertEqual(_gap_length('00000000' * n), gap_max)

    def test_literals_length(self):
        # test the empty string
        self.assertEqual(_literals_length(''), 0)

        # test strings without literals
        for i in range(8, 100):
            self.assertEqual(_literals_length('0' * i), 0)

        literals: Final = ['00000011', '10000001', '10001001',
                           '10011001', '11111111', '11111111']

        for literal in literals:
            # test single-byte literals
            self.assertEqual(_literals_length(literal), 1)

            # test multi-byte literals under the literal limit
            for i in range(1, 16):
                offsets = '00100000' * (i - 1)
                self.assertEqual(_literals_length(offsets), i - 1)
                self.assertEqual(_literals_length(literal + offsets), i)
                self.assertEqual(_literals_length(offsets + literal), i)

                self.assertEqual(_literals_length(literal * i), i)

            # test multi-byte literals over the literal limit
            for i in range(16, 100):
                offsets = '00100000' * i
                self.assertEqual(_literals_length(offsets), 15)
                self.assertEqual(_literals_length(literal + offsets), 15)
                self.assertEqual(_literals_length(offsets + literal), 15)

                self.assertEqual(_literals_length(literal * i), 15)

    def test_dirty_bit_pos(self):
        # test all possible bytes
        for bits in it.product(*it.repeat(['0', '1'], 8)):
            byte = ''.join(bits)

            if byte.count('1') == 1:
                # offset byte found
                self.assertEqual(_dirty_bit_pos(byte), byte.find('1'))
            else:
                # non-offset byte found
                self.assertEqual(_dirty_bit_pos(byte), -1)

    def test_create_atom(self):
        # empty bitstring
        e = BitString()

        # test single-byte atom gap length
        self.assertEqual(_create_atom(0b000, False, 0, e), '00000000')
        self.assertEqual(_create_atom(0b001, False, 0, e), '00100000')
        self.assertEqual(_create_atom(0b010, False, 0, e), '01000000')
        self.assertEqual(_create_atom(0b011, False, 0, e), '01100000')
        self.assertEqual(_create_atom(0b100, False, 0, e), '10000000')
        self.assertEqual(_create_atom(0b101, False, 0, e), '10100000')
        self.assertEqual(_create_atom(0b110, False, 0, e), '11000000')

        # test two-byte atom gap length
        self.assertEqual(_create_atom(0b111, False, 0, e),
                         '11100000' + '00000111')
        self.assertEqual(_create_atom(0b1000, False, 0, e),
                         '11100000' + '00001000')
        self.assertEqual(_create_atom(0b1001, False, 0, e),
                         '11100000' + '00001001')
        self.assertEqual(_create_atom(0b1111111, False, 0, e),
                         '11100000' + '01111111')

        # test three-byte atom gap length
        self.assertEqual(_create_atom(0b10000000, False, 0, e),
                         '11100000' + '10000000' + '10000000')
        self.assertEqual(_create_atom(all_bits(15), False, 0, e),
                         '11100000' + '11111111' + '11111111')

        # test dirty bit flag
        self.assertEqual(_create_atom(0b000, True, 0), '00010000')

    def test_compress(self):
        # test 1-byte gaps
        for gaps in range(1, all_bits(3)):
            gap_prefix: Final = '{:03b}'.format(gaps)

            # only gap
            self.assertEqual(_compress('00000000' * gaps),
                             gap_prefix + '00000')

            # gap with offset byte
            bits = '00000000' * gaps + '01000000'
            expected = gap_prefix + '10001'
            self.assertEqual(_compress(bits), expected)

            # gap with literals
            bits = '00000000' * gaps + '11100000' + '00000111'
            expected = gap_prefix + '00010' + '11100000' + '00000111'
            self.assertEqual(_compress(bits), expected)

            # gap with offset byte, then literals
            bits = '00000000' * gaps + '00000001' + '11100000' + '00000111'
            expected = gap_prefix + '10111' \
                + '00000010' + '11100000' + '00000111'
            self.assertEqual(_compress(bits), expected)

            # gap with literals, then offset byte
            bits = '00000000' * gaps + '11100000' + '00000111' + '01000000'
            expected = gap_prefix + '00011' \
                + '11100000' + '00000111' + '01000000'
            self.assertEqual(_compress(bits), expected)

        # test 2-byte gaps
        for gaps in range(all_bits(3), all_bits(7) + 1):
            gap_bin: Final = '0{:07b}'.format(gaps)

            # only gap
            self.assertEqual(_compress('00000000' * gaps),
                             '11100000' + gap_bin)

            # gap with offset byte
            bits = '00000000' * gaps + '00100000'
            expected = '11110010' + gap_bin
            self.assertEqual(_compress(bits), expected)

            # gap with literals
            bits = '00000000' * gaps + '10010010' + '01001001'
            expected = '11100010' + gap_bin + '10010010' + '01001001'
            self.assertEqual(_compress(bits), expected)

            # gap with offset byte, then literals
            bits = '00000000' * gaps + '10000000' + '10010010' + '01001001'
            expected = '11110000' + gap_bin \
                + '00000010' + '10010010' + '01001001'
            self.assertEqual(_compress(bits), expected)

            # gap with literals, then offset byte
            bits = '00000000' * gaps + '10010010' + '01001001' + '10000000'
            expected = '11100011' + gap_bin \
                + '10010010' + '01001001' + '10000000'
            self.assertEqual(_compress(bits), expected)

        # test large gap
        bits = '00000000' * 510
        expected = '11100000' + '10000001' + '11111110'
        self.assertEqual(_compress(bits), expected)


if __name__ == '__main__':
    ut.main()
