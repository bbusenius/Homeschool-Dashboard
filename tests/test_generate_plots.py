import os
import tempfile
import unittest

import pandas as pd

from homeschool_dashboard import generate_plots
from hsd_constants import PALETTE, palette_for


REQUIRED_COLUMNS = ['Date', 'Start Time', 'End Time', 'Description']


def _write_workbook(path, sheets):
    with pd.ExcelWriter(path) as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)


def _session(description='Work'):
    return pd.DataFrame(
        {
            'Date': ['2023-01-15'],
            'Start Time': ['9:00 AM'],
            'End Time': ['10:00 AM'],
            'Description': [description],
        }
    )


class TestGeneratePlotsEmptySheets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'Time-K.xlsx')

    def tearDown(self):
        self.tmp.cleanup()

    def test_skips_empty_class_tabs_and_uses_populated_ones(self):
        art = pd.DataFrame(columns=REQUIRED_COLUMNS + ['Grade', 'Name'])
        math = pd.DataFrame(
            {
                'Date': ['2023-01-15'],
                'Start Time': ['9:00 AM'],
                'End Time': ['10:00 AM'],
                'Description': ['Addition'],
                'Grade': ['Kindergarten'],
                'Name': ['Eliana'],
            }
        )
        _write_workbook(self.path, {'Art': art, 'Math': math})

        html = generate_plots([self.path])

        self.assertIn('"Math"', html)
        self.assertNotIn('"Art"', html)
        self.assertIn('Kindergarten', html)
        self.assertIn('Eliana', html)
        self.assertIn('&lt;strong&gt;1.0&lt;/strong&gt;', html)
        self.assertIn('hours of learning', html)

    def test_all_empty_class_tabs_render_an_empty_dashboard(self):
        art = pd.DataFrame(columns=REQUIRED_COLUMNS + ['Grade'])
        pe = pd.DataFrame(columns=REQUIRED_COLUMNS)
        _write_workbook(
            self.path, {'Art': art, 'Physical Education': pe}
        )

        html = generate_plots([self.path])

        self.assertIn('&lt;strong&gt;0&lt;/strong&gt;', html)
        self.assertIn('hours of learning', html)
        self.assertNotIn('"Art"', html)
        self.assertNotIn('"Physical Education"', html)

    def test_missing_required_headers_still_errors(self):
        notes = pd.DataFrame({'Foo': [1]})
        _write_workbook(self.path, {'Notes': notes})

        with self.assertRaises(KeyError) as ctx:
            generate_plots([self.path])

        message = str(ctx.exception)
        self.assertIn('Notes', message)
        self.assertIn('Time-K.xlsx', message)
        self.assertIn('Missing required column(s):', message)
        self.assertIn('date', message)
        self.assertIn('start time', message)
        self.assertIn('end time', message)

    def test_empty_sheet_does_not_consume_a_palette_color(self):
        empty = pd.DataFrame(columns=REQUIRED_COLUMNS)
        math = _session('Addition')
        math['Grade'] = ['Kindergarten']
        _write_workbook(self.path, {'Art': empty, 'Math': math})

        html = generate_plots([self.path])

        self.assertIn('"Math"', html)
        self.assertNotIn('"Art"', html)
        self.assertIn(PALETTE[0].lower(), html.lower())

    def test_empty_sheet_plus_ten_classes_keeps_spectral10(self):
        sheets = {'Empty': pd.DataFrame(columns=REQUIRED_COLUMNS)}
        sheets.update({f'Class{i:02d}': _session() for i in range(10)})
        _write_workbook(self.path, sheets)

        html = generate_plots([self.path])
        html_lower = html.lower()

        for i in range(10):
            self.assertIn(f'"Class{i:02d}"', html)
        self.assertNotIn('"Empty"', html)
        self.assertIn(PALETTE[0].lower(), html_lower)
        self.assertIn(PALETTE[-1].lower(), html_lower)
        self.assertNotIn(palette_for(11)[1].lower(), html_lower)

    def test_eleven_classes_interpolates_spectral10(self):
        names = [f'Class{i:02d}' for i in range(11)]
        sheets = {name: _session() for name in names}
        _write_workbook(self.path, sheets)

        html = generate_plots([self.path])
        html_lower = html.lower()
        colors = palette_for(11)

        for name in names:
            self.assertIn(f'"{name}"', html)
        self.assertEqual(len(colors), 11)
        self.assertIn(colors[1].lower(), html_lower)
        self.assertIn(colors[-1].lower(), html_lower)
        self.assertNotIn('#ffffbf', html_lower)


if __name__ == '__main__':
    unittest.main()

