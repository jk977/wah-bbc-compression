'''
Command-line interface for compression algorithms. Run
``python main.py --help`` for program usage.
'''

import logging
import os
import sys

from argparse import ArgumentParser

from lib.wah import WAH
from lib.bbc import BBC


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

    algos.add_argument('--wah', dest='compressor', action='store_const',
                       const=WAH, help='Word-aligned hybrid compression')
    algos.add_argument('--bbc', dest='compressor', action='store_const',
                       const=BBC, help='Byte-aligned bitmap compression')

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

    data = sys.stdin.read().strip()
    compressed = args.compressor.compress(data, word_size=args.word_size)

    print(compressed)


if __name__ == '__main__':
    main()
