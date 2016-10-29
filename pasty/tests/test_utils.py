import unittest

from pasty import utils


class BaseConverterTestCase(unittest.TestCase):
    base62_fixtures = [
        (0, '0'),
        (10, 'A'),
        (61, 'z'),
        (62, '10'),
        (-1, '-1'),
        (-10, '-A'),
        (-61, '-z'),
        (-62, '-10'),
    ]

    def test_base62_encode(self):
        for value, expected in self.base62_fixtures:
            result = utils.base62.encode(value)

            # If this was Py3 we could use self.subTest(value, expected).
            self.assertEqual(result, expected)

    def test_base62_decode(self):
        for expected, value in self.base62_fixtures:
            result = utils.base62.decode(value)

            self.assertEqual(result, expected)

    def test_base62_base(self):
        self.assertEqual(utils.base62.base, 62)
