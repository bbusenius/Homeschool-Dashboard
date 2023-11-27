import unittest
from unittest.mock import patch, Mock
from utils import parse_date


class TestParseDate(unittest.TestCase):

    @patch('utils.dateparser.parse')
    def test_parse_date_with_valid_date(self, mock_dateparser_parse):
        # Arrange
        expected_result = Mock()
        mock_dateparser_parse.return_value = expected_result
        date_str = '2023-11-10'

        # Act
        result = parse_date(date_str)

        # Assert
        mock_dateparser_parse.assert_called_once_with(date_str)
        self.assertEqual(result, expected_result)

    @patch('utils.dateparser.parse')
    def test_parse_date_with_empty_string(self, mock_dateparser_parse):
        # Arrange
        date_str = ''

        # Act
        result = parse_date(date_str)

        # Assert
        mock_dateparser_parse.assert_not_called()
        self.assertEqual(result, None)

    @patch('utils.dateparser.parse')
    def test_parse_date_with_invalid_date(self, mock_dateparser_parse):
        # Arrange
        mock_dateparser_parse.return_value = None
        date_str = 'invalid_date'

        # Act
        result = parse_date(date_str)

        # Assert
        mock_dateparser_parse.assert_called_once_with(date_str)
        self.assertEqual(result, None)

    def test_parse_date_with_various_hour_formats(self):
        date_strings = [
            '01:00 PM',
            '1:00 PM',
            '01:00 pm',
            '1:00 pm',
            '01:00pm',
            '1:00pm',
            '13:00',
            '13:00 PM',
            '13:00 pm',
            '13:00pm',
            '1:00:00 PM',
            '1:00:00 pm',
            '1:00:00pm',
            '01:00:00 PM',
            '01:00:00 pm',
            '01:00:00pm',
        ]

        for time in date_strings:
            string = parse_date(time).strftime('%I:%M %p')
            self.assertEqual(string, '01:00 PM')


    def test_parse_date_with_various_hour_formats_that_should_fail(self):
        date_strings = [
            '13:00:00 PM',
            '13:00:00 pm',
            '13:00:00pm',
        ]

        for time in date_strings:
            string = parse_date(time)
            self.assertEqual(string, None)

        self.assertEqual(parse_date('1:00').strftime('%I:%M %p'), '01:00 AM')


if __name__ == '__main__':
    unittest.main()
