import unittest

from bokeh.palettes import Spectral10, interp_palette

from hsd_constants import PALETTE, palette_for


class TestPaletteFor(unittest.TestCase):
    def test_ten_or_fewer_keeps_spectral10(self):
        self.assertIs(palette_for(0), PALETTE)
        self.assertIs(palette_for(1), PALETTE)
        self.assertIs(palette_for(10), PALETTE)
        self.assertEqual(palette_for(10), Spectral10)

    def test_more_than_ten_interpolates_spectral10(self):
        colors = palette_for(11)
        expected = interp_palette(list(Spectral10), 11)

        self.assertEqual(len(colors), 11)
        self.assertEqual(colors, expected)
        self.assertEqual(colors[0], Spectral10[0])
        self.assertEqual(colors[-1], Spectral10[-1])
        self.assertNotIn('#ffffbf', [c.lower() for c in colors])

    def test_sixteen_stays_on_the_spectral10_ramp(self):
        colors = palette_for(16)

        self.assertEqual(len(colors), 16)
        self.assertEqual(colors[0], Spectral10[0])
        self.assertEqual(colors[-1], Spectral10[-1])
        self.assertEqual(colors, interp_palette(list(Spectral10), 16))


if __name__ == '__main__':
    unittest.main()
