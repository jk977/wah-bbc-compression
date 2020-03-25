'''
Unit tests for WAH implementation.
'''

import itertools as it
import unittest as ut

import lib.wah as wah

from lib.wah import WAH


##############
# unit tests #
##############

class TestWAH(ut.TestCase):
    def test_run_length(self):
        for ws in range(8, 65):
            # test for no runs
            self.assertEqual(wah.run_length('', ws), 0)
            self.assertEqual(wah.run_length('0', ws), 0)
            self.assertEqual(wah.run_length('1', ws), 0)
            self.assertEqual(wah.run_length('01', ws), 0)
            self.assertEqual(wah.run_length('10', ws), 0)
            self.assertEqual(wah.run_length('01'*1000, ws), 0)

        for ws in range(8, 65):
            # test for runs that don't overflow
            sect = ws - 1
            self.assertEqual(wah.run_length('0'*sect, ws), 1)
            self.assertEqual(wah.run_length('0'*sect*5, ws), 5)
            self.assertEqual(wah.run_length('0'*sect*63, ws), 63)

        # test for overflows
        self.assertEqual(wah.run_length('0000000'*64, 8), 63)
        self.assertEqual(wah.run_length('000000000000000'*16384, 16), 16383)

    def test_encode_run(self):
        # test for single-word runs without leftovers
        self.assertEqual(wah.encode_run('111', 4), ('', '1101'))
        self.assertEqual(wah.encode_run('0000000', 8), ('', '10000001'))

        # test for single-word runs with leftovers
        self.assertEqual(wah.encode_run('111110', 4), ('110', '1101'))
        self.assertEqual(wah.encode_run('1111101', 4), ('1101', '1101'))
        self.assertEqual(wah.encode_run('0000000000', 8), ('000', '10000001'))
        self.assertEqual(wah.encode_run('00000001111111', 8),
                         ('1111111', '10000001'))

        # test for multi-word runs without leftovers
        self.assertEqual(wah.encode_run('111111', 4), ('', '1110'))
        self.assertEqual(wah.encode_run('111111111', 4), ('', '1111'))

        self.assertEqual(wah.encode_run('00000000000000', 8), ('', '10000010'))
        self.assertEqual(wah.encode_run('1111111'*(2**6 - 1), 8),
                         ('', '11111111'))

        self.assertEqual(wah.encode_run('0'*31*2**6, 32),
                         ('', '10' + '0'*23 + '1000000'))
        self.assertEqual(wah.encode_run('0'*31*2**7, 32),
                         ('', '10' + '0'*22 + '10000000'))

        # test for multi-word runs with leftovers
        self.assertEqual(wah.encode_run('1111110', 4), ('0', '1110'))
        self.assertEqual(wah.encode_run('1111111110', 4), ('0', '1111'))
        self.assertEqual(wah.encode_run('0000000'*2**6, 8),
                         ('0000000', '10111111'))
        self.assertEqual(wah.encode_run('0000000'*(2**6 - 1) + '10101', 8),
                         ('10101', '10111111'))

    def test_encode_literal(self):
        for i in range(3, 65):
            # test zero-padding on short literals
            self.assertEqual(wah.encode_literal('', i), ('', '0'*i))
            self.assertEqual(wah.encode_literal('1', i),
                             ('', '01' + '0'*(i - 2)))
            self.assertEqual(wah.encode_literal('10', i),
                             ('', '01' + '0'*(i - 2)))
            self.assertEqual(wah.encode_literal('01', i),
                             ('', '001' + '0'*(i - 3)))

        # test single-literal compression with 4-bit words
        self.assertEqual(wah.encode_literal('001', 4), ('', '0001'))
        self.assertEqual(wah.encode_literal('0101', 4), ('1', '0010'))
        self.assertEqual(wah.encode_literal('01111', 4), ('11', '0011'))
        self.assertEqual(wah.encode_literal('100101', 4), ('101', '0100'))
        self.assertEqual(wah.encode_literal('1011001', 4), ('1001', '0101'))
        self.assertEqual(wah.encode_literal('11010001', 4), ('10001', '0110'))
        self.assertEqual(wah.encode_literal('111100001', 4),
                         ('100001', '0111'))

        # test single-literal compression with 8-bit words
        self.assertEqual(wah.encode_literal('1110111', 8), ('', '01110111'))
        self.assertEqual(wah.encode_literal('01010101', 8), ('1', '00101010'))
        self.assertEqual(wah.encode_literal('110100110', 8),
                         ('10', '01101001'))
        self.assertEqual(wah.encode_literal('1001110100', 8),
                         ('100', '01001110'))
        self.assertEqual(wah.encode_literal('11011011000', 8),
                         ('1000', '01101101'))
        self.assertEqual(wah.encode_literal('010101010000', 8),
                         ('10000', '00101010'))
        self.assertEqual(wah.encode_literal('1110011100000', 8),
                         ('100000', '01110011'))

    def test_compress_literals(self):
        '''
        Test ``WAH.compress()`` on strings of literal bytes
        '''

        for ws in range(3, 65):
            # test literal zero-padding on short inputs
            self.assertEqual(WAH.compress('', ws), '')
            self.assertEqual(WAH.compress('0', ws), '0'*ws)
            self.assertEqual(WAH.compress('1', ws), '01' + '0'*(ws - 2))

        for ws in range(4, 65):
            sect_size = ws - 1

            for one_count in range(1, sect_size):
                zeroes = '0' * (sect_size - one_count)
                ones = '1' * one_count

                for bits in it.combinations(it.chain(zeroes, ones), sect_size):
                    # get a string of bits with the given word size in the
                    # format "0+1+" such that there is not a run of either bit
                    word = ''.join(bits)
                    result = WAH.compress(word, ws)
                    self.assertEqual(result, '0' + word)

    def test_compress_runs(self):
        '''
        Test ``WAH.compress()`` on runs of bits
        '''

        for word_size in range(8, 65):
            sect_size = word_size - 1
            result_fmt = '{{:0{}b}}'.format(sect_size - 1)

            for length in range(1, 40):
                # test the compression of a run of both zeroes and ones
                # with ``length`` sections
                zeroes = '0' * sect_size * length
                ones = '1' * sect_size * length

                self.assertEqual(WAH.compress(zeroes, word_size),
                                 '10' + result_fmt.format(length))
                self.assertEqual(WAH.compress(ones, word_size),
                                 '11' + result_fmt.format(length))

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

        self.assertEqual(WAH.compress(wah_slide_example, wah_slide_word_size),
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

        self.assertEqual(WAH.compress(patent_example, patent_word_size),
                         patent_modified_result)


if __name__ == '__main__':
    ut.main()
