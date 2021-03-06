'''
Command-line interface for compression algorithms. Run
``python main.py --help`` for program usage.
'''

import logging
import os
import sys

from argparse import ArgumentParser
from bitstring import BitArray

import lib.wah as wah
import lib.bbc as bbc


def _process_args():
    '''
    Process the command line arguments using the ``argparse`` library.

    Returns:
        The environment given by ``ArgumentParser.parse_args()``.
    '''

    parser = ArgumentParser(description='Index and compress data files.')

    parser.add_argument('--word-size', type=int, dest='word_size', default=8,
                        help='The word size for compression, if applicable '
                        '(default: 8)')

    algos = parser.add_mutually_exclusive_group(required=True)
    logs = parser.add_argument_group(title='debugging')

    algos.add_argument('--wah', dest='algorithm', action='store_const',
                       const='WAH', help='Word-aligned hybrid compression')
    algos.add_argument('--bbc', dest='algorithm', action='store_const',
                       const='BBC', help='Byte-aligned bitmap code '
                       'compression')

    logs.add_argument('--log-level', type=str, dest='log_level',
                      default='WARNING', help='Log level (default: WARNING; '
                      'see logging.setLevel())')
    logs.add_argument('--log-file', type=str, dest='log_file',
                      help='Output logs to the given file instead of stdout')

    return parser.parse_args()


def main():
    '''
    Run the command-line interface for the compression algorithms.
    '''

    args = _process_args()

    logging.basicConfig(level=args.log_level,
                        filename=args.log_file,
                        filemode='w')

    data = BitArray(bytes=sys.stdin.buffer.read().strip())

    if args.algorithm == 'WAH':
        compressed, final_length = wah.compress(data, args.word_size)
        logging.info('Bits used in final word: %d', final_length)
    elif args.algorithm == 'BBC':
        compressed = bbc.compress(data)
    else:
        raise NotImplementedError(f'Unrecognized algorithm: {args.algorithm}')

    sys.stdout.buffer.write(compressed.bytes)


if __name__ == '__main__':
    main()
