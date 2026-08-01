#!/usr/bin/env python
# encoding: utf-8

import datetime

from insert_pre1995_minutes import build_minutes_values, date_ordinal


def _record(name, location, date):
    return {
        'name': name,
        'location': location,
        'date': date,
        'normalized_minutes': 'Leaders: Test Leader, [31b-1991].',
    }


def test_build_minutes_values_marks_southwest_texas_as_non_denson():
    record = _record(
        'SOUTHWEST TEXAS CONVENTION',
        'Littlevine Primitive Baptist Church, Austin, Texas',
        'October 30, 31, 1993',
    )

    values = build_minutes_values(record, minutes_year=1993, denson_year=1991)

    assert values['IsDenson'] == 0


def test_build_minutes_values_marks_early_1992_minutes_non_denson():
    record = _record(
        'All-California Sacred Harp Convention',
        "Women's 20th Century Club, Eagle Rock, California",
        'January 19, 1992',
    )
    record['raw_name'] = 'ALL-CALIFORNIA SACRED HARP CONVENTION'
    record['raw_location'] = "Women's 20th Century Club, Eagle Rock, California"
    record['raw_date'] = 'January 19, 1992'

    values = build_minutes_values(record, minutes_year=1992, denson_year=1991)

    assert values['IsDenson'] == 0
    assert values['Name'] == 'All-California Sacred Harp Convention'


def test_build_minutes_values_keeps_1992_bob_burnham_denson():
    record = _record(
        'BOB BURNHAM MEMORIAL DUTCH TREAT SINGING',
        'Jacksonville Alabama',
        'February 2, 1992',
    )

    values = build_minutes_values(record, minutes_year=1992, denson_year=1991)

    assert values['IsDenson'] == 1


def test_date_ordinal_handles_comma_after_month():
    assert date_ordinal('January, 22-23, 1994') == datetime.date(
        1994, 1, 22
    ).toordinal()


def test_date_ordinal_handles_weekday_text_and_comma_after_month():
    assert date_ordinal('Saturday night, November, 18, 2006') == datetime.date(
        2006, 11, 18
    ).toordinal()
