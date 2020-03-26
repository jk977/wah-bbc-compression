'''
Utility functions used across multiple modules.
'''

from typing import Any, Optional


def all_bits(bit_count: int) -> int:
    '''
    Get an integer with the specified number of set bits.

    Args:
        bit_count: the number of bits to set.

    Returns:
        an ``int`` with only the lowest ``bit_count`` bits set.
    '''

    return 2**bit_count - 1


def binstr(n: int, length: Optional[int] = None) -> str:
    '''
    Convert ``n`` to a binary string. Similar to ``bin()`` but without the
    prefix ``0b`` and with the ability to specify the string length.

    Args:
        n: the number to convert to a binary string.
        length: the desired length of the resulting string.

    Returns:
        a string containing the binary representation of ``n``. If ``length``
        is specified, the lower ``length`` bits are taken from ``n``, and
        the rest are truncated.
    '''

    if length is None:
        fmt = '{:b}'
    else:
        n &= all_bits(length)
        fmt = '{{:0{}b}}'.format(length)

    return fmt.format(n)


def chunks_of(n: int, ls: Any):
    '''
    Generate pieces of a slice-able object in chunks of ``n``.

    Args:
        n: the size of chunks to take from ``ls``.
        ls: the object to get chunks of.

    Returns:
        a generator that yields the next ``n``-sized slice of ``ls``.
    '''

    while len(ls) > 0:
        yield ls[:n]
        ls = ls[n:]
