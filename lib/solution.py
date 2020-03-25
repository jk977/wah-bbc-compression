'''
Functions required by the assignment description. Builds on top of the other
modules in the package to produce the required functions.
'''

import logging
import operator as op
import os

from functools import reduce
from typing import Final, Optional, Type

from lib.bitstring import BitString
from lib.compression import CompressionBase

from lib.bbc import BBC
from lib.wah import WAH


def _compression_filename(in_path: str, method: str,
                          word_size: Optional[int] = None) \
                            -> str:
    '''
    Args:
        in_path: a path to the compression input file.
        method: one of 'WAH' or 'BBC'.
        word_size: the word size used in the compression algorithm.

    Returns:
        the name of the output file for the compression algorithm, named
        using the conventions detailed in the assignment description.
    '''

    suffix: Final = '_{}'.format(word_size) if word_size is not None else ''
    return in_path + '_{}'.format(method) + suffix


def _index_row(row: str) -> BitString:
    '''
    Turn a comma-separated data file row into its compressed
    form as specified by the assignment.

    Args:
        row: a string in the format 'animal,age,adopted', where animal is in
             'cat', 'dog', 'turtle', or 'bird'; age is an integer between
             1 and 100 (inclusive); and adopted is 'True' or 'False'.

    Returns:
        a BitString containing the binary representation of the columns given
        by ``row``.
    '''

    logging.debug('Indexing row: {}'.format(row))
    [animal, age, adopted] = row.split(',')

    # animals allowed in the animal column
    animals: Final = ['cat', 'dog', 'turtle', 'bird']

    # number of bits in each column
    animal_width: Final = 4
    age_width: Final = 10
    adopted_width: Final = 2

    # set of 4 bits representing the animal type, in the same left-to-right
    # order as the animals array.
    animal_cols: Final = 0b1000 >> animals.index(animal)
    animal_bits: Final = BitString(animal_cols, animal_width)

    # set of 10 bits representing the animal age, in buckets of 10 years
    # (0b1000000000 -> 1-10 years, 0b0100000000 -> 11-20, etc.)
    age_cols: Final = 0b1000000000 >> (int(age) - 1) // 10
    age_bits: Final = BitString(age_cols, age_width)

    # set of 2 bits representing whether or not the animal was adopted
    adopted_cols: Final = 0b10 if adopted == 'True' else 0b01
    adopted_bits: Final = BitString(adopted_cols, adopted_width)

    return animal_bits + age_bits + adopted_bits


def create_index(in_file: str, out_file: str, sort_data: bool) -> str:
    '''
    Create an index for the data from ``in_file`` and write the result to
    ``out_file``.

    Args:
        in_file: the path to the file to index.
        out_file: the path to write the index to.
        sort_data: whether or not to sort in_file's lines lexicographically
                   before indexing.

    Returns:
        the path to the resulting index file. This will be ``out_file``
        if ``sort_data`` is False, or ``out_file`` appended with '_sorted'.
        otherwise.
    '''

    logging.debug('Indexing {} to {}'.format(in_file, out_file))

    with open(in_file, 'r') as ifile:
        contents = ifile.read().splitlines()

    if sort_data:
        out_file += '_sorted'
        contents = sorted(contents)

    index = reduce(op.iadd, map(_index_row, contents))

    with open(out_file, 'w') as ofile:
        ofile.write(str(index))

    return out_file


def compress_index(in_file: str, out_dir: str, method: str,
                   word_size: Optional[int] = None) \
                       -> str:
    '''
    Compress ``in_file`` using the given compression method, writing the result
    to ``out_dir``.

    Args:
        in_file: the path to the file to compress.
        out_dir: the directory to output the compressed file in.
        method: one of 'WAH' or 'BBC'.
        word_size: the word size used in the compression algorithm.

    Returns:
        the path to the resulting compressed file.

    Raises:
        ValueError: if ``word_size`` is None when an int was expected.
        NotImplementedError: if ``method`` is not a recognized compression
                             algorithm.
    '''

    compressor: Type[CompressionBase]
    out_file: Final = _compression_filename(in_file, method, word_size)

    logging.debug('Compressing index {} to {}'.format(in_file, out_file))

    if method == 'WAH':
        if word_size is None:
            raise ValueError('WAH requires a word size')

        compressor = WAH
    elif method == 'BBC':
        compressor = BBC
    else:
        raise NotImplementedError('compress_index(method = {})'.format(method))

    columns: Final = 16
    compressor.write(in_file, out_file, columns, word_size)
    return out_file
