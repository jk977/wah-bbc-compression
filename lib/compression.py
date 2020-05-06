'''
Contains the base class for compression algorithms.
'''

from abc import ABC, abstractmethod
from bitstring import BitArray


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
    def compress(bs: BitArray, word_size) -> str:
        '''
        Compress the given bitmap index with the specified word size,
        if applicable.

        Args:
            bs: a string of zeroes and ones.
            word_size: the word size used in the algorithm.

        Returns:
            the compressed ``bs``.

        Note:
            The format of ``bs`` is not checked. If ``bs`` contains
            characters other than '0' and '1', the resulting string is
            meaningless.
        '''

        pass
