import logging
import re

from abc import ABC, abstractmethod
from typing import Optional

from lib.bitstring import BitString


class CompressionBase(ABC):
    '''
    Base class for compression algorithms.

    Represented as a class rather than a plain function in order to allow
    easier testing and debugging. Instead of reading and writing to a file,
    input and output can also be strings provided at runtime without having
    boilerplate code. In addition, it allows all derived classes to inherit
    class methods that are common across compression algorithms.
    '''

    @staticmethod
    @abstractmethod
    def compress(bs: BitString, word_size: Optional[int]) -> BitString:
        '''
        Compress the given bitmap index with the specified word size,
        if applicable.

        Args:
            bs: a BitString, or an object that can construct a BitString.
            word_size: the word size used in the algorithm.

        Returns:
            the compressed ``bs``.
        '''

        pass

    @classmethod
    def write(cls,
              in_file: str,
              out_file: str,
              col_count: int,
              word_size: Optional[int] = 8):
        '''
        Read the index from ``in_file`` with ``col_count`` columns and a word
        size of ``word_size`` (if applicable), then compress and write the
        result to ``out_file``.

        Args:
            in_file: the index to compress.
            out_file: the path to write the compressed index to.
            col_count: the number of columns in the in_file index.
            word_size: the word size used in the algorithm.
        '''

        with open(in_file, 'r') as ifile:
            content = ifile.read()

        with open(out_file, 'w') as ofile:
            for i in range(col_count):
                logging.debug('Compressing column {}'.format(i))
                column = BitString(content[i::col_count])
                compressed = cls.compress(column, word_size)
                ofile.write(str(compressed))
                ofile.write('\n')
