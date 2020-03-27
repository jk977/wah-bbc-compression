'''
Contains the implementation of the word-aligned hybrid (WAH) compression
algorithm, in addition to WAH-related functions.
'''

import logging
from typing import Final, Tuple

from lib.compression import CompressionBase
from lib.util import binstr


def run_length(bs: str, word_size: int) -> int:
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

    section_size: Final = word_size - 1
    toggle_bit: Final = '0' if bs[0] == '1' else '1'
    bit_idx: Final = bs.find(toggle_bit)
    run_bits: Final = bit_idx if bit_idx >= 0 else len(bs)

    if run_bits < section_size:
        return 0

    run_words: Final = run_bits // section_size
    max_run_words: Final = 2**(section_size - 1) - 1

    return min(max_run_words, run_words)


def encode_run(bs: str, word_size: int) -> Tuple[str, str]:
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

    runs: Final = run_length(bs, word_size)
    section_size: Final = word_size - 1

    # store length in the least significant bits of resulting
    # word, set the first bit to 1 to signify a run, and set
    # the second bit to the type of run.
    encoded_runs: Final = binstr(runs, section_size - 1)
    result: Final = f'1{bs[0]}{encoded_runs}'
    logging.debug('Encoded %s-run of %d words', bs[0], runs)

    return bs[section_size * runs:], result


def encode_literal(bs: str, word_size: int) -> Tuple[str, str]:
    '''
    Encode the next ``(word_size - 1)`` bits as a literal, padding the right
    with zeroes as needed.

    Args:
        bs: the string to analyze.
        word_size: the WAH word size.

    Returns:
        A tuple ``(tail, literal)``, where ``literal`` is the next literal
        from ``bs`` of length ``(word_size - 1)``, and ``tail`` is the
        remainder of ``bs`` with the literal removed. If there are less than
        ``(word_size - 1)`` bits remaining in ``bs``, ``literal`` is padded
        with zeroes on the right.
    '''

    section_size: Final = word_size - 1
    literal: Final = bs[:section_size]

    # format string is ugly, but all this does is create a string beginning
    # with 0, followed by the literal padded to become exactly one word long
    word = f'0{{:<0{section_size}s}}'.format(literal)
    return bs[section_size:], word


class WAH(CompressionBase):
    '''
    WAH algorithm implementation. The primary difference between this
    implementation and the WAH patent's algorithm description is that literals
    smaller than the word size are encoded by storing the literal in the most
    significant bits of the output word, then padding the right with zeroes.
    '''

    @staticmethod
    def compress(bs, word_size=8):
        if not isinstance(bs, str):
            bs = str(bs)

        logging.info('WAH - compressing %d bits', len(bs))
        logging.info('Word size: %d', word_size)
        logging.debug('Bits: %s', bs)

        section_size: Final = word_size - 1
        result = ''

        while len(bs) > 0:
            run_count = run_length(bs, word_size)

            if run_count == 0:
                bs, next_word = encode_literal(bs, word_size)
                logging.info('Found literal')
                logging.debug('Literal: %s', next_word)
            else:
                bs, next_word = encode_run(bs, word_size)
                logging.info('Found run of size %d', run_count)

            logging.debug('Next compressed word: %s', next_word)
            result += next_word

        logging.info('Compressed bit count: %d', len(result))
        return result
