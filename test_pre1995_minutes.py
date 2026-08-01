#!/usr/bin/env python
# encoding: utf-8

from pre1995_minutes import (
    normalize_pre1995_header_text,
    normalize_pre1995_minutes,
    parse_big_minutes_text,
    reflow_pre1995_ocr_text,
    separate_pre1995_comma_list_leaders,
    split_big_minutes_text,
)


def test_split_big_minutes_text_uses_three_line_headers_after_notes():
    text = """January 1, 1993
not a singing header

NOTES:

OLD DEKALB COUNTY COURTHOUSE IN DECATUR
Decatur Georgia
Saturday, September 21, 1991
Doug Allison led song on page 335.

FLORIDA STATE SINGING CONVENTION
Panama City Beach, Florida
November 30--December 1, 1991
Jeff Sheppard led song on page 111.
"""

    records = split_big_minutes_text(text)

    assert len(records) == 2
    assert records[0]['name'] == 'Old DeKalb County Courthouse in Decatur'
    assert records[0]['raw_name'] == 'OLD DEKALB COUNTY COURTHOUSE IN DECATUR'
    assert records[0]['location'] == 'Decatur Georgia'
    assert records[0]['date'] == 'Saturday, September 21, 1991'
    assert records[1]['name'] == 'Florida State Singing Convention'


def test_split_big_minutes_text_joins_wrapped_title_lines():
    text = """NOTES:

MR. AND MRS O. H. HANDLEY AND MR. AND MRS W.H.
WALKER MEMOIRAL SINGING
Vinemont Fire Station, Vinemont, Alabama.
March 1, 1992
Chairman led song on page 31b.
"""

    records = split_big_minutes_text(text)

    assert len(records) == 1
    assert records[0]['name'] == (
        'Mr. and Mrs O. H. Handley and Mr. and Mrs W.H. '
        'Walker Memoiral Singing'
    )


def test_split_big_minutes_text_stops_before_address_directory():
    text = """NOTES:

OAK GROVE CHURCH
Near Alpheretta, Georgia
November 8, 1992
Loy Garrison led song on page 69.

197

Aaron, Lorene Rt 1 box 203a Nauvoo Al 35578
"""

    records = split_big_minutes_text(text)

    assert 'Aaron, Lorene' not in records[0]['minutes']


def test_split_big_minutes_text_stops_before_address_directory_without_page_marker():
    text = """NOTES:

JAMES RIVER CONVENTION
Richmond, Virginia
November 20, 21, 1993
Chairman led song on page 38b.
Chairman, Stephen McMaster; Secretary, Kelly Macklin.

Aaron, Lorene Rt 1 Box 203 4 Nauvoo Al 35578
Aaron, Ruth 1Water Oak 18th St E Jasper Al 35501
Abrahams, Donna 307 S Reynolds P219 Alexandria Va 22304
Abrams, Kurt 2144 Bonar St Berkelu Ca 34702
Adams, Azilee 306 Devon Dr Birmingham Al 35209
"""

    records = split_big_minutes_text(text)

    assert len(records) == 1
    assert 'Stephen McMaster' in records[0]['minutes']
    assert 'Aaron, Lorene' not in records[0]['minutes']


def test_split_big_minutes_text_handles_comma_day_range_date():
    text = """NOTES:

SOUTHWEST TEXAS SACRED HARP CONVENTION
Little Vine Primitive Baptist Church - Austin, Texas
August 29, 30, 1992
The fall session was held.
"""

    records = split_big_minutes_text(text)

    assert len(records) == 1
    assert records[0]['date'] == 'August 29, 30, 1992'


def test_split_big_minutes_text_handles_three_comma_separated_days():
    text = """NOTES:

NATIONAL SACRED HARP CONVENTION
Briarwood Presbyterian Church, Birmingham, Alabama
June 17, 18 ,19, 1993
The convention was called to order.
"""

    records = split_big_minutes_text(text)

    assert len(records) == 1
    assert records[0]['name'] == 'National Sacred Harp Convention'
    assert records[0]['date'] == 'June 17, 18 ,19, 1993'


def test_split_big_minutes_text_handles_and_separated_days():
    text = """NOTES:

NATIONAL SACRED HARP CONVENTION
Samford University, Birmingham, Alabama
June 18, 19 and 20, 1992
The convention was called to order.
"""

    records = split_big_minutes_text(text)

    assert len(records) == 1
    assert records[0]['date'] == 'June 18, 19 and 20, 1992'


def test_split_big_minutes_text_joins_wrapped_location_lines():
    text = """NOTES:

ILLINOIS STATE SACRED HARP CONVENTION
Otterbein United Methodist Church and Coles County Courthouse
Charleston, Illinois
September 25-26, 1993
The ninth annual session was called to order.
"""

    records = split_big_minutes_text(text)

    assert len(records) == 1
    assert records[0]['name'] == 'Illinois State Sacred Harp Convention'
    assert records[0]['location'] == (
        'Otterbein United Methodist Church and Coles County Courthouse '
        'Charleston, Illinois'
    )


