'''
Contains the implementation of the BBC algorithm, in addition to BBC-related
functions.
'''

import logging

from typing import Final, Optional

from lib.bitstring import BitString
from lib.compression import CompressionBase
from lib.util import all_bits


# BBC compression constants
bits_per_byte: Final = 8

header_gap_bits: Final = 3  # number of bits in header gap size
header_gap_max: Final = all_bits(header_gap_bits)  # max gap size in header
max_gap_bits: Final = 2 * bits_per_byte - 1        # max bits used for gap size


def gap_length(bs: BitString) -> int:
    '''
    Args:
        bs: the BitString to check for gaps.

    Returns:
        the number of gap bytes at the beginning of ``bs``. If the number
        of gap bytes exceeds the number that can be stored by a BBC atom,
        returns the max number of gaps that can be stored.
    '''

    gap_bits: Final = bs.run_length(0)
    gap_max: Final = all_bits(max_gap_bits)

    if gap_bits < bits_per_byte:
        return 0

    return min(gap_max, gap_bits // bits_per_byte)


def dirty_bit_pos(bs: BitString) -> int:
    '''
    Checks if the next byte in ``bs`` contains only a single set bit
    (i.e., is an offset, or dirty, byte).

    Args:
        bs: the BitString to check for a dirty byte.

    Returns:
        the position of the dirty bit in the next byte, or -1 if the byte
        is not a dirty byte.
    '''

    bstr = str(bs[:bits_per_byte])

    if bstr.count('1') != 1:
        return -1
    else:
        return bstr.find('1')


def literals_length(bs: BitString) -> int:
    '''
    Returns:
        the number of literal (i.e., non-gap, non-dirty) bytes at the
        beginning of bs.
    '''

    lits = 0

    while len(bs) > 0 and gap_length(bs) == 0:
        bs = bs[bits_per_byte:]
        lits += 1

    max_lits: Final = 0b1111
    return min(lits, max_lits)


def create_atom(gap_count: int,
                is_dirty: bool,
                special: int,
                literal: Optional[BitString] = None) \
        -> BitString:
    '''
    Creates the next compressed atom, consisting of a header byte
    and followed by trailing literals if is_dirty is false.

    Args:
        gap_count: the number of gaps to encode in the atom.
        is_dirty: whether or not the lower bits of the header byte in the
                  atom represents a dirty bit position.
        special: if is_dirty is True, represents the position of the dirty
                  bit in the last byte encoded by the atom, zero-indexed
                  from the right. Otherwise, ``special`` is a 4-bit value
                  representing the amount of trailing literals given by
                  ``literal``.
        literal: the trailing literals to add to the end of the atom.

    Returns:
        an atom encoding a sequence of bits with the information given by
        the parameters.

    Raises:
        ValueError: if ``literal`` is None when a BitString was expected,
                    or if ``gap_count`` is too large.
    '''

    if not is_dirty and literal is None:
        raise ValueError('expected a non-None value for literal')

    # header begins with 3 bits that indicate the number of gap bytes.
    # (if first three bits of header are all set, the remainder of
    # gap_count is stored in the bytes after the header.)
    header_gap_bits: Final = 3
    header_gap_max: Final = all_bits(header_gap_bits)
    header_gap_count: Final = min(gap_count, header_gap_max)

    max_gap_bits: Final = 2 * bits_per_byte - 1

    # initialize result with header byte
    result = BitString(header_gap_count, header_gap_bits)
    result += BitString(is_dirty, 1)
    result += BitString(special, 4)

    if header_gap_max <= gap_count <= all_bits(bits_per_byte - 1):
        logging.debug('One tail byte needed.')
        result += BitString(gap_count, bits_per_byte)
    elif all_bits(bits_per_byte - 1) < gap_count <= all_bits(max_gap_bits):
        logging.debug('Two tail bytes needed.')

        # the first bit of first byte is a flag indicating there's another
        # byte, and the rest of the byte is the upper bits of gap_count.
        # the second byte is the lower 8 bits.
        gaps = BitString(gap_count >> bits_per_byte, bits_per_byte)
        gaps[0] = 1
        gaps += BitString(gap_count, bits_per_byte)

        result += gaps
    elif all_bits(max_gap_bits) < gap_count:
        raise ValueError('too many gaps: {}'.format(gap_count))

    if not is_dirty:
        result += literal

    logging.debug('Created chunk: {}'.format(result))

    return result


class BBC(CompressionBase):
    '''
    BBC algorithm implementation. The following modifications have been made to
    the BBC patent's algorithm description:

    1. Gap length is encoded in three bits rather than five.
    2. The last field of the header byte uses four bits rather than three.
    3. Instead of using a split for indicating if there are literals or an
       offset byte, the fourth bit in the header byte is a flag for whether or
       not there is an offset byte.
    4. For encoding gap length across two bytes, the first byte contains the
       most significant bits rather than the least significant bits.
    5. Offset bytes are allowed as literals.
    '''

    @staticmethod
    def compress(bs, word_size=None):
        if not isinstance(bs, BitString):
            bs = BitString(bs)

        result = BitString()

        # compression data for logs
        input_length: Final = len(bs)
        atom_count = 0
        gap_count = 0
        off_count = 0
        lit_count = 0

        logging.info('Compressing {} bits with BBC'.format(input_length))
        logging.debug('Bits: {}'.format(bs))

        while len(bs) > 0:
            logging.debug('Remaining bits: {}'.format(bs))

            # determine the number of gaps and skip past them
            gap_bytes = gap_length(bs)
            bs = bs[gap_bytes * bits_per_byte:]

            if gap_bytes > 0:
                logging.info('Found gap of size {}'.format(gap_bytes))
                gap_count += 1

            # determine the type of byte following the gaps
            dirty_bit = dirty_bit_pos(bs)
            is_dirty = (dirty_bit != -1)
            literals = None

            if is_dirty:
                logging.debug('Offset byte: set bit @ {}'.format(dirty_bit))
                off_count += 1

                # skip past the offset byte
                bs = bs[bits_per_byte:]
                special = dirty_bit
            else:
                # literals encountered; encode as many as possible then skip
                # past them
                current_lit_count = literals_length(bs)
                literals = bs[:current_lit_count * bits_per_byte]
                bs = bs[current_lit_count * bits_per_byte:]
                special = current_lit_count

                logging.debug('Gap followed by literals: {}'.format(literals))
                lit_count += current_lit_count

            # encode the gaps and trailing byte(s) in an atom
            result += create_atom(gap_bytes, is_dirty, special, literals)
            atom_count += 1

        # log the compression metadata
        logging.info('Compressed bit count: {}'.format(len(result)))
        logging.info('Atom count: {}'.format(atom_count))
        logging.info('Gap count: {}'.format(gap_count))
        logging.info('Offset count: {}'.format(off_count))
        logging.info('Literal count: {}'.format(lit_count))

        ratio: Final = input_length / len(result) if len(result) > 0 else 'inf'
        logging.info('Compression ratio: {:.02f}'.format(ratio))

        return result
