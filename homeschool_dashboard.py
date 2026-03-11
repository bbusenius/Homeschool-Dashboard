import argparse
import os
import webbrowser
from datetime import datetime

import pandas as pd
from bokeh.embed import components
from bokeh.models import Div
from bokeh.resources import INLINE
from jinja2 import Template

from hsd_constants import LOGO_BW, OUTPUT_FILE, PALETTE
from hsd_plot import barchart, curricula, days, donut, reading_level, reading_list
from styles import CSS
from templates import INNER_TEMPLATE_STR, OUTER_TEMPLATE_STR
from fi import get_percentage
from utils import parse_date


def _find_bad_rows(df, checks):
    """Find rows with invalid data and return formatted error messages.

    Args:
        df (DataFrame): the DataFrame being validated.
        checks (list): list of (mask, message) tuples where mask is a
            boolean Series and message describes the problem.

    Returns:
        list: formatted error strings, one per bad row/field.
    """
    bad_rows = []
    # Combine all boolean masks into one using bitwise OR (|=) so
    # that any row flagged by any check is included. This is a
    # vectorized pandas operation, not a per-row loop.
    combined = pd.Series(False, index=df.index)
    for mask, _ in checks:
        combined |= mask
    # Only loop over rows when there's actually bad data
    if combined.any():
        for idx in df.index[combined]:
            row_num = idx + 2  # +1 for 0-index, +1 for header row
            for mask, msg in checks:
                if mask.at[idx]:
                    bad_rows.append(f"  Row {row_num}: {msg}")
    return bad_rows


