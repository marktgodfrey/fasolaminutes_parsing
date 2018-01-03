#!/usr/bin/env python
# encoding: utf-8

import datetime
import re
import sqlite3

def open_db():
    conn = sqlite3.connect("minutes.db")
    conn.text_factory = unicode
    return conn


def minutes_to_csv(name, date):
    """Turns a minutes row into a csv filename.

    Format is 'YYYY-MM-DD-${name}.csv' where name has all non alphanumeric
    characters removed, and spaces are replaced with '_'.
    """
    name = re.sub(r'\s+\\n\s+', ' ', name) # Replace literal ' \n '
    filename = '%s-%s' % (parse_minutes_date(name, date).strftime('%Y-%m-%d'), name)
    filename = re.sub(r'[^A-Za-z0-9\-_]', '', re.sub(r'\s+', '_', filename))
    return filename + '.csv'

def parse_minutes_date(name, date):
    # Some 1990s dates start with 'l' instead of '1'
    date = re.sub(r'\bl(\d{3}\b)', r'1\1', date)
    # Some dates don't include the year (if the year is in the name)
    date = date + ' ' + name
    (month, day, year) = date_re.search(date).groups()
    return datetime.date(int(year), months.get(month.lower()), int(day))

month_names = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
               'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

months = {month: i + 1 for i, month in enumerate(month_names)}

# This just extracts the first date
date_re = re.compile(r'''
    (%s)\w*[\s\D]+        # Month
    (\d{1,2})(?=\D)       # Day
    [-\d,\s\w]*?          # Possible extra days
    [\s,](\d{4})          # Year
''' % ('|'.join(month_names),), re.X | re.I)
