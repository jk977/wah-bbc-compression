'''
Contains BitString implementation used to represent a string of bits in
compression algorithms.
'''

from typing import Any, Final, Optional, Tuple
from lib.util import all_bits


class BitString:
    '''
    Represents a string of bits. Although the assignment description
    didn't require bitwise operations to be used, this class was an
    exercise in using magic methods and bitwise operations in Python.

    The behavior of the constructor depends on the arguments provided.

    Args:
        args: If ``len(args)`` is 0, an empty BitString is created.

              If ``len(args)`` is 1, the parameter is read as an ASCII string
              of bits, or is passed to ``from_iter()`` if not a string.

              If ``len(args)`` is 2, a BitString of size ``args[1]`` is created
              from ``args[0]``, where ``args[0]`` is either an object
              compatible with ``from_iter()`` or an ``int``, representing a raw
              string of bits. If there are more bit-like objects in ``args[0]``
              than the given length, the first ``args[1]`` bits are taken from
              ``args[0]``.

    Attributes:
        bits (int): The raw bits of the BitString.
        length (int): The length of the BitString.
    '''

    def __init__(self, *args):
        # NOTE: This could be implemented in a cleaner way with keyword
        #       arguments, but as a mostly-internal structure, this is
        #       sufficient and leads to less boilerplate ``key=val`` parameters

        if len(args) > 2:
            raise TypeError('constructor takes at most 2 arguments')
        elif len(args) == 2:
            bits = args[0]
            length = int(args[1])
        elif len(args) == 1:
            bits = args[0]
            length = len(bits)
        else:
            bits = 0
            length = 0

        if length is not None and length < 0:
            raise ValueError('cannot have negative BitString length')

        if isinstance(bits, str):
            if len(bits) == 0:
                self.bits = 0
                self.length = 0
            else:
                self.bits = int(bits, 2)
                self.length = len(bits)
        elif isinstance(bits, self.__class__):
            self.bits = bits.bits
            self.length = len(bits)
        elif isinstance(bits, int):
            self.bits = bits
            self.length = length
        else:
            result = self.__class__.from_iter(bits, length)
            self.bits = result.bits
            self.length = result.length

        if len(args) == 2:
            # if length was specified, clear the unused bits
            self.bits &= all_bits(length)
            self.length = length

    @classmethod
    def from_iter(cls, bits, length=-1):
        '''
        Creates a BitString from an iterable object containing int-like
        values.

        Args:
            bits: an iterable object containing int-like values. 0-like values
                  are considered an unset bit, and any other value is
                  considered a set bit.
            length: the length of ``bits``. If negative or not provided, all of
                    ``bits`` is used.

        Returns:
            a BitString constructed from ``bits``.

        Raises:
            TypeError: if ``bits`` is not iterable.
            ValueError: if ``bits`` contains an object that is not int-like.
        '''

        buf = 0
        count = 0

        for bit in bits:
            if count == length:
                break

            bit = 0 if int(bit) == 0 else 1
            buf = (buf << 1) | bit
            count += 1

        return cls(buf, count)

    def __len__(self):
        '''
        Get the number of bits in the BitString.
        '''

        return self.length

    def _absolute_index(self, i: int):
        '''
        Args:
            i: the index to convert.

        Returns:
            the positive equivalent of the index ``i``. If ``i`` was already
            positive, ``i`` will be returned. If ``i`` was negative, ``i`` is
            taken as an offset from the end of the BitString.
        '''

        if i < 0:
            return len(self) + i
        else:
            return i

    def _normalize_slice(self,
                         start: Optional[int] = None,
                         stop: Optional[int] = None,
                         step: Optional[int] = None) \
            -> Tuple[int, int, int]:
        '''
        Makes sure all values are not None, and that ``start`` and ``stop`` are
        within the BitString bounds. Any negative indices are converted to
        positive.

        Args:
            start: starting index to slice from. Default: 0.
            stop: the index to stop before when slicing. Default: len(self).
            step: the number of elements to skip. Default: 1.

        Returns:
            a tuple (``new_start``, ``new_stop``, ``new_step``).

        Raises:
            NotImplementedError: if a negative ``step`` is given.
            ValueError: if a step of ``zero`` is given.
        '''

        start = 0 if start is None else self._absolute_index(start)
        stop = len(self) if stop is None else self._absolute_index(stop)
        step = 1 if step is None else self._absolute_index(step)

        if step < 0:
            raise NotImplementedError('negative step')
        elif step == 0:
            raise ValueError('slice step cannot be zero')

        start = max(0, start)
        stop = min(stop, len(self))

        return start, stop, step

    def _get_consecutive_bits(self,
                              start: Optional[int] = None,
                              stop: Optional[int] = None):
        '''
        Get the BitString between ``start`` and ``stop`` indices. Behaves the
        same as Pythonic array slicing with ``step`` == 1.

        Args:
            start: starting index to slice from. Default: 0.
            stop: the index to stop before when slicing. Default:
                  ``len(self)``.

        Returns:
            the BitString between ``start`` and ``stop`` indices.

            If ``stop`` < ``start``, if ``start`` is after the end of the
            BitString, or if ``stop`` is negative, returns an empty BitString.
        '''

        start, stop, _ = self._normalize_slice(start, stop, 1)

        if start == 0 and stop == len(self):
            # no bit operations necessary; copy everything
            return self.__class__(self)
        elif start >= stop or start >= len(self) or stop <= 0:
            return self.__class__()

        # align the range bits to the right stop of the buffer
        bits: Final = self.bits >> self._right_align_index(stop - 1)
        length: Final = stop - start

        return self.__class__(bits & all_bits(length), length)

    def slice(self,
              start: Optional[int] = None,
              stop: Optional[int] = None,
              step: Optional[int] = None):
        '''
        Get the BitString between the start and stop indices, inclusive,
        with the given step size.

        Behaves the same as Pythonic array slicing, but with more constraints
        on the start/stop/step values and different negative value behavior.

        Args:
            start: the starting slice index.
            stop: the index of the bit to stop before.

        Returns:
            if ``stop`` < ``start``, if ``start`` is after the end of the
            BitString, or if ``stop`` is negative, returns an empty BitString.

        Raises:
            NotImplementedError: if a negative ``step`` is given.
        '''

        start, stop, step = self._normalize_slice(start, stop, step)

        if step == 1:
            return self._get_consecutive_bits(start, stop)
        elif start >= stop or start >= len(self) or stop <= 0:
            return self.__class__()

        slice_span = stop - start
        slice_count = 1 + (slice_span - 1) // step
        bits = BitString(0, slice_count)

        for dest, src in enumerate(range(start, stop, step)):
            bits[dest] = self[src]

        return bits

    def _right_align_index(self, i: int):
        '''
        Convert the given left-aligned index to a right-aligned one.

        Args:
            i: the index to convert.

        Returns:
            the offset (from the right) of the bit at ``i`` (from the left).
        '''

        return len(self) - 1 - i

    def __getitem__(self, key):
        '''
        Args:
            key: either the index of the bit to retrieve, or a slice.
                 Indexing begins from the left -- the BitString can be thought
                 of as an array of bits ``b[0]``, ``b[1]``, ``b[2]``, ...

        Returns:
            1 if the bit at the given index is set, 0 if not, or a
            BitString in the specified range if ``key`` is a slice object.
        '''

        if isinstance(key, slice):
            return self.slice(key.start, key.stop, key.step)
        elif key < 0 or key >= len(self):
            raise IndexError('index out of range')

        bit_at_key = 1 << self._right_align_index(key)
        return 1 if self.bits & bit_at_key else 0

    def __setitem__(self, i: int, flag):
        '''
        Sets the bit at the given index on if flag is truthy, or off
        if flag is falsey.

        Args:
            i: the index to set.
            flag: a bool-like value to set the bit to.
        '''

        if i < 0 or i >= len(self):
            raise IndexError('index out of range')

        bit_at_i = 1 << self._right_align_index(i)

        if flag:
            self.bits |= bit_at_i
        else:
            self.bits &= all_bits(len(self)) & ~bit_at_i

    def __iter__(self):
        '''
        Yields:
            Each bit of the BitString in order.
        '''

        for i in range(0, len(self)):
            yield self[i]

    def __str__(self):
        '''
        Returns:
            the BitString as a string exactly len(self) long containing only
            zeroes and ones.
        '''

        if len(self) > 0:
            return '{{:0{}b}}'.format(len(self)).format(self.bits)
        else:
            return ''

    def __eq__(self, other):
        '''
        Args:
            other: a BitString or other object implementing __len__ with a
                   ``bits`` attribute.
        Returns:
            true if ``self`` equals ``other``, False otherwise.
        '''

        return len(self) == len(other) and self.bits == other.bits

    def __add__(self, other):
        '''
        Args:
            other: the BitString to add to self.

        Returns:
            the concatenation of the bits in ``self`` with the bits in
            ``other``, with the length adjusted appropriately.
        '''

        bits = (self.bits << len(other)) | other.bits

        return self.__class__(bits, len(self) + len(other))

    def __iadd__(self, other):
        '''
        Same as __add__ but in-place.
        '''

        self.bits <<= len(other)
        self.bits |= other.bits
        self.length += len(other)

        return self

    def __lshift__(self, count):
        '''
        Args:
            count: the number of times to shift the bits to the left.

        Returns:
            the BitString represented by ``self``, shifted left by ``count``
            bits. The length of the result is increased by ``count``.
        '''

        return self.__class__(self.bits << count, len(self) + count)

    def __ilshift__(self, count):
        '''
        Same as __lshift__ but in-place
        '''

        self.bits <<= count
        self.length += count
        return self

    def __rshift__(self, count):
        '''
        Args:
            count: the number of times to shift the bits to the right.

        Returns:
            the BitString represented by ``self``, shifted right by ``count``
            bits.  The length of the result is decreased by ``count``, and the
            rightmost ``count`` bits are truncated.
        '''

        return self.__class__(self.bits >> count, max(0, len(self) - count))

    def __irshift__(self, count):
        '''
        Same as __rshift__ but in-place.
        '''

        self.bits >>= count
        self.length = max(0, len(self) - count)
        return self

    def __invert__(self):
        '''
        Returns:
            a BitString with the same length as self but with all bits flipped.
        '''

        return self.__class__(~self.bits, len(self))

    def run_length(self, flag: Optional[Any] = None):
        '''
        Args:
            flag: the type of run to count. If None, defaults to the first
                  bit in self.

        Returns:
            the length of the first run of bits in self. If ``flag`` is
            specified, the length is 0 if the first bit is the opposite of
            ``flag``.
        '''

        if flag is None and len(self) > 0:
            flag = self[0]

        if len(self) == 0 or bool(self[0]) != bool(flag):
            return 0

        bit_len = (~self if flag else self).bits.bit_length()
        return len(self) - bit_len
