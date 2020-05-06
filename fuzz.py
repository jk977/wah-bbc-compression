import random
import logging

from bitstring import BitArray


logging.basicConfig(level=logging.DEBUG)


import lib.wah as wah
import lib.bbc as bbc


def rand_char():
    return random.choice([chr(n) for n in range(128)])


def rand_ascii(length):
    s = ''.join(rand_char() for _ in range(length))
    return s.encode(encoding='ASCII')


def fuzz_compressor(ntimes, compress, decompress, str_len):
    for _ in range(ntimes):
        bs = BitArray(bytes=rand_ascii(str_len))
        print(f'Testing {bs.bin}')
        assert decompress(compress(bs)) == bs


def fuzz_wah(ntimes, str_len):
    for word_size in range(8, 65):
        fuzz_compressor(ntimes, \
                        lambda bs: wah.compress(bs, word_size), \
                        lambda result: wah.decompress(*result, word_size), \
                        str_len)


def fuzz_bbc(ntimes, str_len):
    fuzz_compressor(ntimes, bbc.compress, bbc.decompress, str_len)


if __name__ == '__main__':
    print('Fuzzing BBC...')
    fuzz_bbc(10000, 10)

    print('Fuzzing WAH...')
    fuzz_wah(10, 10)
