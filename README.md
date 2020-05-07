# WAH/BBC Compression

## About

This project implements the word-aligned hybrid (WAH) compression algorithm and a modified version of the byte-aligned bitmap code (BBC) compression algorithm.

## Requirements

* Python 3.6 or above
* The [`bitstring`](https://pypi.org/project/bitstring/) module

## Usage

The source code for the compression algorithms are located in `lib/wah.py` and `lib/bbc.py`. See Examples for examples on using these modules.

The `wah` and `bbc` modules both have `compress()` and `decompress()` methods that take a `BitArray` containing the data to compress and returns the compressed `BitArray`. The `wah` module also requires an additional parameter: the word size to be used in the compression algorithm. See the module's documentation for more details.

There is a command-line interface for the `compress()` methods implemented in `compress.py`, which also serves as an example of how the methods in the aforementioned source files can be used. For `compress.py` usage, run `python compress.py --help`.

## Tests

Unit tests are present in `test_bbc.py` and `test_wah.py`, testing WAH and BBC compression, respectively.

The compression algorithms may also be fuzzed using `fuzz.py`. This module has functions for generating random strings and passing them to the algorithm implementations. If ran as a standalone script, it fuzzes WAH and BBC in two phases: first using a high volume of short inputs, then using a low volume of long inputs. All WAH word sizes between 2 and 64 (inclusive) are fuzzed.

## Examples

These examples build off of the following imports:

```
>>> from bitstring import BitArray
>>> import lib.wah as wah
>>> import lib.bbc as bbc
```

### WAH

To compress a string:

```
>>> s = 'Hello, world!'
>>> bs = BitArray(bytes=s.encode(encoding='ascii'))
>>> compressed, final_bits = wah.compress(bs, word_size=8)
>>> print(compressed.bin)
001001000001100100101101010001100110001100111100010110000010000000111011010110110110111000100110011000110001000001000010
```

To decompress `compressed`, `final_bits` is required since it tells the algorithm where to stop on the last compressed byte:

```
>>> decompressed = wah.decompress(compressed, final_bits, word_size)
>>> print(decompressed.bytes)
b'Hello, world!'
```

### BBC

To compress a string:

```
>>> s = 'Goodbye, world!'
>>> bs = BitArray(bytes=s.encode(encoding='ascii'))
>>> compressed = bbc.compress(bs)
>>> print(compressed.bin)
0000110101001000011001010110110001101100011011110010110000100000011101110110111101110010011011000110010000100001
```

To decompress `compressed`:

```
>>> decompressed = bbc.decompress(compressed)
>>> print(decompressed.bytes)
b'Goodbye, world!'
```

## Notes

These compression algorithms are best used on binary data rather than plain text. Because plain text is unlikely to have any consecutive zero-bytes (`0b00000000`), one-bytes (`0b11111111`), or bytes with a single bit set, the performance of these algorithms will likely be very poor on these files. This can be tested by comparing the compression ratio of a plain-text file, such as `compress.py`, to the compression ratio of a binary file, such as `/bin/sh`.
