import logging
import os

from argparse import ArgumentParser

from lib.solution import create_index, compress_index


def get_basename(path: str) -> str:
    '''
    Args:
        path: The path to process.

    Returns:
        ``path`` stripped of any parent directories.
    '''

    return os.path.split(path)[1]


def process_args():
    '''
    Process the command line arguments using the ``argparse`` library.

    Returns:
        The environment given by ``ArgumentParser.parse_args()``.
    '''

    parser = ArgumentParser(description='Index and compress data files.')

    parser.add_argument('data_file', type=str,
                        help='File containing data to be indexed.')
    parser.add_argument('output_path', type=str, default='.',
                        help='Path to store resulting files in (default: .)')
    parser.add_argument('--word-size', type=int, dest='word_size',
                        help='The word size for compression, if applicable.')
    parser.add_argument('--sort', dest='sort_data', action='store_true',
                        help='Whether or not to sort the data file.')

    algos = parser.add_mutually_exclusive_group(required=True)
    logs = parser.add_argument_group(title='Debugging')

    algos.add_argument('--wah', dest='method', action='store_const',
                       const='WAH', help='Word-aligned hybrid compression')
    algos.add_argument('--bbc', dest='method', action='store_const',
                       const='BBC', help='Byte-aligned bitmap compression')

    logs.add_argument('--log-level', type=str, dest='log_level',
                      default='WARNING', help='Log level (default: WARNING; '
                      'see logging.setLevel())')
    logs.add_argument('--log-file', type=str, dest='log_file',
                      help='Output logs to the given file instead of stdout.')

    return parser.parse_args()


def main():
    '''
    Run the command-line interface for the compression algorithms.
    '''

    args = process_args()

    logging.basicConfig(level=args.log_level,
                        filename=args.log_file,
                        filemode='w')

    data_file = args.data_file
    output_path = args.output_path
    sort_data = args.sort_data
    method = args.method
    word_size = args.word_size

    logging.debug('Data file: {}'.format(data_file))
    logging.debug('Compression method: {}'.format(method))
    logging.debug('Word size: {}'.format(word_size))
    logging.debug('Sort data: {}'.format(sort_data))

    idx_file = create_index(data_file,
                            os.path.join(output_path, get_basename(data_file)),
                            sort_data)
    logging.info('Index file written to {}'.format(idx_file))

    cmp_file = compress_index(idx_file, output_path, method, word_size)
    logging.info('Compressed file written to {}'.format(cmp_file))


if __name__ == '__main__':
    main()
