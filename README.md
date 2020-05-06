# WAH/BBC Compression

## About

This project implements the word-aligned hybrid (WAH) compression algorithm and a modified version of the byte-aligned bitmap compression (BBC) algorithm.

## Requirements

* Python 3.6 or above
* The [`bitstring`](https://pypi.org/project/bitstring/) module

## Usage

The source code for the compression algorithms are located in `lib/wah.py` and `lib/bbc.py`. To import these into a Python script, include the following lines:

> `from lib.wah import WAH`

> `from lib.bbc import BBC`

`WAH` and `BBC` both have a `compress()` method that takes a `BitArray` containing the data to compress and returns the compressed `BitArray`. There is a command-line interface implemented in `compress.py`, which also serves as an example of how the methods in the aforementioned source files can be used. For `compress.py` usage, run `python compress.py --help`.
