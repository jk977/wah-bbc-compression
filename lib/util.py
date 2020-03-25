'''
Utility functions used across multiple modules.
'''

def all_bits(bit_count: int) -> int:
    '''
    Args:
        bit_count: the number of bits to set in the return value.

    Returns:
        a bit field with the lowest ``bit_count`` bits set, and the rest unset.
    '''

    return 2**bit_count - 1
