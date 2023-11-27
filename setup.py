from setuptools import find_packages, setup

setup(
    name='homeschool_dashboard',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'bokeh',
        'dateparser',
        'fi @ git+https://github.com/bbusenius/FI.git#egg=FI',
        'openpyxl',
        'pandas',
    ],
    scripts=[
        'homeschool_dashboard.py',
    ],
    py_modules=[
        'hsd_constants',
        'homeschool_dashboard',
        'hsd_plot',
        'styles',
        'templates',
        'utils',
    ],
    entry_points={
        'console_scripts': [
            'homeschool_dashboard = homeschool_dashboard:run',
        ],
    },
    test_suite='tests',
)
