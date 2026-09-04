import os
import tempfile
import unittest

import pandas as pd

from homeschool_dashboard import generate_plots


REQUIRED_COLUMNS = ['Date', 'Start Time', 'End Time', 'Description']


def _write_workbook(path, sheets):
    with pd.ExcelWriter(path) as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)


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


if __name__ == '__main__':
    unittest.main()
