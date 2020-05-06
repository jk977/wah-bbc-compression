'''
Contains the base class for compression algorithms.
'''

from abc import ABC, abstractmethod
from bitstring import BitArray


class CompressionBase(ABC):
    '''
    Base class for compression algorithms.
    '''

    @staticmethod
    @abstractmethod
    def compress(bs: BitArray, word_size) -> BitArray:
        '''
        Compress the given bitmap index with the specified word size,
        if applicable.

        Args:
            bs: the bits to compress.
            word_size: the word size used in the algorithm.

        Returns:
            the compressed ``bs``.
        '''

        pass
