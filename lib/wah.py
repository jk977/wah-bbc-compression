'''
Contains the implementation of the WAH algorithm, in addition to WAH-related
functions.
'''

import logging

from typing import Final, Optional, Tuple

from lib.bitstring import BitString
from lib.compression import CompressionBase


def run_length(bs: BitString, word_size: int) -> int:
    '''
    Args:
        bs: the BitString to analyze.
        word_size: the WAH word size.

    Returns:
        the number of run sections at the beginning of the bitstring. Note
        that a single word can encode up to ``2**(word_size - 2) - 1`` runs.
        If the run is too long to be encoded in a single word, the maximum
        possible length is returned.
    '''

    section_size: Final = word_size - 1
    run_bits: Final = bs.run_length()

    if run_bits < section_size:
        return 0

    run_words: Final = run_bits // section_size
    max_run_words: Final = 2**(section_size - 1) - 1

    return min(max_run_words, run_words)


def encode_run(bs: BitString, word_size: int) \
        -> Tuple[BitString, BitString]:
    '''
    Encode the run at the beginning of ``bs``. Assumes that a run is present,
    and that the run's length is in the range ``(word_size - 1)`` to
    ``(word_size - 1) * (2**(word_size - 2) - 1)``.

    Args:
        bs: the BitString to analyze.
        word_size: the WAH word size.

    Returns:
        A tuple ``(tail, encoded_run)``, where ``tail`` is the remainder of
        ``bs`` with ``encoded_run`` removed.
    '''

    runs: Final = run_length(bs, word_size)
    section_size: Final = word_size - 1

    # store length in the least significant bits of resulting
    # word, set the first bit to 1 to signify a run, and set
    # the second bit to the type of run.
    result = BitString(runs, word_size)
    result[0] = 1
    result[1] = bs[0]

    logging.debug('Encoded {}-run of {} words'.format(bs[0], runs))

    return bs[section_size * runs:], result


def encode_literal(bs: BitString, word_size: int) \
        -> Tuple[BitString, BitString]:
    '''
    Encode the next ``(word_size - 1)`` bits as a literal, padding the right
    with zeroes as needed.

    Args:
        bs: the BitString to analyze.
        word_size: the WAH word size.

    Returns:
        A tuple ``(tail, literal)``, where ``literal`` is the next literal
        from ``bs`` of length ``(word_size - 1)``, and ``tail`` is the
        remainder of ``bs`` with the literal removed. If there are less than
        ``(word_size - 1)`` bits remaining in ``bs``, ``literal`` is padded
        with zeroes on the right.
    '''

    section_size: Final = word_size - 1

    # set the first bit to 0, then add the literal
    header = BitString(0b0, 1)
    literal = BitString(bs[0:section_size])

    # pad the right with zeroes if literal is too short
    literal <<= section_size - len(literal)

    return bs[section_size:], header + literal


class WAH(CompressionBase):
    '''
    WAH algorithm implementation. The primary difference between this
    implementation and the WAH patent's algorithm description is that literals
    smaller than the word size are encoded by storing the literal in the most
    significant bits of the output word, then padding the right with zeroes.
    '''

    @staticmethod
    def compress(bs, word_size=8):
        if not isinstance(bs, BitString):
            bs = BitString(bs)

        logging.info('Compressing {} bits with WAH '
                     '(word size: {})'.format(len(bs), word_size))
        logging.debug('Bits: {}'.format(bs))

        section_size: Final = word_size - 1
        result = BitString()

        input_length: Final = len(bs)
        run_count = 0
        lit_count = 0

        while len(bs) > 0:
            current_run_count = run_length(bs, word_size)

            if current_run_count == 0:
                bs, next_word = encode_literal(bs, word_size)
                lit_count += 1
            else:
                bs, next_word = encode_run(bs, word_size)
                logging.info('Found run of size {}'.format(current_run_count))
                run_count += 1

            logging.debug('Next compressed word: {}'.format(next_word))
            logging.debug('Remaining bits: {}'.format(bs))
            result += next_word

        logging.info('Run count: {}'.format(run_count))
        logging.info('Literal count: {}'.format(lit_count))
        logging.info('Compressed bit count: {}'.format(len(result)))

        ratio = input_length / len(result) if len(result) > 0 else 'inf'
        logging.info('Compression ratio: {}'.format(ratio))

        return result
