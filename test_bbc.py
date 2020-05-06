'''
Unit tests for BBC implementation.
'''

import itertools as it
import unittest as ut

from bitstring import BitArray

import lib.bbc as bbc

from lib.util import all_bits, binstr


bits_per_byte = 8
gap_max = all_bits(15)       # max number of gaps in atom
lit_max = all_bits(4)        # max number of literals in atom


##############
# unit tests #
##############

class TestBBC(ut.TestCase):
    def test_get_gaps(self):
        '''
        Test ``bbc.get_gaps()`` with gaps that fit into one atom.
        '''

        for i in range(gap_max + 1):
            bs = BitArray(bin='00000000' * i)
            self.assertEqual(bbc.get_gaps(bs), (BitArray(), i))

    def test_gap_length_overflow(self):
        '''
        Test ``bbc.get_gaps()`` with gaps that do not fit into one atom.
        '''

        for i in range(1, 11):
            n = gap_max + i
            bs = BitArray(bin='00000000' * n)
            expected = BitArray(bin='00000000' * i)
            self.assertEqual(bbc.get_gaps(bs), (expected, gap_max))

    def test_get_literals_none(self):
        '''
        Test ``bbc.get_literals()`` with non-literal inputs.
        '''

        self.assertEqual(bbc.get_literals(BitArray()),
                         (BitArray(), BitArray()))

        for i in range(8, 100):
            bits = BitArray(bin='0' * i)
            self.assertEqual(bbc.get_literals(bits), (bits, BitArray()))

    def test_get_literals_single(self):
        '''
        Test ``bbc.get_literals()`` with single-byte literals.
        '''

        literals = ['00000011', '10000001', '10001001',
                    '10011001', '11111111', '11111111']

        for literal in literals:
            lit_bs = BitArray(bin=literal)
            self.assertEqual(bbc.get_literals(lit_bs), (BitArray(), lit_bs))

    def test_get_literals_multi(self):
        '''
        Test ``bbc.get_literals()`` with multi-byte literals that fit into
        one atom.
        '''

        literals = ['00000011', '10000001', '10001001',
                    '10011001', '11111111', '11111111']

        for literal in literals:
            lit_bs = BitArray(bin=literal)

            for i in range(1, lit_max + 1):
                offsets = BitArray(bin='00100000' * (i - 1))

                self.assertEqual(bbc.get_literals(offsets),
                                 (BitArray(), offsets))
                self.assertEqual(bbc.get_literals(lit_bs + offsets),
                                 (BitArray(), lit_bs + offsets))
                self.assertEqual(bbc.get_literals(offsets + lit_bs),
                                 (BitArray(), offsets + lit_bs))
                self.assertEqual(bbc.get_literals(lit_bs * i),
                                 (BitArray(), lit_bs * i))

    def test_get_literals_overflow(self):
        '''
        Test ``bbc.get_literals()`` with multi-byte literals that do not fit
        into one atom.
        '''

        lit_max_bits = lit_max * bits_per_byte
        literals = ['00000011', '10000001', '10001001',
                    '10011001', '11111111', '11111111']

        for literal in literals:
            lit_bs = BitArray(bin=literal)

            for i in range(lit_max + 1, 100):
                offsets = BitArray(bin='00100000' * i)
                tests = [offsets, lit_bs + offsets, offsets + lit_bs,
                         lit_bs * i, offsets * i]

                for bs in tests:
                    tail, lits = bbc.get_literals(bs)
                    self.assertEqual(lits, bs[:lit_max_bits])
                    self.assertEqual(tail, bs[lit_max_bits:])

    def test_dirty_bit_pos(self):
        '''
        Test ``bbc.dirty_bit_pos()`` against all possible bytes.
        '''

        for bits in it.product(*it.repeat(['0', '1'], 8)):
            byte = BitArray(bin=''.join(bits))

            if byte.count(1) == 1:
                # offset byte found
                self.assertEqual(bbc.dirty_bit_pos(byte), byte.find('0b1')[0])
            else:
                # non-offset byte found
                self.assertEqual(bbc.dirty_bit_pos(byte), -1)

    def test_create_atom_short(self):
        '''
        Test ``bbc.create_atom()`` with gaps that can be encoded in the header.
        '''

        self.assertEqual(bbc.create_atom(0b000, False, 0, BitArray()),
                         BitArray(bin='00000000'))
        self.assertEqual(bbc.create_atom(0b001, False, 0, BitArray()),
                         BitArray(bin='00100000'))
        self.assertEqual(bbc.create_atom(0b010, False, 0, BitArray()),
                         BitArray(bin='01000000'))
        self.assertEqual(bbc.create_atom(0b011, False, 0, BitArray()),
                         BitArray(bin='01100000'))
        self.assertEqual(bbc.create_atom(0b100, False, 0, BitArray()),
                         BitArray(bin='10000000'))
        self.assertEqual(bbc.create_atom(0b101, False, 0, BitArray()),
                         BitArray(bin='10100000'))
        self.assertEqual(bbc.create_atom(0b110, False, 0, BitArray()),
                         BitArray(bin='11000000'))

    def test_create_atom_mid(self):
        '''
        Test ``bbc.create_atom()`` with gaps that can be encoded in one byte
        after the header.
        '''

        self.assertEqual(bbc.create_atom(0b111, False, 0, BitArray()),
                         BitArray(bin='11100000' '00000111'))
        self.assertEqual(bbc.create_atom(0b1000, False, 0, BitArray()),
                         BitArray(bin='11100000' '00001000'))
        self.assertEqual(bbc.create_atom(0b1001, False, 0, BitArray()),
                         BitArray(bin='11100000' '00001001'))
        self.assertEqual(bbc.create_atom(0b1111111, False, 0, BitArray()),
                         BitArray(bin='11100000' '01111111'))

    def test_create_atom_long(self):
        '''
        Test ``bbc.create_atom()`` with gaps that can be encoded in two bytes
        after the header.
        '''

        self.assertEqual(bbc.create_atom(0b10000000, False, 0, BitArray()),
                         BitArray(bin='11100000' '10000000' '10000000'))
        self.assertEqual(bbc.create_atom(all_bits(15), False, 0, BitArray()),
                         BitArray(bin='11100000' '11111111' '11111111'))

    def test_create_atom_dirty(self):
        '''
        Test ``bbc.create_atom()`` with offset bytes.
        '''

        self.assertEqual(bbc.create_atom(0b000, True, 0b0000, BitArray()),
                         BitArray(bin='00010000'))
        self.assertEqual(bbc.create_atom(0b001, True, 0b0001, BitArray()),
                         BitArray(bin='00110001'))
        self.assertEqual(bbc.create_atom(0b111, True, 0b1000, BitArray()),
                         BitArray(bin='11111000' '00000111'))
        self.assertEqual(bbc.create_atom(0b10000000, True, 0b1010, BitArray()),
                         BitArray(bin='11111010' '10000000' '10000000'))

    def test_create_atom_lits(self):
        '''
        Test ``bbc.create_atom()`` with literal bytes.
        '''

        lits = BitArray(bin='110101100010110101011100')
        self.assertEqual(bbc.create_atom(0b000, False, 3, lits),
                         '0b00000011' + lits)

        lits = lits[bits_per_byte:]
        self.assertEqual(bbc.create_atom(0b1111, False, 2, lits),
                         '0b1110001000001111' + lits)

        lits = lits[bits_per_byte:]
        self.assertEqual(bbc.create_atom(all_bits(15), False, 1, lits),
                         '0b111000011111111111111111' + lits)

    def test_compress_short(self):
        '''
        Test ``bbc.compress()`` using bytes with gaps that can be encoded in
        the header.
        '''

        for gaps in range(1, all_bits(3)):
            gap_prefix = BitArray(uint=gaps, length=3)

            # only gap
            bs = BitArray(bin='00000000' * gaps)
            self.assertEqual(bbc.compress(bs), gap_prefix + '0b00000')

            # gap with offset byte
            bs = BitArray(bin='00000000' * gaps + '01000000')
            expected = gap_prefix + '0b10001'
            self.assertEqual(bbc.compress(bs), expected)

            # gap with literals
            bs = BitArray(bin='00000000' * gaps + '11100000' '00000111')
            expected = gap_prefix + '0b000101110000000000111'
            self.assertEqual(bbc.compress(bs), expected)

            # gap with offset byte, then literals
            bs = BitArray(bin='00000000' * gaps + '000000011110000000000111')
            expected = gap_prefix + '0b00011000000011110000000000111'
            self.assertEqual(bbc.compress(bs), expected)

            # gap with literals, then offset byte
            bs = BitArray(bin='00000000' * gaps + '111000000000011101000000')
            expected = gap_prefix + '0b00011111000000000011101000000'
            self.assertEqual(bbc.compress(bs), expected)

    def test_compress_mid(self):
        '''
        Test ``bbc.compress()`` using bytes with gaps that can be encoded in
        one byte after the header.
        '''

        for gaps in range(all_bits(3), all_bits(7) + 1):
            gap_bs = BitArray(uint=gaps, length=8)

            # only gap
            bs = BitArray(bin='00000000' * gaps)
            self.assertEqual(bbc.compress(bs), '0b11100000' + gap_bs)

            # gap with offset byte
            bs = BitArray(bin='00000000' * gaps + '00100000')
            expected = '0b11110010' + gap_bs
            self.assertEqual(bbc.compress(bs), expected)

            # gap with literals
            bs = BitArray(bin='00000000' * gaps + '1001001001001001')
            expected = '0b11100010' + gap_bs + '0b1001001001001001'
            self.assertEqual(bbc.compress(bs), expected)

            # gap with offset byte, then literals
            bs = BitArray(bin='00000000' * gaps + '100000001001001001001001')
            expected = '0b11100011' + gap_bs + '0b100000001001001001001001'
            self.assertEqual(bbc.compress(bs), expected)

            # gap with literals, then offset byte
            bs = BitArray(bin='00000000' * gaps + '100100100100100110000000')
            expected = '0b11100011' + gap_bs + '0b100100100100100110000000'
            self.assertEqual(bbc.compress(bs), expected)

    def test_compress_long(self):
        '''
        Test ``bbc.compress()`` using bytes with gaps that can be encoded in
        two bytes after the header.
        '''

        bs = BitArray(bin='00000000' * 510)
        expected = BitArray(bin='111000001000000111111110')
        self.assertEqual(bbc.compress(bs), expected)


if __name__ == '__main__':
    ut.main()
