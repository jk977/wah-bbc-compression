import random

from bitstring import BitArray

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
    for word_size in range(2, 65):
        print(f'Fuzzing WAH {word_size}')
        fuzz_compressor(ntimes, \
                        lambda bs: wah.compress(bs, word_size), \
                        lambda res: wah.decompress(*res, word_size), \
                        str_len)


def fuzz_bbc(ntimes, str_len):
    fuzz_compressor(ntimes, bbc.compress, bbc.decompress, str_len)


if __name__ == '__main__':
    print('Fuzzing WAH with small inputs...')
    fuzz_wah(1000, 64)

    print('Fuzzing BBC with small inputs...')
    fuzz_bbc(1000, 64)

    print('Fuzzing WAH with large inputs...')
    fuzz_wah(5, 10000)

    print('Fuzzing BBC with large inputs...')
    fuzz_bbc(5, 10000)
