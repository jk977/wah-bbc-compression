'''
Unit tests for BBC implementation.
'''

import itertools as it
import unittest as ut

from typing import Final

import lib.bbc as bbc

from lib.bbc import BBC
from lib.util import all_bits, binstr


bits_per_byte: Final = 8
gap_max: Final = all_bits(15)       # max number of gaps in atom
lit_max: Final = 0b1111             # max number of literals in atom


##############
# unit tests #
##############

class TestBBC(ut.TestCase):
    def test_gap_length(self):
        '''
        Test ``bbc.gap_length()`` with gaps that fit into one atom.
        '''

        for i in range(gap_max + 1):
            self.assertEqual(bbc.gap_length('00000000' * i), i)

    def test_gap_length_overflow(self):
        '''
        Test ``bbc.gap_length()`` with gaps that do not fit into one atom.
        '''

        for i in range(1, 11):
            n = gap_max + i
            self.assertEqual(bbc.gap_length('00000000' * n), gap_max)

    def test_get_literals_none(self):
        '''
        Test ``bbc.get_literals()`` with non-literal inputs.
        '''

        self.assertEqual(bbc.get_literals(''), ('', ''))

        for i in range(8, 100):
            bits = '0' * i
            self.assertEqual(bbc.get_literals(bits), (bits, ''))

    def test_get_literals_single(self):
        '''
        Test ``bbc.get_literals()`` with single-byte literals.
        '''

        literals: Final = ['00000011', '10000001', '10001001',
                           '10011001', '11111111', '11111111']

        for literal in literals:
            self.assertEqual(bbc.get_literals(literal), ('', literal))

    def test_get_literals_multi(self):
        '''
        Test ``bbc.get_literals()`` with multi-byte literals that fit into
        one atom.
        '''

        literals: Final = ['00000011', '10000001', '10001001',
                           '10011001', '11111111', '11111111']

        for literal in literals:
            for i in range(1, lit_max + 1):
                offsets = '00100000' * (i - 1)
                self.assertEqual(bbc.get_literals(offsets), ('', offsets))
                self.assertEqual(bbc.get_literals(literal + offsets),
                                 ('', literal + offsets))
                self.assertEqual(bbc.get_literals(offsets + literal),
                                 ('', offsets + literal))

                self.assertEqual(bbc.get_literals(literal * i),
                                 ('', literal * i))

    def test_get_literals_overflow(self):
        '''
        Test ``bbc.get_literals()`` with multi-byte literals that do not fit
        into one atom.
        '''

        lit_max_bits: Final = lit_max * bits_per_byte
        literals: Final = ['00000011', '10000001', '10001001',
                           '10011001', '11111111', '11111111']

        for literal in literals:
            for i in range(lit_max + 1, 100):
                offsets = '00100000' * i
                tests = [offsets, literal + offsets, offsets + literal,
                         literal * i, offsets * i]

                for bits in tests:
                    tail, lits = bbc.get_literals(bits)
                    self.assertEqual(lits, bits[:lit_max_bits])
                    self.assertEqual(tail, bits[lit_max_bits:])

    def test_dirty_bit_pos(self):
        '''
        Test ``bbc.dirty_bit_pos()`` against all possible bytes.
        '''

        for bits in it.product(*it.repeat(['0', '1'], 8)):
            byte = ''.join(bits)

            if byte.count('1') == 1:
                # offset byte found
                self.assertEqual(bbc.dirty_bit_pos(byte), byte.find('1'))
            else:
                # non-offset byte found
                self.assertEqual(bbc.dirty_bit_pos(byte), -1)

    def test_create_atom_short(self):
        '''
        Test ``bbc.create_atom()`` with gaps that can be encoded in the header.
        '''

        self.assertEqual(bbc.create_atom(0b000, False, 0, ''), '00000000')
        self.assertEqual(bbc.create_atom(0b001, False, 0, ''), '00100000')
        self.assertEqual(bbc.create_atom(0b010, False, 0, ''), '01000000')
        self.assertEqual(bbc.create_atom(0b011, False, 0, ''), '01100000')
        self.assertEqual(bbc.create_atom(0b100, False, 0, ''), '10000000')
        self.assertEqual(bbc.create_atom(0b101, False, 0, ''), '10100000')
        self.assertEqual(bbc.create_atom(0b110, False, 0, ''), '11000000')

    def test_create_atom_mid(self):
        '''
        Test ``bbc.create_atom()`` with gaps that can be encoded in one byte
        after the header.
        '''

        self.assertEqual(bbc.create_atom(0b111, False, 0, ''),
                         '11100000' '00000111')
        self.assertEqual(bbc.create_atom(0b1000, False, 0, ''),
                         '11100000' '00001000')
        self.assertEqual(bbc.create_atom(0b1001, False, 0, ''),
                         '11100000' '00001001')
        self.assertEqual(bbc.create_atom(0b1111111, False, 0, ''),
                         '11100000' '01111111')

    def test_create_atom_long(self):
        '''
        Test ``bbc.create_atom()`` with gaps that can be encoded in two bytes
        after the header.
        '''

        self.assertEqual(bbc.create_atom(0b10000000, False, 0, ''),
                         '11100000' '10000000' '10000000')
        self.assertEqual(bbc.create_atom(all_bits(15), False, 0, ''),
                         '11100000' '11111111' '11111111')

    def test_create_atom_dirty(self):
        '''
        Test ``bbc.create_atom()`` with offset bytes.
        '''

        self.assertEqual(bbc.create_atom(0b000, True, 0b0000), '00010000')
        self.assertEqual(bbc.create_atom(0b001, True, 0b0001), '00110001')

        self.assertEqual(bbc.create_atom(0b111, True, 0b1000),
                         '11111000' '00000111')

        self.assertEqual(bbc.create_atom(0b10000000, True, 0b1010),
                         '11111010' '10000000' '10000000')

    def test_create_atom_lits(self):
        '''
        Test ``bbc.create_atom()`` with literal bytes.
        '''

        lits = '11010110' '00101101' '01011100'

        self.assertEqual(bbc.create_atom(0b000, False, 3, lits),
                         '00000011' + lits)

        lits = lits[bits_per_byte:]
        self.assertEqual(bbc.create_atom(0b1111, False, 2, lits),
                         '11100010' '00001111' + lits)

        lits = lits[bits_per_byte:]
        self.assertEqual(bbc.create_atom(all_bits(15), False, 1, lits),
                         '11100001' '11111111' '11111111' + lits)

    def test_compress_short(self):
        '''
        Test ``BBC.compress()`` using bytes with gaps that can be encoded in
        the header.
        '''

        for gaps in range(1, all_bits(3)):
            gap_prefix: Final = binstr(gaps, 3)

            # only gap
            self.assertEqual(BBC.compress('00000000' * gaps),
                             gap_prefix + '00000')

            # gap with offset byte
            bits = '00000000' * gaps + '01000000'
            expected = gap_prefix + '10001'
            self.assertEqual(BBC.compress(bits), expected)

            # gap with literals
            bits = '00000000' * gaps + '11100000' '00000111'
            expected = gap_prefix + '00010' '11100000' '00000111'
            self.assertEqual(BBC.compress(bits), expected)

            # gap with offset byte, then literals
            bits = '00000000' * gaps + '00000001' '11100000' '00000111'
            expected = gap_prefix + '00011' \
                + '00000001' '11100000' '00000111'
            self.assertEqual(BBC.compress(bits), expected)

            # gap with literals, then offset byte
            bits = '00000000' * gaps + '11100000' '00000111' '01000000'
            expected = gap_prefix + '00011' \
                + '11100000' '00000111' '01000000'
            self.assertEqual(BBC.compress(bits), expected)

    def test_compress_mid(self):
        '''
        Test ``BBC.compress()`` using bytes with gaps that can be encoded in
        one byte after the header.
        '''

        for gaps in range(all_bits(3), all_bits(7) + 1):
            gap_bin: Final = '0' + binstr(gaps, 7)

            # only gap
            self.assertEqual(BBC.compress('00000000' * gaps),
                             '11100000' + gap_bin)

            # gap with offset byte
            bits = '00000000' * gaps + '00100000'
            expected = '11110010' + gap_bin
            self.assertEqual(BBC.compress(bits), expected)

            # gap with literals
            bits = '00000000' * gaps + '10010010' '01001001'
            expected = '11100010' + gap_bin + '10010010' '01001001'
            self.assertEqual(BBC.compress(bits), expected)

            # gap with offset byte, then literals
            bits = '00000000' * gaps + '10000000' '10010010' '01001001'
            expected = '11100011' + gap_bin \
                + '10000000' '10010010' '01001001'
            self.assertEqual(BBC.compress(bits), expected)

            # gap with literals, then offset byte
            bits = '00000000' * gaps + '10010010' '01001001' '10000000'
            expected = '11100011' + gap_bin \
                + '10010010' '01001001' '10000000'
            self.assertEqual(BBC.compress(bits), expected)

    def test_compress_long(self):
        '''
        Test ``BBC.compress()`` using bytes with gaps that can be encoded in
        two bytes after the header.
        '''

        bits = '00000000' * 510
        expected = '11100000' '10000001' '11111110'
        self.assertEqual(BBC.compress(bits), expected)


if __name__ == '__main__':
    ut.main()
