import itertools as it
import unittest as ut

from lib.bitstring import BitString


BS = BitString


class TestBS(ut.TestCase):
    def test_init(self):
        '''
        Test ``BitString.__init__()``
        '''

        for i in range(0, 1000):
            self.assertEqual(len(BS(i, 0)), 0)
            self.assertEqual(str(BS(i, 0)), '')

        self.assertEqual(len(BS(0b11001, 5)), 5)
        self.assertEqual(str(BS(0b11001, 5)), '11001')

        self.assertEqual(len(BS(0b11001, 2)), 2)
        self.assertEqual(str(BS(0b11001, 2)), '01')

        self.assertEqual(str(BS('0101')), '0101')
        self.assertEqual(str(BS([0, 1, 0, 1])), '0101')
        self.assertEqual(str(BS([False, True, False, True])), '0101')

        s = '010101'
        b = BitString(s)
        c = BitString(b)

        c[0] = 1

        self.assertNotEqual(b, c)
        self.assertEqual(len(b), len(c))
        self.assertEqual(str(b), s)
        self.assertEqual(str(c), '1' + s[1:])

        try:
            a = BS(0b0, -1)
            self.assertTrue(False)
        except Exception:
            pass

    def test_eq(self):
        '''
        Test ``BitString.__eq__()``
        '''

        for i in range(0, 500):
            for j in range(0, 500):
                a = BS(i, j)
                b = BS(i-1, j+1)

                self.assertEqual(a, a)
                self.assertNotEqual(a, b)
                self.assertNotEqual(b, a)

    def test_str(self):
        '''
        Test ``BitString.__str__()``
        '''

        for i in range(0, 1000):
            self.assertEqual(str(BS(i, 0)), '')

        self.assertEqual(str(BS(0b0, 1)), '0')
        self.assertEqual(str(BS(0b1, 1)), '1')

        self.assertEqual(str(BS(0b00, 2)), '00')
        self.assertEqual(str(BS(0b01, 2)), '01')
        self.assertEqual(str(BS(0b10, 2)), '10')
        self.assertEqual(str(BS(0b11, 2)), '11')

        self.assertEqual(str(BS(0b000, 3)), '000')
        self.assertEqual(str(BS(0b001, 3)), '001')
        self.assertEqual(str(BS(0b010, 3)), '010')
        self.assertEqual(str(BS(0b011, 3)), '011')
        self.assertEqual(str(BS(0b100, 3)), '100')
        self.assertEqual(str(BS(0b101, 3)), '101')
        self.assertEqual(str(BS(0b110, 3)), '110')
        self.assertEqual(str(BS(0b111, 3)), '111')

        self.assertEqual(str(BS(0b0110001111000001, 16)), '0110001111000001')

    def test_add(self):
        '''
        Test ``BitString.__add__()``
        '''

        a = BS(0b110, 3)
        b = BS(0b001, 3)

        self.assertEqual(len(a + b), 6)
        self.assertEqual(str(a + b), '110001')

    def test_shift(self):
        '''
        Test ``BitString.__lshift__()`` and ``BitString.__rshift__()``
        '''

        self.assertEqual(BS(0b1, 0) << 5, BS(0b00000, 5))
        self.assertEqual(BS(0b1, 1) << 5, BS(0b100000, 6))
        self.assertEqual(BS(0b1010, 4) << 2, BS(0b101000, 6))

        self.assertEqual(BS(0b1, 0) >> 5, BS(0b0, 0))
        self.assertEqual(BS(0b1, 1) >> 5, BS(0b0, 0))
        self.assertEqual(BS(0b1000, 4) >> 2, BS(0b10, 2))

    def test_slice(self):
        '''
        Test ``BitString.__getitem__()`` with slices
        '''

        s = '0110100'
        b = BS.from_iter(s)

        indices = it.chain(range(0, len(b) + 5), range(-len(b) - 5, 0))
        steps = range(1, len(b))

        for i, j, k in it.product(indices, indices, steps):
            self.assertEqual(str(b.slice(start=i)), s[i:])
            self.assertEqual(str(b[i:]), s[i:])

            self.assertEqual(str(b.slice(stop=j)), s[:j])
            self.assertEqual(str(b[:j]), s[:j])

            self.assertEqual(str(b.slice(start=i, step=k)), s[i::k])
            self.assertEqual(str(b[i:j]), s[i:j])

            self.assertEqual(str(b.slice(start=i, step=k)), s[i::k])
            self.assertEqual(str(b[i::k]), s[i::k])

            self.assertEqual(str(b.slice(stop=j, step=k)), s[:j:k])
            self.assertEqual(str(b[:j:k]), s[:j:k])

            self.assertEqual(str(b.slice(i, j, k)), s[i:j:k])
            self.assertEqual(str(b[i:j:k]), s[i:j:k])


if __name__ == '__main__':
    ut.main()
