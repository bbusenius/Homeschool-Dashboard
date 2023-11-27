import os
import unittest
from datetime import datetime
from unittest.mock import patch

import pandas as pd
from bokeh.models import ColumnDataSource, DataTable, Div, RangeTool
from bokeh.models.glyphs import VBar
from bokeh.models.renderers import GlyphRenderer
from bokeh.plotting import figure
from constants import COLUMN_HEIGHT, PALETTE
from plot import barchart, curricula, days, donut, reading_level, reading_list


class Tests(unittest.TestCase):
    def setUp(self):
        self.labels = ['ClassA', 'ClassB', 'ClassC']
        self.data = [10, 15, 8]

        # Create a sample spreadsheet with two sheets and some book data
        self.path = 'test.xlsx'
        self.level = pd.Series([2.5, 3.0, 3.2, 3.5, 4.0])
        self.date = pd.Series(
            ["2023-01-01", "2023-02-01", "2023-03-01", "2023-04-01", "2023-05-01"],
            dtype="datetime64[ns]",
        )
        reading_list_1 = pd.DataFrame(
            {
                'title': [
                    'The Anti-Communist Manifesto',
                    'Basic Economics',
                    'The Rape of the Mind: The Psychology of Thought Control, Menticide, and Brainwashing',
                ],
                'author': ['Jesse Kelly', 'Thomas Sowell', 'Joost A.M. Meerloo'],
                'language': ['English', 'English', 'English'],
                'isbn': ['978-1668010877', '978-0465081387', '978-161427'],
                'level': ['Beginner', 'Advanced', 'Intermediate'],
            }
        )
        reading_list_2 = pd.DataFrame(
            {
                'title': [
                    'Jane and the King',
                    'Los Gemelos Tuttle y la Criatura de la Isla Jekyll',
                    'Los Gemelos Tuttle y la Regla de Oro',
                ],
                'author': ['Jenny Phillips', 'Connor Boyack', 'Connor Boyack'],
                'language': ['English', 'Spanish', 'Spanish'],
                'isbn': ['978-1951097493', '978-1943521159', '978-1943521159'],
            }
        )

        with pd.ExcelWriter(self.path) as writer:
            reading_list_1.to_excel(writer, sheet_name='Adults')
            reading_list_2.to_excel(writer, sheet_name='Kids')

    def test_barchart(self):

        plot = barchart(self.labels, self.data)

        # Check if the returned value is a Bokeh plot
        self.assertIsInstance(plot, figure)

        # Check some properties of the plot
        self.assertEqual(plot.title.text, 'Hours')
        self.assertEqual(plot.y_range.start, 0)
        self.assertEqual(plot.y_range.end, max(self.data))
        self.assertEqual(plot.legend.orientation, 'horizontal')
        self.assertEqual(plot.legend.location, 'top_center')

        # Check the presence of glyphs in the plot
        assert any(
            isinstance(renderer, GlyphRenderer) and isinstance(renderer.glyph, VBar)
            for renderer in plot.renderers
        )

        # Check if the source data matches the input
        source_data = plot.select(ColumnDataSource)[0].data
        self.assertEqual(source_data['labels'], self.labels)
        self.assertEqual(source_data['data'], self.data)

    def test_donut(self):
        plot = donut(self.labels, self.data)

        # Check some properties of the plot
        self.assertEqual(plot.title.text, 'Classes')

        # Assert that the plot is an instance of Bokeh's figure
        self.assertIsInstance(plot, figure)

    def test_days_function(self):
        # Mock data for testing
        day_data = {
            'category1': {
                'dates': [datetime(2023, 1, 1)],
                'date_strings': ['2023-01-01'],
                'hours': [3.5],
                'start_times': [datetime(2023, 1, 1, 9, 0)],
                'start_time_strings': ['9:00 AM'],
                'end_times': [datetime(2023, 1, 1, 12, 30)],
                'end_time_strings': ['12:30 PM'],
                'color': ['blue'],
                'class': ['Math'],
                'description': ['Algebra'],
            },
            'category2': {
                'dates': [datetime(2023, 1, 2)],
                'date_strings': ['2023-01-02'],
                'hours': [2],
                'start_times': [datetime(2023, 1, 1, 1, 0)],
                'start_time_strings': ['1:00 PM'],
                'end_times': [datetime(2023, 1, 1, 2, 30)],
                'end_time_strings': ['2:30 PM'],
                'color': ['blue'],
                'class': ['Language Arts'],
                'description': ['Reading'],
            },
        }

        min_date = datetime(2023, 1, 1)
        max_date = datetime(2023, 1, 15)

        plots = days(day_data, min_date, max_date)

        # Assert that the function returns a list of two plots
        self.assertEqual(len(plots), 2)

        # Assert that the first plot is a Bokeh figure
        self.assertTrue(isinstance(plots[0], figure))

        # Assert that the second plot is a Bokeh figure with a RangeTool
        self.assertTrue(isinstance(plots[1], figure))
        self.assertTrue(any(isinstance(tool, RangeTool) for tool in plots[1].tools))

    def test_reading_list(self):
        # Test the reading_list function with the sample spreadsheet
        book_lists = reading_list(self.path)
        # check that the output is a list of lists
        self.assertIsInstance(book_lists, list)
        self.assertTrue(all(isinstance(book_list, list) for book_list in book_lists))
        # Check that the output has the same length as the number of sheets in the spreadsheet
        self.assertEqual(len(book_lists), 2)
        # Check that each sublist contains a Div and a DataTable
        self.assertTrue(all(isinstance(book_list[0], Div) for book_list in book_lists))
        self.assertTrue(
            all(isinstance(book_list[1], DataTable) for book_list in book_lists)
        )
        # Check that the Div text matches the sheet name
        self.assertEqual(book_lists[0][0].text, '<h3>Adults</h3>')
        self.assertEqual(book_lists[1][0].text, '<h3>Kids</h3>')
        # Check that the DataTable source and columns match the sheet data
        adult_source = book_lists[0][1].source
        adult_columns = book_lists[0][1].columns
        kids_source = book_lists[1][1].source
        kids_columns = book_lists[1][1].columns
        # Check the adult source data
        self.assertEqual(adult_source.data['index'], [1, 2, 3])
        self.assertSequenceEqual(
            adult_source.data["titles"].to_list(),
            [
                'The Anti-Communist Manifesto',
                'Basic Economics',
                'The Rape of the Mind: The Psychology of Thought Control, Menticide, and Brainwashing',
            ],
        )
        self.assertEqual(
            adult_source.data['authors'].to_list(),
            ['Jesse Kelly', 'Thomas Sowell', 'Joost A.M. Meerloo'],
        )
        self.assertEqual(
            adult_source.data['language'].to_list(), ['English', 'English', 'English']
        )
        self.assertEqual(
            adult_source.data['isbns'].to_list(),
            ['978-1668010877', '978-0465081387', '978-161427'],
        )
        self.assertEqual(
            adult_source.data['level'].to_list(),
            ['Beginner', 'Advanced', 'Intermediate'],
        )
        # Check the adult columns
        self.assertEqual(len(adult_columns), 6)
        self.assertEqual(adult_columns[0].field, 'index')
        self.assertEqual(adult_columns[0].title, '#')
        self.assertEqual(adult_columns[1].field, 'titles')
        self.assertEqual(adult_columns[1].title, 'Title')
        self.assertEqual(adult_columns[2].field, 'authors')
        self.assertEqual(adult_columns[2].title, 'Author')
        self.assertEqual(adult_columns[3].field, 'language')
        self.assertEqual(adult_columns[3].title, 'Language')
        self.assertEqual(adult_columns[4].field, 'isbns')
        self.assertEqual(adult_columns[4].title, 'ISBN')
        self.assertEqual(adult_columns[5].field, 'level')
        self.assertEqual(adult_columns[5].title, 'Level')
        # Check the kids source data
        self.assertEqual(kids_source.data['index'], [1, 2, 3])
        self.assertEqual(
            kids_source.data['titles'].to_list(),
            [
                'Jane and the King',
                'Los Gemelos Tuttle y la Criatura de la Isla Jekyll',
                'Los Gemelos Tuttle y la Regla de Oro',
            ],
        )
        self.assertEqual(
            kids_source.data['authors'].to_list(),
            ['Jenny Phillips', 'Connor Boyack', 'Connor Boyack'],
        )
        self.assertEqual(
            kids_source.data['language'].to_list(),
            ['English', 'Spanish', 'Spanish'],
        )
        self.assertEqual(
            kids_source.data['isbns'].to_list(),
            ['978-1951097493', '978-1943521159', '978-1943521159'],
        )
        # Check that the kids source does not have a level column
        self.assertNotIn('level', kids_source.data)
        # Check the kids columns
        self.assertEqual(len(kids_columns), 5)
        self.assertEqual(kids_columns[0].field, 'index')
        self.assertEqual(kids_columns[0].title, '#')
        self.assertEqual(kids_columns[1].field, 'titles')
        self.assertEqual(kids_columns[1].title, 'Title')
        self.assertEqual(kids_columns[2].field, 'authors')
        self.assertEqual(kids_columns[2].title, 'Author')
        self.assertEqual(kids_columns[3].field, 'language')
        self.assertEqual(kids_columns[3].title, 'Language')
        self.assertEqual(kids_columns[4].field, 'isbns')
        self.assertEqual(kids_columns[4].title, 'ISBN')
        # Check that the kids columns do not have a level column
        self.assertFalse(any(column.field == 'level' for column in kids_columns))

    def test_reading_level(self):
        # Test the reading_level function with the sample data
        p = reading_level(self.level, self.date)
        # Check that the output is a Bokeh figure
        self.assertIsInstance(p, figure)
        # Check that the figure has the expected title, tools, height, sizing mode and x axis type
        self.assertEqual(p.title.text, 'Reading Level')
        self.assertEqual(p.tools, [])
        self.assertEqual(p.height, COLUMN_HEIGHT)
        self.assertEqual(p.sizing_mode, 'stretch_width')
        # Check that the figure has a line and a circle glyph
        self.assertEqual(len(p.renderers), 2)
        self.assertEqual(p.renderers[0].glyph.__class__.__name__, 'Line')
        self.assertEqual(p.renderers[1].glyph.__class__.__name__, 'Circle')
        # Check that the line and circle glyphs have the expected data and properties
        self.assertEqual(p.renderers[0].data_source.data['x'], list(self.date))
        self.assertEqual(p.renderers[0].data_source.data['y'], list(self.level))
        self.assertEqual(p.renderers[0].glyph.line_color, PALETTE[1])
        self.assertEqual(p.renderers[0].glyph.line_width, 2)
        self.assertEqual(p.renderers[1].data_source.data['x'], list(self.date))
        self.assertEqual(p.renderers[1].data_source.data['y'], list(self.level))
        self.assertEqual(p.renderers[1].glyph.size, 6)

    def test_curricula_function(self):
        mock_data = {
            'Course': ['Math', 'Science', 'History'],
            'Materials': ['Book1', 'Book2', 'Book3'],
            'ISBN': ['123456', '789012', '345678'],
        }

        source = ColumnDataSource(data=mock_data)

        data_table = curricula(mock_data)

        self.assertListEqual(
            list(data_table.source.data['Course']), source.data['Course']
        )
        self.assertListEqual(
            list(data_table.source.data['Materials']), source.data['Materials']
        )
        self.assertListEqual(list(data_table.source.data['ISBN']), source.data['ISBN'])

    def tearDown(self):
        # Delete the sample spreadsheet
        os.remove(self.path)


if __name__ == '__main__':
    unittest.main()
