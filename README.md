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

`WAH` and `BBC` both have a `compress()` method that takes a string and returns an ASCII representation of the resulting binary string after compression.

There is also a command-line interface implemented in `main.py`, which also serves as an example of how the methods in `src/lib/solution.py` can be used.
