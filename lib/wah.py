'''
Contains the implementation of the word-aligned hybrid (WAH) compression
algorithm, in addition to WAH-related functions.

The primary difference between this implementation and the WAH patent's
algorithm description is that literals smaller than the word size are encoded
by storing the literal in the most significant bits of the output word, then
padding the right with zeroes.
'''

import logging

from bitstring import BitArray


def run_length(bs: BitArray, word_size: int) -> int:
    '''
    Args:
        bs: the bits to analyze.
        word_size: the WAH word size.

    Returns:
        the number of run sections at the beginning of the bitstring. Note
        that a single word can encode up to ``2**(word_size - 2) - 1`` runs.
        If the run is too long to be encoded in a single word, the maximum
        possible length is returned.
    '''

    if len(bs) == 0:
        return 0

    section_size = word_size - 1
    toggle_bit = BitArray(bool=not bs[0])
    bit_idx = bs.find(toggle_bit)
    run_bits = bit_idx[0] if bit_idx else len(bs)

    if run_bits < section_size:
        return 0

    run_words = run_bits // section_size
    max_run_words = 2**(section_size - 1) - 1

    return min(max_run_words, run_words)


def encode_run(bs: BitArray, word_size: int):
    '''
    Encode the run at the beginning of ``bs``. Assumes that a run is present,
    and that the run's length is in the range ``(word_size - 1)`` to
    ``(word_size - 1) * (2**(word_size - 2) - 1)``.

    Args:
        bs: the bits to analyze.
        word_size: the WAH word size.

    Returns:
        A tuple ``(tail, encoded_run)``, where ``tail`` is the remainder of
        ``bs`` with ``encoded_run`` removed.
    '''

    runs = run_length(bs, word_size)
    section_size = word_size - 1

    # store length in the least significant bits of resulting
    # word, set the first bit to 1 to signify a run, and set
    # the second bit to the type of run.
    result = BitArray(uint=1, length=1)
    result += bs[0:1]
    result += BitArray(uint=runs, length=section_size - 1)

    logging.debug('Encoded %d-run of %d words', bs[0], runs)
    return bs[section_size * runs:], result


def encode_literal(bs: BitArray, word_size: int):
    '''
    Encode the next ``(word_size - 1)`` bits as a literal, padding the right
    with zeroes as needed.

    Args:
        bs: the bits to analyze.
        word_size: the WAH word size.

    Returns:
        A tuple ``(tail, encoded_literal)``, where ``encoded_literal`` is a
        word encoding the next ``(word_size - 1)``-bit literal from ``bs``,
        and ``tail`` is the remainder of ``bs`` with the literal removed.
        If there are less than ``(word_size - 1)`` bits remaining in ``bs``,
        ``literal`` is padded with zeroes on the right.
    '''

    if len(bs) == 0:
        return bs, BitArray(uint=0, length=word_size)

    section_size = word_size - 1
    literal = bs[:section_size]

    # create a string beginning with 0, followed by the literal padded to
    # become exactly one word long
    encoded_literal = BitArray(uint=0, length=1)
    encoded_literal += literal

    if len(literal) < section_size:
        remaining_bits = section_size - len(literal)
        encoded_literal += BitArray(uint=0, length=remaining_bits)

    return bs[section_size:], encoded_literal


def compress(bs, word_size):
    '''
    Compress the given bits with WAH compression using the specified word
    size.

    Args:
        bs: the bits to compress.
        word_size: the word size used in the algorithm.

    Returns:
        a tuple ``(compressed, length)``, where ``compressed`` is the
        compressed ``bs`` and ``length`` is the number of bits used in the
        final word of ``compressed``. ``length`` is returned because the
        value is required when decompressing WAH-compressed data.
    '''

    if len(bs) == 0:
        raise ValueError('bs must have a length greater than 0')
    elif word_size <= 1:
        raise ValueError('word_size must be at least 2')

    logging.info('Compressing %d bits', len(bs))
    logging.info('Word size: %d', word_size)
    logging.debug('Bits: %s', bs.bin)

    section_size = word_size - 1
    result = BitArray()
    final_length = word_size

    while len(bs) > 0:
        run_count = run_length(bs, word_size)

        if run_count == 0:
            final_length = min(word_size, len(bs) + 1)
            bs, next_word = encode_literal(bs, word_size)
            logging.info('Found literal: %s', next_word.bin)
        else:
            bs, next_word = encode_run(bs, word_size)
            logging.info('Found run of size %d', run_count)

        logging.debug('Next compressed word: %s', next_word.bin)
        result += next_word

    logging.info('Compressed bit count: %d', len(result))
    logging.debug('Compressed bits: %s', result.bin)

    return result, final_length


def decompress(bs, final_length, word_size):
    '''
    Decompress the given WAH-compressed bits with the specified word size.
    This is the inverse of ``WAH.compress()``.

    Args:
        bs: the bits to decompress.
        word_size: the word size used.
        final_length: the number of bits used in the final word of ``bs``.
    '''

    if len(bs) == 0:
        raise ValueError('bs must have a length greater than 0')
    elif word_size <= 1:
        raise ValueError('word_size must be at least 2')
    elif not 1 <= final_length <= word_size:
        raise ValueError('final_length must be between 1 and word_size, '
                         'inclusive')

    result = BitArray()

    while len(bs) > 0:
        next_word = bs[:word_size]
        bs = bs[word_size:]

        logging.info('Decompressing word: %s', next_word.bin)
        is_run = next_word[0]

        if is_run:
            run_type = next_word[1]
            runs = next_word[2:].uint
            logging.info('Expanding %d-run of length %d', run_type, runs)

            section_size = word_size - 1
            result += [run_type] * section_size * runs
        else:
            if len(bs) > 0:
                # end isn't reached, so don't worry about trailing bits
                lit = next_word[1:]
            else:
                # final word is reached; only use first ``final_length`` bits
                lit = next_word[1:final_length]

            logging.info('Adding literal: %s', lit.bin)
            result += lit

    return result
