import os
import tempfile
import unittest
from unittest import mock

import pandas as pd

import homeschool_dashboard
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


class TestGeneratePlotsReadingData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'Time-4.xlsx')
        books_dir = os.path.join(self.tmp.name, 'books')
        os.makedirs(books_dir)
        self.books_relpath = os.path.join('books', 'Reading-List.xlsx')
        books = pd.DataFrame(
            {
                'Title': ['Sample Title', 'Another Sample Title'],
                'Author': ['Sample Author', 'Another Author'],
                'Language': ['English', 'English'],
                'ISBN': ['', ''],
            }
        )
        _write_workbook(
            os.path.join(self.tmp.name, self.books_relpath),
            {'Sample Books': books},
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _reading_tab(self):
        df = pd.DataFrame(
            {
                'Date': ['2023-01-15', '2023-02-15'],
                'Start Time': ['9:00 AM', '9:00 AM'],
                'End Time': ['10:00 AM', '10:00 AM'],
                'Description': ['Reading', 'Reading'],
                'Grade': ['Grade 4', None],
                'Name': ['Alex', None],
                'Reading List': [self.books_relpath, None],
                'Reading Level': [3.2, 3.6],
            }
        )
        return df

    def _blank_reading_tab(self, description, reading_list=None):
        df = _session(description)
        df['Reading List'] = [reading_list]
        df['Reading Level'] = [None]
        return df

    def _assert_reading_widgets(self, html):
        # assertIn would dump the whole page on failure.
        for text in ('Sample Title', 'Sample Author', 'Sample Books'):
            self.assertTrue(text in html, f'booklist missing {text!r}')
        self.assertTrue('Reading Level' in html, 'reading level chart missing')

    def test_every_tab_has_reading_columns_but_only_middle_has_values(self):
        sheets = {
            'Art': self._blank_reading_tab('Drawing'),
            'Reading': self._reading_tab(),
            'Science': self._blank_reading_tab('Plants'),
        }
        _write_workbook(self.path, sheets)

        with mock.patch.object(
            homeschool_dashboard,
            'reading_list',
            wraps=homeschool_dashboard.reading_list,
        ) as spy:
            html = generate_plots([self.path])

        self._assert_reading_widgets(html)
        self.assertEqual(spy.call_count, 1)

    def test_later_blank_tabs_do_not_wipe_reading_data(self):
        sheets = {
            'Reading': self._reading_tab(),
            'Math': self._blank_reading_tab('Addition', reading_list='   '),
            'Science': self._blank_reading_tab('Plants'),
        }
        _write_workbook(self.path, sheets)

        html = generate_plots([self.path])

        self._assert_reading_widgets(html)

    def test_reading_columns_on_one_tab_only(self):
        sheets = {
            'Art': _session('Drawing'),
            'Reading': self._reading_tab(),
            'Science': _session('Plants'),
        }
        _write_workbook(self.path, sheets)

        html = generate_plots([self.path])

        self._assert_reading_widgets(html)

    def test_no_reading_columns_omits_reading_widgets(self):
        _write_workbook(self.path, {'Art': _session('Drawing')})

        html = generate_plots([self.path])

        self.assertFalse('Sample Title' in html, 'unexpected booklist')
        self.assertFalse('Reading Level' in html, 'unexpected reading level chart')


if __name__ == '__main__':
    unittest.main()

