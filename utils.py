import dateparser


def parse_date(date_str):
    """Parse a date string of an unknown format. Let dateparser guess the
    format instead of handing it off straight to dateutil like a maniac.

    Args:
        date_str (str): date string of an unknown format.

    Returns:
        date object or pandas.NA.
    """
    if date_str:
        return dateparser.parse(date_str)
    return None
