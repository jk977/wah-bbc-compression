'''
Utility functions used across multiple modules.
'''

from typing import Any, Generator, List, Optional


def all_bits(bit_count: int) -> int:
    '''
    Args:
        bit_count: the number of bits to set in the return value.

    Returns:
        a bit field with the lowest ``bit_count`` bits set, and the rest unset.
    '''

    return 2**bit_count - 1


def binstr(n: int, length: Optional[int] = None) -> str:
    if length is None:
        fmt = '{:b}'
    else:
        n &= all_bits(length)
        fmt = '{{:0{}b}}'.format(length)

    return fmt.format(n)


def chunks_of(n: int, ls: Any):
    while len(ls) > 0:
        yield ls[:n]
        ls = ls[n:]
