'''
Unit tests for WAH implementation.
'''

import itertools as it
import unittest as ut

import lib.wah as wah

from lib.bitstring import BitString
from lib.wah import WAH


############################
# wrappers for WAH methods #
############################

def run_length(index, word_size):
    return wah.run_length(BitString(index), word_size)


def encode_run(index, word_size):
    tail, encoded = wah.encode_run(BitString(index), word_size)
    return (str(tail), encoded and str(encoded))


def encode_literal(index, word_size):
    tail, encoded = wah.encode_literal(BitString(index), word_size)
    return (str(tail), str(encoded))


def compress(index, word_size):
    return str(WAH.compress(index, word_size))


class TestWAH(ut.TestCase):
    def test_run_length(self):
        '''
        Test ``_run_length()``
        '''

        for word_size in range(8, 65):
            self.assertEqual(run_length('', word_size), 0)
            self.assertEqual(run_length('0', word_size), 0)
            self.assertEqual(run_length('1', word_size), 0)
            self.assertEqual(run_length('01', word_size), 0)
            self.assertEqual(run_length('10', word_size), 0)
            self.assertEqual(run_length('01'*1000, word_size), 0)

        for word_size in range(8, 65):
            sect = word_size - 1
            self.assertEqual(run_length('0'*sect, word_size), 1)
            self.assertEqual(run_length('0'*sect*5, word_size), 5)
            self.assertEqual(run_length('0'*sect*63, word_size), 63)

        # overflow tests
        self.assertEqual(run_length('0'*7*64, 8), 63)
        self.assertEqual(run_length('0'*15*16384, 16), 16383)

    def test_encode_run(self):
        '''
        Test ``_encode_run()``
        '''

        self.assertEqual(encode_run('111110', 4), ('110', '1101'))
        self.assertEqual(encode_run('111111', 4), ('', '1'*3 + '0'))
        self.assertEqual(encode_run('111111111', 4), ('', '1'*4))

        self.assertEqual(encode_run('1111101', 4), ('1101', '1101'))
        self.assertEqual(encode_run('1111110', 4), ('0', '1110'))
        self.assertEqual(encode_run('1111111110', 4), ('0', '1'*4))

        self.assertEqual(encode_run('00000001111111', 8),
                         ('1111111', '10000001'))

        self.assertEqual(encode_run('0'*7, 8), ('', '10000001'))
        self.assertEqual(encode_run('0'*10, 8), ('000', '10000001'))
        self.assertEqual(encode_run('0'*14, 8), ('', '10000010'))
        self.assertEqual(encode_run('1'*7*(2**6 - 1), 8), ('', '1'*8))
        self.assertEqual(encode_run('0'*7*2**6, 8), ('0'*7, '10' + '1'*6))
        self.assertEqual(encode_run('0'*7*(2**6 - 1) + '10101', 8),
                         ('10101', '10111111'))

        self.assertEqual(encode_run('0'*31*2**6, 32),
                         ('', '1' + '0'*24 + '1000000'))
        self.assertEqual(encode_run('0'*31*2**7, 32),
                         ('', '1' + '0'*23 + '10000000'))

    def test_encode_literal(self):
        '''
        Test ``_encode_literal()``
        '''

        for i in range(3, 65):
            self.assertEqual(encode_literal('', i), ('', '0'*i))
            self.assertEqual(encode_literal('1', i), ('', '01' + '0'*(i - 2)))
            self.assertEqual(encode_literal('10', i), ('', '01' + '0'*(i - 2)))
            self.assertEqual(encode_literal('01', i),
                             ('', '001' + '0'*(i - 3)))

        self.assertEqual(encode_literal('001', 4), ('', '0001'))
        self.assertEqual(encode_literal('0101', 4), ('1', '0010'))
        self.assertEqual(encode_literal('01111', 4), ('11', '0011'))
        self.assertEqual(encode_literal('100101', 4), ('101', '0100'))
        self.assertEqual(encode_literal('1011001', 4), ('1001', '0101'))
        self.assertEqual(encode_literal('11010001', 4), ('10001', '0110'))
        self.assertEqual(encode_literal('111100001', 4), ('100001', '0111'))

        self.assertEqual(encode_literal('1110111', 8), ('', '01110111'))
        self.assertEqual(encode_literal('01010101', 8), ('1', '00101010'))
        self.assertEqual(encode_literal('110100110', 8), ('10', '01101001'))
        self.assertEqual(encode_literal('1001110100', 8), ('100', '01001110'))
        self.assertEqual(encode_literal('11011011000', 8),
                         ('1000', '01101101'))
        self.assertEqual(encode_literal('010101010000', 8),
                         ('10000', '00101010'))
        self.assertEqual(encode_literal('1110011100000', 8),
                         ('100000', '01110011'))

    def test_compress_literals(self):
        '''
        Test ``WAH.compress()`` on strings of literal bytes
        '''

        for i in range(3, 65):
            self.assertEqual(compress('', i), '')
            self.assertEqual(compress('0', i), '0'*i)
            self.assertEqual(compress('1', i), '01' + '0'*(i - 2))

        for word_size in range(4, 65):
            sect_size = word_size - 1

            for lit_length in range(1, sect_size):
                zeroes = '0' * (sect_size - lit_length)
                ones = '1' * lit_length

                for bits in it.combinations(it.chain(zeroes, ones), sect_size):
                    word = ''.join(bits)
                    result = compress(word, word_size)
                    self.assertEqual(result, '0' + word)

    def test_compress_runs(self):
        '''
        Test ``WAH.compress()`` on runs of bits
        '''

        for word_size in range(8, 65):
            sect_size = word_size - 1
            result_fmt = '{{:0{}b}}'.format(sect_size - 1)

            for run_length in range(1, 40):
                zeroes = '0' * sect_size * run_length
                ones = '1' * sect_size * run_length

                self.assertEqual(compress(zeroes, word_size),
                                 '10' + result_fmt.format(run_length))
                self.assertEqual(compress(ones, word_size),
                                 '11' + result_fmt.format(run_length))

    def test_compress_long(self):
        '''
        Test ``WAH.compress()`` on more complex examples
        '''

        # WAH example from class slides.
        # Note: The slides contained an error in encoding the bits; this
        #       has been corrected in the test.
        wah_slide_example = '00000000' + '00000000' \
            + '00010000' + '00000000' * 13 \
            + '10101010' + '11110000'
        wah_slide_corrected_result = '00000000' + '00000000' \
            + '00001000' + '00000000' \
            + '10000000' + '00000000' \
            + '00000000' + '00000011' \
            + '00000101' + '01010111' \
            + '10000000' + '00000000'
        wah_slide_word_size = 32

        self.assertEqual(compress(wah_slide_example, wah_slide_word_size),
                         wah_slide_corrected_result)

        # WAH example from the patent description.
        # Note: The algorithm has been slightly modified from the patent;
        #       trailing bits are encoded differently than the patent.
        #       This is accounted for in the test.
        patent_example = '10000000' + '00000000' \
            + '00000000' + '00000000' \
            + '00000000' + '00000000' \
            + '00000000' + '00001000' \
            + '01100110' + '01111111' \
            + '11111111' + '11111111' \
            + '11111111' + '11111111' \
            + '11111111' + '11111100' \
            + '00000000' + '00000000' \
            + '00000000' + '00000000' \
            + '00000100' + '000111'
        patent_modified_result = '01000000' + '00000000' \
            + '10000000' + '00000011' \
            + '01000011' + '00110011' \
            + '11000000' + '00000011' \
            + '01111110' + '00000000' \
            + '10000000' + '00000010' \
            + '01000001' + '11000000'
        patent_word_size = 16

        self.assertEqual(compress(patent_example, patent_word_size),
                         patent_modified_result)


if __name__ == '__main__':
    ut.main()
