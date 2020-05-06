'''
Contains the implementation of the word-aligned hybrid (WAH) compression
algorithm, in addition to WAH-related functions.
'''

import logging

from bitstring import BitArray
from lib.compression import CompressionBase


def run_length(bs: BitArray, word_size: int) -> int:
    '''
    Args:
        bs: the string to analyze.
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
        bs: the string to analyze.
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


def encode_literal(bs: str, word_size: int):
    '''
    Encode the next ``(word_size - 1)`` bits as a literal, padding the right
    with zeroes as needed.

    Args:
        bs: the string to analyze.
        word_size: the WAH word size.

    Returns:
        A tuple ``(tail, encoded_literal)``, where ``encoded_literal`` is a
        word encoding the next ``(word_size - 1)``-bit literal from ``bs``,
        and ``tail`` is the remainder of ``bs`` with the literal removed.
        If there are less than ``(word_size - 1)`` bits remaining in ``bs``,
        ``literal`` is padded with zeroes on the right.
    '''

    section_size = word_size - 1
    literal = bs[:section_size]

    # format string is ugly, but all this does is create a string beginning
    # with 0, followed by the literal padded to become exactly one word long
    encoded_literal = BitArray(uint=0, length=1)
    encoded_literal += BitArray(uint=literal.uint, length=section_size)

    return bs[section_size:], encoded_literal


class WAH(CompressionBase):
    '''
    WAH algorithm implementation. The primary difference between this
    implementation and the WAH patent's algorithm description is that literals
    smaller than the word size are encoded by storing the literal in the most
    significant bits of the output word, then padding the right with zeroes.
    '''

    @staticmethod
    def compress(bs, word_size=8):
        logging.info('WAH - compressing %d bits', len(bs))
        logging.info('Word size: %d', word_size)
        logging.debug('Bits: %s', bs.bin)

        section_size = word_size - 1
        result = BitArray()

        while len(bs) > 0:
            run_count = run_length(bs, word_size)

            if run_count == 0:
                bs, next_word = encode_literal(bs, word_size)
                logging.info('Found literal')
                logging.debug('Literal: %s', next_word.bin)
            else:
                bs, next_word = encode_run(bs, word_size)
                logging.info('Found run of size %d', run_count)

            logging.debug('Next compressed word: %s', next_word.bin)
            result += next_word

        logging.info('Compressed bit count: %d', len(result))
        logging.debug('Compressed bits: %s', result.bin)

        return result
