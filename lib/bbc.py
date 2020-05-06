'''
Contains an implementation of the byte-aligned bitmap code (BBC) compression
algorithm, in addition to BBC-related utility functions. The algorithm
has been modified from the original; see the ``BBC`` class documentation
for the differences.

The following modifications have been made to the BBC patent's algorithm
description:

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

import logging

from bitstring import BitArray

from lib.util import all_bits


# BBC compression constants
bits_per_byte = 8

header_gap_bits = 3  # number of bits in header gap size
header_gap_max = all_bits(header_gap_bits)  # max gap size in header
max_gap_bits = 2 * bits_per_byte - 1        # max bits used for gap size


def get_gaps(bs: BitArray):
    '''
    Args:
        bs: the bits to check for gaps.

    Returns:
        a tuple ``(tail, gaps)``, where ``tail`` is ``bs`` without the leading
        gaps and ``gaps`` is the number of gap bytes to encode.
    '''

    bit_idx = bs.find('0b1')
    gap_bits = bit_idx[0] if bit_idx else len(bs)
    gap_max = all_bits(max_gap_bits)

    if gap_bits < bits_per_byte:
        return bs, 0

    # if the number of gaps found is greater than the amount that can be
    # stored in an atom, only take what can be stored
    gaps = min(gap_max, gap_bits // bits_per_byte)
    return bs[gaps * bits_per_byte:], gaps


def dirty_bit_pos(bs: BitArray) -> int:
    '''
    Checks if the next byte in ``bs`` contains only a single set bit
    (i.e., is an offset, or dirty, byte).

    Args:
        bs: the bits to check for a dirty byte.

    Returns:
        the position of the dirty bit in the next byte, or -1 if the byte
        is not a dirty byte.
    '''

    byte = bs[:bits_per_byte]

    if byte.count(1) != 1:
        return -1
    else:
        return byte.find('0b1')[0]


def get_literals(bs: BitArray):
    '''
    Returns:
        a tuple ``(tail, literals)`` where ``tail`` is ``bs`` without the
        literals, and ``literals`` is the series of literal bytes at the
        beginning of ``bs``.
    '''

    literal_max = 0b1111
    literals = BitArray()
    count = 0

    for byte in bs.cut(bits_per_byte):
        if byte.count(1) == 0:
            break

        literals += byte
        count += 1

        if count == literal_max:
            break

    return bs[count * bits_per_byte:], literals


def create_atom(gaps: int,
                is_dirty: bool,
                special: int,
                literals: BitArray) \
        -> BitArray:
    '''
    Creates the next compressed atom, consisting of a header byte
    and followed by trailing literals if ``is_dirty`` is ``False``.

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
        an atom encoding the information given by the parameters.

    Raises:
        ValueError: if ``literals`` is ``None`` when a ``BitArray`` is
                    expected, or if ``gaps`` is too large.
    '''

    if not is_dirty and literals is None:
        raise ValueError('Expected a value for literals, got None')

    # header begins with 3 bits that indicate the number of gap bytes.
    # (if first three bits of header are all set, the remainder of
    # gaps is stored in the bytes after the header.)
    header_gap_bits = 3
    header_gap_max = all_bits(header_gap_bits)
    header_gap_count = min(gaps, header_gap_max)

    max_gap_bits = 2 * bits_per_byte - 1

    # construct the header byte
    result = BitArray(uint=header_gap_count, length=3)
    result += BitArray(uint=1 if is_dirty else 0, length=1)
    result += BitArray(uint=special, length=4)

    if header_gap_max <= gaps <= all_bits(bits_per_byte - 1):
        # gap length can be encoded in one byte after header
        logging.debug('One tail byte needed.')
        result += BitArray(uint=gaps, length=bits_per_byte)
    elif all_bits(bits_per_byte - 1) < gaps <= all_bits(max_gap_bits):
        # gap length can be encoded in two bytes after header
        logging.debug('Two tail bytes needed.')

        upper = gaps >> bits_per_byte
        lower_mask = (1 << bits_per_byte) - 1
        lower = gaps & lower_mask

        # the first bit of first byte is a flag indicating there's another
        # byte, and the rest of the byte is the upper bits of gaps.
        # the second byte is the lower 8 bits.
        result += BitArray(uint=1, length=1)
        result += BitArray(uint=upper, length=bits_per_byte - 1)
        result += BitArray(uint=lower, length=bits_per_byte)
    elif gaps > all_bits(max_gap_bits):
        raise ValueError(f'gaps too large ({gaps} > {all_bits(max_gap_bits)})')

    if not is_dirty:
        result += literals

    return result


def compress(bs):
    '''
    Compress the given bits using the BBC algorithm.

    Args:
        bs: the bits to compress.

    Returns:
        the compressed ``bs``.
    '''

    if len(bs) == 0:
        raise ValueError('bs must have a length greater than 0')

    logging.info('Compressing %d bits with BBC', len(bs))
    logging.debug('Bits: %s', bs.bin)

    result = BitArray()

    while len(bs) > 0:
        bs, gaps = get_gaps(bs)

        if gaps > 0:
            logging.info('Found gap of size %d', gaps)

        # get the byte after next to determine whether or not an offset byte
        # should be treated as a literal
        lookahead_byte = bs[bits_per_byte:2 * bits_per_byte]
        offset_as_literal = lookahead_byte.count(1) > 0

        # determine the type of byte following the gaps
        dirty_bit = dirty_bit_pos(bs)
        is_dirty = (dirty_bit != -1) and not offset_as_literal

        if is_dirty:
            # skip past the offset byte without encoding literals, storing the
            # dirty bit position in ``special``
            bs, literals = bs[bits_per_byte:], BitArray()
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
        logging.debug('Atom: %s', atom.bin)

        result += atom

    logging.info('Compressed bit count: %d', len(result))
    logging.debug('Compressed bits: %s', result.bin)

    return result


def decompress(bs):
    '''
    Decompress the given BBC-compressed data. This is the inverse of
    ``BBC.compress()``.

    Args:
        bs: the bits to compress.
        word_size: the word size used in the algorithm.
    '''

    if len(bs) == 0:
        raise ValueError('bs must have a length greater than 0')

    logging.info('Decompressing %d bits with BBC', len(bs))
    logging.debug('Bits: %s', bs.bin)

    result = BitArray()

    while len(bs) > 0:
        if len(bs) < bits_per_byte:
            raise ValueError('Invalid data format')

        header_byte = bs[:bits_per_byte]
        bs = bs[bits_per_byte:]

        gaps = header_byte[:3].uint
        is_dirty = header_byte[3]
        special = header_byte[4:].uint

        if gaps > 0:
            logging.info('Adding gap of size %d', gaps)
            result += BitArray(uint=0, length=gaps * bits_per_byte)

        if is_dirty:
            logging.info('Adding offset byte with bit @ %d', special)
            end_bits = bits_per_byte - special - 1

            result += BitArray(uint=1, length=bits_per_byte - end_bits)

            if end_bits > 0:
                result += BitArray(uint=0, length=end_bits)
        else:
            logging.info('Adding %d literal bytes', special)
            lit_bits = special * bits_per_byte

            if len(bs) < lit_bits:
                raise ValueError('Invalid data format')

            result += bs[:lit_bits]
            bs = bs[lit_bits:]

    return result