def generate_plots(files):
    """Main function that generates the plots and all corresponding html.

    Args:
        files (list): list of strings.

    Returns:
        HTML (str): everything needed to display the data including
        Javascript and CSS.
    """
    seconds_in_an_hour = 3600
    name = ''
    inner_html = ''
    for file in files:
        spreadsheet = pd.ExcelFile(file)
        sheet_names = spreadsheet.sheet_names

        grade = ''
        hours = []
        teacher_hours = {}
        min_date = datetime.max
        max_date = datetime.min
        day_data = {}
        level = pd.Series([])
        level_date = pd.Series([])
        reading_lists = ''
        reading_list_path = ''
        curricula_data = {
            'Course': [],
            'Materials': [],
            'ISBN': [],
        }

        for key in sheet_names:
            day_data[key] = {
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
            }

        filename = os.path.basename(file)

        for i, sheet_name in enumerate(sheet_names):
            try:
                df = pd.read_excel(file, sheet_name=sheet_name)
                df.columns = df.columns.str.lower()

                # Validate required columns exist
                required_cols = ['date', 'start time', 'end time']
                missing = [c for c in required_cols if c not in df.columns]
                if missing:
                    raise KeyError(
                        f"Missing required column(s): "
                        f"{', '.join(missing)}"
                    )

                # Drop rows with NaT values
                df = df.dropna(subset=['end time'])
                df = df.dropna(subset=['start time'])
                df = df.dropna(subset=['date'])

                # Make usre that start times and date times (datetime objects)
                # are treated as strings so they can be reparsed for consistency
                data_types = {'start time': str, 'end time': str}
                df = df.astype(data_types)

                start_time = df['start time'] = pd.to_datetime(
                    df['start time'].apply(parse_date), errors='coerce'
                )
                end_time = df['end time'] = pd.to_datetime(
                    df['end time'].apply(parse_date), errors='coerce'
                )

                parsed_dates = pd.to_datetime(
                    df['date'], errors='coerce'
                )

                # Check for unparseable dates/times and report row numbers
                bad_rows = _find_bad_rows(df, [
                    (parsed_dates.isna(), "invalid 'date'"),
                    (start_time.isna(), "invalid 'start time'"),
                    (end_time.isna(), "invalid 'end time'"),
                ])
                if bad_rows:
                    detail = "\n".join(bad_rows)
                    raise ValueError(
                        f"Invalid data found:\n{detail}"
                    )

                duration = end_time - start_time

                # Check for end times before start times (e.g. AM/PM error)
                bad_durations = _find_bad_rows(df, [
                    (duration < pd.Timedelta(0),
                     "end time is before start time"),
                ])
                if bad_durations:
                    detail = "\n".join(bad_durations)
                    raise ValueError(
                        f"Invalid data found:\n{detail}"
                    )

                hours_decimal = (
                    duration.dt.total_seconds() / seconds_in_an_hour
                )
                df['hours'] = hours_decimal

                oldest_date = parsed_dates.min()
                newest_date = parsed_dates.max()
                if oldest_date < min_date:
                    min_date = oldest_date
                if newest_date > max_date:
                    max_date = newest_date

                day_data[sheet_name]['dates'].extend(parsed_dates)
                day_data[sheet_name]['date_strings'].extend(
                    parsed_dates.dt.strftime('%Y-%m-%d')
                )
                num_cells = len(day_data[sheet_name]['dates'])
                day_data[sheet_name]['start_times'].extend(
                    start_time.dt.time
                )
                day_data[sheet_name]['start_time_strings'].extend(
                    start_time.dt.strftime('%I:%M %p')
                )
                day_data[sheet_name]['end_times'].extend(end_time.dt.time)
                day_data[sheet_name]['end_time_strings'].extend(
                    end_time.dt.strftime('%I:%M %p')
                )
                day_data[sheet_name]['hours'].extend(df['hours'])
                day_data[sheet_name]['color'].extend(
                    [PALETTE[i] for x in range(num_cells)]
                )
                day_data[sheet_name]['class'].extend(
                    [sheet_name for x in range(num_cells)]
                )
                day_data[sheet_name]['description'].extend(
                    df['description']
                )

                total_hours = df['hours'].sum()
                hours.append(total_hours)

                # Accumulate hours per teacher
                try:
                    teachers = df['teacher'].fillna('Independent')
                    for teacher, h in df.groupby(teachers)['hours'].sum().items():
                        teacher_hours[teacher] = (
                            teacher_hours.get(teacher, 0) + h
                        )
                except (KeyError):
                    pass

                # Populate curricula data
                try:
                    materials = df['materials'].dropna()
                    if len(materials) > 0:
                        curricula_data['Materials'].extend(materials)
                        curricula_data['Course'].append(sheet_name)
                        curricula_data['Course'].extend(
                            [pd.NA for i in range(len(materials) - 1)]
                        )
                        isbn = df['isbn'][: len(materials)].fillna('')
                        curricula_data['ISBN'].extend(isbn)
                except (KeyError):
                    pass

                # Set global variables if they exist in the first row of
                # any spreadsheet. These are treated like user
                # configuration.
                try:
                    column_index = df.columns.get_loc('grade')
                    tmp_grade = df.iloc[0, column_index]
                    if isinstance(tmp_grade, str):
                        grade = tmp_grade
                except (KeyError):
                    pass

                try:
                    column_index = df.columns.get_loc('name')
                    tmp_name = df.iloc[0, column_index]
                    if isinstance(tmp_name, str):
                        name = tmp_name
                except (KeyError):
                    pass

                try:
                    column_index = df.columns.get_loc('reading list')
                    reading_list_path = df.iloc[0, column_index]
                except (KeyError):
                    pass

                # Build reading lists if a path was found.
                if reading_list_path:
                    reading_lists = reading_list(reading_list_path)

                # Reading level if it exists.
                try:
                    level = df['reading level'].dropna()
                    copy = df.loc[level.index]
                    level_date = pd.to_datetime(copy['date'])
                except (KeyError):
                    pass

            except Exception as e:
                raise type(e)(
                    f"Sheet '{sheet_name}' in '{filename}': {e}"
                ) from e

        # Simple HTML elements to drop on the page.
        total = sum(hours)
        teacher_html = ''
        if teacher_hours:
            sorted_teachers = sorted(
                teacher_hours.items(), key=lambda x: x[1], reverse=True
            )
            lines = [
                f'{name}: {get_percentage(h, total, r=True)}%'
                for name, h in sorted_teachers
            ]
            teacher_html = (
                '<hr style="margin: 0.5em 0;"/>'
                '<p style="font-size: 0.5em;">'
                + '<br/>'.join(lines)
                + '</p>'
            )
        total_hours_taught = Div(
            styles={'text-align': 'center', 'font-size': '2em'},
            text=(
                f'<p><strong>{round(total, 2)}</strong>'
                f' <br/>hours of learning</p>'
                f'{teacher_html}'
            ),
            sizing_mode='stretch_width',
        )

        days_plot, days_select = days(day_data, min_date, max_date)

        # Reading lists are special
        dyn_scripts = []
        dyn_divs = []
        for component_set in reading_lists:
            for component in component_set:
                dyn_script, dyn_div = components(component)
                dyn_scripts.append(dyn_script)
                dyn_divs.append(dyn_div)

        # Widgets and plots to display
        widgets = {
            'total_hours': total_hours_taught,
            'barchart': barchart(sheet_names, hours),
            'donut': donut(sheet_names, hours),
            'days': days_plot,
            'slider': days_select,
        }

        # Optional widgets and plots to dispaly
        if not level.empty and not level_date.empty:
            widgets['reading_level'] = reading_level(level, level_date)
        if any(list(curricula_data.values())[1:]):
            widgets['curricula'] = curricula(curricula_data)

        inner_template = Template(INNER_TEMPLATE_STR)

        script, div = components(widgets)
        html = inner_template.render(
            plot_script=script,
            plot_div=div,
            dyn_scripts=dyn_scripts,
            dyn_divs=dyn_divs,
            grade=grade,
        )
        inner_html += html

        # Redundant closing of file but necessary for some reason
        spreadsheet.close()

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    outer_template = Template(OUTER_TEMPLATE_STR)
    outer_html = outer_template.render(
        content=inner_html,
        name=name,
        bokeh_js=js_resources,
        bokeh_css=css_resources,
        css=CSS,
        logo=LOGO_BW,
    )
    return outer_html


def run_in_code(files):
    """Build a webpage in code and open it in the browser.

    Args:
        files (list): paths to files.
    """
    html = generate_plots(files)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html)
    webbrowser.open(OUTPUT_FILE)


def save_html(files, output_path=OUTPUT_FILE):
    """Build a webpage and save it.

    Args:
        files (list): paths to files.
        output_file (str): name of a file, should end in .html.
    """
    html = generate_plots(files)
    with open(output_path, 'w') as f:
        f.write(html)


def run():
    """Build a webpage and open it in the browser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='*', help='List of files')
    args = parser.parse_args()
    files = args.files

    html = generate_plots(files)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html)
    webbrowser.open(OUTPUT_FILE)


if __name__ == "__main__":
    run()