def test_split_big_minutes_text_splits_location_and_date_on_same_line():
    text = """NOTES:

Illinois State SACRED HARP CONVENTION
Otterbein United Methodist Church and Coles County Courthouse
Charleston, Illinois September 26-27, 1992
The eighth annual session was called to order.
"""

    records = split_big_minutes_text(text)

    assert len(records) == 1
    assert records[0]['name'] == 'Illinois State Sacred Harp Convention'
    assert records[0]['location'] == (
        'Otterbein United Methodist Church and Coles County Courthouse '
        'Charleston, Illinois'
    )
    assert records[0]['date'] == 'September 26-27, 1992'


def test_split_big_minutes_text_handles_month_comma_date_and_mixed_title():
    text = """NOTES:

BALDWIN COUNTY Cooper Book SINGING CONVENTION
Bay Minette City Hall - Bay Minette, Alabama
January, 22-23, 1994
The annual convention was called to order.
"""

    records = split_big_minutes_text(text)

    assert len(records) == 1
    assert records[0]['name'] == 'Baldwin County Cooper Book Singing Convention'
    assert records[0]['date'] == 'January, 22-23, 1994'


def test_normalize_pre1995_header_text_preserves_initials_and_acronyms():
    assert normalize_pre1995_header_text(
        'MR. AND MRS O. H. HANDLEY MEMORIAL SINGING'
    ) == 'Mr. and Mrs O. H. Handley Memorial Singing'
    assert normalize_pre1995_header_text(
        'USA SACRED HARP CONVENTION OF GEORGIA'
    ) == 'USA Sacred Harp Convention of Georgia'
    assert normalize_pre1995_header_text(
        'MT. ZION CHURCH'
    ) == 'Mt. Zion Church'


def test_normalize_pre1995_minutes_marks_likely_song_pages():
    text = (
        'Doug Allison led songs on pages 146 and 268. '
        'Leaders: Kelly Morris led 147 and 114; Laurie Allison, 45, 128.'
    )

    normalized = normalize_pre1995_minutes(text)

    assert '[146-1991]' in normalized
    assert '[268-1991]' in normalized
    assert '[147-1991]' in normalized
    assert '[45-1991]' in normalized


def test_reflow_pre1995_ocr_text_removes_visual_wraps_and_printed_page_numbers():
    text = """The annual singing was called to order
by Velton Chafin leading song on page 33b.
RECESS.
The class resumed with songs on pages 430,
29


542, 385b; Unia B. Howard, 48, 384.
DISMISSED FOR LUNCH.
The class resumed singing."""

    normalized = reflow_pre1995_ocr_text(text)

    assert normalized == (
        'The annual singing was called to order by Velton Chafin leading '
        'song on page 33b.\vRECESS.\vThe class resumed with songs on pages '
        '430, 542, 385b; Unia B. Howard, 48, 384.\v'
        'DISMISSED FOR LUNCH.\vThe class resumed singing.'
    )


def test_reflow_pre1995_ocr_text_removes_isolated_printed_page_number():
    text = """Aver Crider 430,
29


542,385b"""

    # A printed page number borders the blank page break in the OCR.
    assert reflow_pre1995_ocr_text(text) == 'Aver Crider 430, 542,385b'


def test_separate_pre1995_comma_list_leaders_splits_mid_clause_leaders():
    text = (
        'Leaders: Hugh McGraw, [73b-1991], Carol Hanson, [222-1991]; '
        'Tom Hanson, [101-1991], [36b-1991].'
    )

    normalized = separate_pre1995_comma_list_leaders(text)

    assert 'Hugh McGraw, [73b-1991]; Carol Hanson, [222-1991]' in normalized
    assert 'Tom Hanson, [101-1991], [36b-1991]' in normalized


def test_parse_big_minutes_text_parses_normalized_leaders():
    text = """NOTES:

OLD DEKALB COUNTY COURTHOUSE IN DECATUR
Decatur Georgia
Saturday, September 21, 1991
Doug Allison led song on page 335 and E. C. Bowen led the morning prayer.
Doug Allison led songs on pages 146 and 268.
Leaders: Kelly Morris led 147 and 114; Laurie Allison, 45, 128.
"""

    records = parse_big_minutes_text(text)
    leaders = records[0]['parsed_minutes'][0]['leaders']

    assert {'name': 'Doug Allison', 'song': '335', 'book': 1991} in leaders
    assert {'name': 'Kelly Morris', 'song': '147', 'book': 1991} in leaders
    assert {'name': 'Laurie Allison', 'song': '45', 'book': 1991} in leaders


def test_parse_big_minutes_text_handles_comma_list_leader_switches():
    text = """NOTES:

OLD DEKALB COUNTY COURTHOUSE IN DECATUR
Decatur Georgia
Saturday, September 21, 1991
Leaders: Hugh McGraw, 73b, Carol Hanson, 222; Tom Hanson, 101, 36b.
"""

    records = parse_big_minutes_text(text)
    leaders = records[0]['parsed_minutes'][0]['leaders']

    assert {'name': 'Hugh McGraw', 'song': '73b', 'book': 1991} in leaders
    assert {'name': 'Carol Hanson', 'song': '222', 'book': 1991} in leaders
    assert {'name': 'Hugh McGraw', 'song': '222', 'book': 1991} not in leaders
