'''
Utility functions used across multiple modules.
'''

def all_bits(bit_count: int) -> int:
    '''
    Get an integer with the specified number of set bits.

    Args:
        bit_count: the number of bits to set.

    Returns:
        an ``int`` with only the lowest ``bit_count`` bits set.
    '''

    return 2**bit_count - 1
