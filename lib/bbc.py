'''
Contains an implementation of the byte-aligned bitmap compression (BBC)
algorithm, in addition to BBC-related utility functions. The algorithm
has been modified from the original; see the ``BBC`` class documentation
for the differences.
'''

import logging

from typing import Final, Tuple

from lib.compression import CompressionBase
from lib.util import all_bits, binstr, chunks_of


# BBC compression constants
bits_per_byte: Final = 8

header_gap_bits: Final = 3  # number of bits in header gap size
header_gap_max: Final = all_bits(header_gap_bits)  # max gap size in header
max_gap_bits: Final = 2 * bits_per_byte - 1        # max bits used for gap size


def get_gaps(bs: str) -> Tuple[str, int]:
    '''
    Args:
        bs: the string to check for gaps.

    Returns:
        a tuple ``(tail, gaps)``, where ``tail`` is ``bs`` without the leading
        gaps and ``gaps`` is the number of gap bytes to encode.
    '''

    bit_idx: Final = bs.find('1')
    gap_bits: Final = bit_idx if bit_idx >= 0 else len(bs)
    gap_max: Final = all_bits(max_gap_bits)

    if gap_bits < bits_per_byte:
        return bs, 0

    # if the number of gaps found is greater than the amount that can be
    # stored in an atom, only take what can be stored
    gaps: Final = min(gap_max, gap_bits // bits_per_byte)
    return bs[gaps * bits_per_byte:], gaps


def dirty_bit_pos(bs: str) -> int:
    '''
    Checks if the next byte in ``bs`` contains only a single set bit
    (i.e., is an offset, or dirty, byte).

    Args:
        bs: the string to check for a dirty byte.

    Returns:
        the position of the dirty bit in the next byte, or -1 if the byte
        is not a dirty byte.
    '''

    byte = bs[:bits_per_byte]

    if byte.count('1') != 1:
        return -1
    else:
        return byte.find('1')


def get_literals(bs: str) -> Tuple[str, str]:
    '''
    Returns:
        a tuple ``(tail, literals)`` where ``tail`` is ``bs`` without the
        literals, and ``literals`` is the string of literal bytes at the
        beginning of ``bs``.
    '''

    literal_max: Final = 0b1111
    literals = ''
    count = 0

    for byte in chunks_of(bits_per_byte, bs):
        if byte.count('1') == 0:
            break

        literals += byte
        count += 1

        if count == literal_max:
            break

    return bs[count * bits_per_byte:], literals


def create_atom(gaps: int,
                is_dirty: bool,
                special: int,
                literals: str = '') \
        -> str:
    '''
    Creates the next compressed atom, consisting of a header byte
    and followed by trailing literals if is_dirty is false.

    Args:
        gaps: the number of gaps to encode in the atom.
        is_dirty: whether or not the lower bits of the header byte in the
                  atom represent a dirty bit position.
        special: if ``is_dirty`` is ``True``, represents the position of the
                 dirty bit in the last byte encoded by the atom, zero-indexed
                 from the right. Otherwise, ``special`` is a 4-bit value
                 representing the amount of trailing literals given by
                 ``literals``.
        literals: the trailing literals to add to the end of the atom.

    Returns:
        an atom encoding a sequence of bits with the information given by
        the parameters.

    Raises:
        ValueError: if ``literals`` is ``None`` when a ``str`` is expected,
                    or if ``gaps`` is too large.
    '''

    # header begins with 3 bits that indicate the number of gap bytes.
    # (if first three bits of header are all set, the remainder of
    # gaps is stored in the bytes after the header.)
    header_gap_bits: Final = 3
    header_gap_max: Final = all_bits(header_gap_bits)
    header_gap_count: Final = min(gaps, header_gap_max)

    max_gap_bits: Final = 2 * bits_per_byte - 1

    # initialize result with header byte
    result = binstr(header_gap_count, header_gap_bits)
    result += '1' if is_dirty else '0'
    result += binstr(special, 4)

    if header_gap_max <= gaps <= all_bits(bits_per_byte - 1):
        logging.debug('One tail byte needed.')
        result += binstr(gaps, bits_per_byte)
    elif all_bits(bits_per_byte - 1) < gaps <= all_bits(max_gap_bits):
        logging.debug('Two tail bytes needed.')

        # the first bit of first byte is a flag indicating there's another
        # byte, and the rest of the byte is the upper bits of gaps.
        # the second byte is the lower 8 bits.
        upper: Final = binstr(gaps >> bits_per_byte, bits_per_byte - 1)
        lower: Final = binstr(gaps, bits_per_byte)
        result += f'1{upper}{lower}'
    elif gaps > all_bits(max_gap_bits):
        raise ValueError(f'too many gaps: {gaps}')

    if not is_dirty:
        result += literals

    return result


class BBC(CompressionBase):
    '''
    BBC algorithm implementation. The following modifications have been made to
    the BBC patent's algorithm description:

    1. Gap length is encoded in three bits rather than five.
    2. The last field of the header byte uses four bits rather than three.
    3. Instead of using a split to indicate an offset byte in the header byte,
       the fourth bit of the header is a flag that indicates the presence of an
       offset byte.
    4. For encoding the gap length across two bytes, the first byte contains
       the most significant bits rather than the least significant bits.
    5. Offset bytes are allowed as literals, and can be literally encoded in
       the beginning, middle, or end of a sequence of literals.
    '''

    @staticmethod
    def compress(bs, word_size=None):
        if not isinstance(bs, str):
            bs = str(bs)

        logging.info('Compressing %d bits with BBC', len(bs))
        logging.debug('Bits: %s', bs)

        result = ''

        while len(bs) > 0:
            bs, gaps = get_gaps(bs)

            if gaps > 0:
                logging.info('Found gap of size %d', gaps)

            # get the byte after next to determine whether or not an offset
            # byte should be treated as a literal
            lookahead_byte: Final = bs[bits_per_byte:2 * bits_per_byte]
            offset_as_literal: Final = lookahead_byte.count('1') > 0

            # determine the type of byte following the gaps
            dirty_bit = dirty_bit_pos(bs)
            is_dirty = (dirty_bit != -1) and not offset_as_literal

            if is_dirty:
                # skip past the offset byte without encoding literals,
                # storing the dirty bit position in ``special``
                bs, literals = bs[bits_per_byte:], ''
                special = dirty_bit
                logging.info('Offset byte found: bit @ %d', dirty_bit)
            else:
                # literals encountered; encode and skip, storing the number
                # of literals in ``special``
                bs, literals = get_literals(bs)
                special = len(literals) // bits_per_byte
                logging.info('Literals found: %d', special)

            atom = create_atom(gaps, is_dirty, special, literals)
            logging.info('Created atom of length %d', len(atom))
            logging.debug('Atom: %s', atom)

            result += atom

        logging.info('Compressed bit count: %d', len(result))
        return result
