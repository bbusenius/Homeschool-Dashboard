"""Module Description

This module contains functions for handling data visualization with Bokeh.
"""
from datetime import timedelta
from math import pi

import pandas as pd
from bokeh.models import (
    ColumnDataSource,
    DataTable,
    DatetimeTickFormatter,
    Div,
    HoverTool,
    RangeTool,
    TableColumn,
)
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from fi import get_percentage

from hsd_constants import COLUMN_HEIGHT, PALETTE


def barchart(labels, data):
    """Bokeh bar graph showing the number of hours spent on each
    project. Used to chart hours spent per class for a given year.

    Args:
        labels (list): strings to use as categories.
        data: (data) floats that correspond to labels where each
        float is a number to chart for the category of the same
        index. labels and data should be the same length.

    Returns:
        Bokeh plot
    """
    source = ColumnDataSource(data=dict(labels=labels, data=data))
    p = figure(
        x_range=labels,
        height=COLUMN_HEIGHT,
        toolbar_location=None,
        tooltips=[
            ('Hours', '@data'),
        ],
        title='Hours',
        sizing_mode='stretch_width',
    )
    p.vbar(
        x='labels',
        top='data',
        width=0.9,
        source=source,
        legend_field='labels',
        line_color='white',
        fill_color=factor_cmap('labels', palette=PALETTE, factors=labels),
    )

    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.y_range.end = max(data)
    p.legend.orientation = 'horizontal'
    p.legend.location = 'top_center'
    p.toolbar.active_drag = None

    return p


def donut(labels, data):
    """Bokeh donut chart that shows percentages of total time spent
    on a given category.

    Args:
        labels (list): strings to use as categories.
        data (list): floats that correspond to labels where each
        float is a number to chart for the category of the same
        index. labels and data should be the same length.

    Returns:
        Bokeh plot
    """
    total_hours = sum(data)
    percentages = [get_percentage(d, total_hours, i=False, r=True) for d in data]
    source = ColumnDataSource(data=dict(labels=labels, data=percentages))
    donut = figure(
        title='Classes',
        toolbar_location=None,
        tools='',
        height=COLUMN_HEIGHT,
        sizing_mode='stretch_width',
    )

    cumulative_angles = [0] + [
        sum(percentages[: i + 1]) / 100 * 2 * pi for i in range(len(percentages))
    ]

    source.add(cumulative_angles[:-1], 'start_angle')
    source.add(cumulative_angles[1:], 'end_angle')

    donut.annular_wedge(
        x=0,
        y=1,
        inner_radius=0.3,
        outer_radius=0.7,
        start_angle='start_angle',
        end_angle='end_angle',
        line_color='white',
        fill_color=factor_cmap('labels', palette=PALETTE, factors=labels),
        legend_field='labels',
        source=source,
    )
    donut.xaxis.visible = False
    donut.yaxis.visible = False

    hover = HoverTool(
        tooltips=[
            ('Label', '@labels'),
            ('Data', '@data{0.00}%'),
        ],
        mode='mouse',
    )
    donut.add_tools(hover)

    return donut


def days(day_data, min_date, max_date):
    """Multicolor candlestick plot showing tasks completed by date (x axis)
    and time (y axis). Items plotted are color coated to correspond with
    their category label and display tooltips with details about the event.

    Args:
        day_data: dictionary of dictionaries where the first keys are for
        categories and their values are dictionaries of corresponding data
        for a given day.
           {'category': {
                'dates': [],
                'date_strings': [],
                'hours': [],
                'start_times': [],
                'start_time_strings': [],
                'end_times': [],
                'end_time_strings': [],
                'color': [],
                'class': [],
                'description': [],
            },}
        min_date: date object, the first date of time range for all day data.
        max_date: date object, the latest date for the same time range.

    Returns:
        List of Bokeh plots where the first is a candlestick plot of date time
        events colored by category and the second is a slider that allows the
        user to control the first plot and traverse the time time range between
        min_date and max_date.
    """
    tooltips = [
        ('Class', '@class'),
        ('Date', '@date_strings'),
        ('Start Time', '@start_time_strings'),
        ('End Time', '@end_time_strings'),
        ('Hours', '@hours{0.00}'),
        ('Description', '@description'),
    ]

    p = figure(
        x_axis_type='datetime',
        x_axis_location='above',
        height=COLUMN_HEIGHT,
        sizing_mode='stretch_width',
        tooltips=tooltips,
        x_range=(max_date - timedelta(days=30), max_date),
    )
    p.toolbar.logo = None
    p.toolbar.active_drag = None

    for sheet in day_data:
        data = day_data[sheet]
        source = ColumnDataSource(data)

        p.segment(
            x0='dates',
            y0='start_times',
            x1='dates',
            y1='end_times',
            line_color='color',
            source=source,
            line_width=8,
        )

        p.yaxis[0].formatter = DatetimeTickFormatter(hours='%I:%M %p')

    select = figure(
        title='Drag the slider to change the range above',
        height=80,
        sizing_mode='stretch_width',
        y_range=p.y_range,
        x_axis_type='datetime',
        y_axis_type=None,
        tools='',
        toolbar_location=None,
        background_fill_color='#efefef',
    )

    range_tool = RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = '#cccccc'
    range_tool.overlay.fill_alpha = 1

    select.line('dates', 'start_times', source=source, line_color='#efefef')
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)

    return [p, select]


def reading_list(path):
    """Reads a spreadsheet file containing multiple sheets of book data and creates
    a list of Bokeh DataTables with optional columns based on the available data.

    Args:
        path (str): The file path to the Excel spreadsheet.

    Returns:
        list: A list of Bokeh DataTables, each representing a sheet in the spreadsheet.
            Each DataTable includes columns such as 'Title', 'Author', 'Language', 'ISBN',
            and an optional 'Level' column if the 'level' information is available.
    """
    # Bail if there's not a path
    if not isinstance(path, str):
        return []

    with pd.ExcelFile(path) as spreadsheet:
        sheet_names = spreadsheet.sheet_names

    book_lists = []
    for sheet_name in sheet_names:
        df = pd.read_excel(path, sheet_name=sheet_name)
        df.columns = df.columns.str.lower()
        titles = df['title']
        authors = df['author'].fillna('')
        language = df['language'].fillna('')
        isbns = df['isbn'].fillna('')
        index = df['index'] = list(range(1, len(df) + 1))

        data = dict(
            index=index,
            titles=titles,
            authors=authors,
            language=language,
            isbns=isbns,
        )

        # Set optional columns
        try:
            level = df['level'].fillna('')
            data['level'] = level
        except (KeyError):
            level = pd.Series([])

        columns = [
            TableColumn(field='index', title='#'),
            TableColumn(field='titles', title='Title'),
            TableColumn(field='authors', title='Author'),
            TableColumn(field='language', title='Language'),
            TableColumn(field='isbns', title='ISBN'),
        ]

        # Add optional columns
        if level.any():
            columns.append(TableColumn(field='level', title='Level'))

        # Set source
        source = ColumnDataSource(data)

        book_lists.append(
            [
                Div(text=f'<h3>{sheet_name}</h3>', flow_mode='inline'),
                DataTable(
                    source=source,
                    columns=columns,
                    height_policy='auto',
                    index_position=None,
                    sizing_mode='stretch_width',
                ),
            ]
        )
    return book_lists


def reading_level(level, date):
    """Creates a Bokeh line chart representing a student's reading level over time.

    Args:
        level (pandas.Series): A pandas Series containing reading level data.
        date (pandas.Series): A pandas Series containing corresponding date
        information.

    Returns:
        bokeh.plotting.Figure: A Bokeh figure displaying a line chart of reading
        level over time.
    """
    x = list(date)
    y = list(level)
    p = figure(
        title='Reading Level',
        tools='',
        height=COLUMN_HEIGHT,
        sizing_mode='stretch_width',
        x_axis_type='datetime',
    )
    p.xaxis.visible = False
    p.yaxis.major_tick_line_color = None
    p.yaxis.minor_tick_line_color = None
    p.toolbar.logo = None
    p.line(x=x, y=y, line_color=PALETTE[1], line_width=2)
    p.scatter(x, y, size=6)
    return p


def curricula(data):
    """Creates a Bokeh DataTable representing curricula data.

    Args:
        data (dict or pandas.DataFrame): The data to be displayed in the
        DataTable. If a dictionary is provided, it will be converted to a
        pandas DataFrame.

    Returns:
        bokeh.models.widgets.tables.DataTable: A Bokeh DataTable displaying
        the provided curricula data.
    """
    df = pd.DataFrame(data)
    source = ColumnDataSource(df)
    columns = [TableColumn(field=col, title=col) for col in df.columns]
    data_table = DataTable(
        source=source,
        columns=columns,
        height=COLUMN_HEIGHT,
        sizing_mode='stretch_width',
        index_position=None,
        sortable=False,
    )
    return data_table
