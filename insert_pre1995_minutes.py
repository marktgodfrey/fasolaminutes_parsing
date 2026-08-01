#!/usr/bin/env python
# encoding: utf-8

import argparse
import datetime
import os
import re
import sqlite3

import parse_minutes as minutes_parser
from pre1995_minutes import split_big_minutes_text


MINUTES_COLUMNS = (
    'Name',
    'Location',
    'Date',
    'Minutes',
    'Year',
    'IsDenson',
    'GoodCt',
    'ErrCt',
    'AmbCt',
    'CorrCt',
    'ProbCt',
    'TotalCt',
    'ProbPercent',
    'DensonYear',
    'DateOrdinal',
    'IsVirtual',
)

MONTH_PATTERN = (
    'January|February|March|April|May|June|July|August|September|October|'
    'November|December'
)
FIRST_DATE_PATTERN = re.compile(
    r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?[,]?\s*'
    r'(' + MONTH_PATTERN + r'),?\s+(\d{1,2})',
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r'(\d{4})')


PRE1995_NON_DENSON_OVERRIDES = {
    (
        'OLD DEKALB COUNTY COURTHOUSE IN DECATUR',
        'Decatur Georgia',
        'Saturday, September 21, 1991',
    ),
    (
        'FLORIDA STATE SINGING CONVENTION',
        'Panama City Beach, Florida',
        'November 30--December 1, 1991',
    ),
    (
        'CONCORD PRIMITIVE BAPTIST CHURCH',
        '.7 mile south or Counry Road 14 on Beasley Road, Winfield, Alabama',
        'December 8, 1991',
    ),
    (
        'LITTLE BRANCH PRIMITIVE BAPTIST CHURCH',
        'Albertville, Alabama',
        'December 12, 1991',
    ),
    (
        'MARTIN BLACKMON MEMORIAL',
        'New Hope Primitive Baptist Church - Villa Rica, Georgia',
        'December 29 1991',
    ),
    (
        'CINCINNATI',
        'Northside Christian Church',
        'Wednesday, January 1, 1992',
    ),
    (
        'DUTCH TREAT SINGING',
        'Shadu Grove Church, Winston County, Alabama',
        'January 5, 1992',
    ),
    (
        'WEST GEORGIA COLLEGE SINGING',
        'Food Services Building, Carrollton, Georgia',
        'January 5, 1992',
    ),
    (
        'CHICAGO ANNIVERSARY SINGING',
        'Indian Boundary Park - Chicago, Illinois',
        'Sunday, January 12, 1992',
    ),
    (
        'UNCLE JACK KERR MEMORIAL',
        'Camp Ground Methodist Church- North of Fruithurst, Alabama',
        'January 12, 1992',
    ),
    (
        'ALL-CALIFORNIA SACRED HARP CONVENTION',
        "Women's 20th Century Club, Eagle Rock, California",
        'January 19, 1992',
    ),
    (
        'FOUR - NOTE SINGING',
        'Marion, Kentucky',
        'January 25, 1992',
    ),
    (
        'SOUTHWESTERN BAPTIST THEOLOGICAL SEMINARY',
        'Fort Worth, Texas',
        'January 25, 1991',
    ),
    (
        'GALILLE CONVENTION',
        'Stapleton, Alabama',
        'January 25,26, 1992',
    ),
    (
        'GARRISON MEMORIAL',
        'Oak Grove Primitive Baptist Church - Alpharetta, Georgia',
        'March 15, 1992',
    ),
    (
        'SOUTHWEST TEXAS SACRED HARP CONVENTION',
        'Little Vine Primitive Baptist Church - Austin, Texas',
        'August 29, 30, 1992',
    ),
    (
        'UNIVERSITY OF GEORGIA',
        'Visitor Center Botonical Gardens, Athens, Georgia',
        'February 22, 23, 1992',
    ),
    (
        'SOUTHEAST TEXAS CONVENTION',
        'Salem Lutheren Church, Brenham, Texas',
        'October 24, 1992',
    ),
    (
        'FOUR - NOTE SINGING',
        'Marion, Kentucky',
        'January 23, 1993',
    ),
    (
        'BALDWIN COUNTY SACRED HARP SINGING CONVENTION',
        'Bay Minette City Hall— Bay Minette Alabama',
        'January 23 -24, 1993',
    ),
    (
        'UNIVERSITY OF GEORGIA',
        'Visitor Center Botonical Gardens, Athens, Gerogia',
        'February 28, 1993',
    ),
    (
        'GARRISON MEMORIAL',
        'Oak Grove Primitive Baptist Church _ Alpharetta, Georgia',
        'March 21, 1993',
    ),
    (
        'SOUTHEAST TEXAS SINGING',
        'Salem Lutheran Church, Brenham, Texas',
        'October 23, 1993',
    ),
    (
        'EAST TEXAS SACRED HARP SINGING CONVENTION',
        'Henderson, Texas',
        'August 7 and 8, 1993',
    ),
    (
        'BALDWIN COUNTY Cooper Book SINGING CONVENTION',
        'Bay Minette City Hall - Bay Minette, Alabama',
        'January, 22-23, 1994',
    ),
    (
        'UNIVERSITY OF GEORGIA',
        'Visitor Center-Botanical Gardens, Athens Georgia',
        'February 27, 1994',
    ),
    (
        'EAST TEXAS SACRED HARP SINGING CONVENTION',
        'Community Center Building - Henderson, Texas',
        'August 13, 14, 1994',
    ),
    (
        'GARRISON MEMORIAL (COOPER BOOK)',
        "Oak Grove Primitive Baptist Church Alpharetta, Georgia, B'ham Road",
        'March 20, 1994',
    ),
    (
        'SOUTHEAST TEXAS SINGING',
        'Salem Lutheran Church, Brenham, Texas',
        'October 22, 1994',
    ),
    (
        'FLORIDA STATE CONVENTION',
        'Holiday Inn, Panama City, Florida',
        'December 3-4, 1994',
    ),
}


PRE1995_DATE_CORRECTIONS = {
    (
        'ORIGINAL DUTCH SINGING',
        'West Georgia College, Carrolton, Georgia',
        'January 3, 1393',
    ): 'January 3, 1993',
    (
        'SHADY GROVE (KEETON CEMETARY)',
        'Walker County, Alabama',
        'May 2, 1992',
    ): 'May 2, 1993',
    (
        'THE LOG CABIN SACRED HARP SINGING',
        'North of Double Springs, Alabama',
        'March 15, 1991',
    ): 'March 15, 1992',
    (
        'DUTTON AND GREEN MEMORIAL',
        'New Flatwoods Primtive Baptist Church, South of Nauvoo, Alabama',
        'July 4, 1991',
    ): 'July 4, 1993',
    (
        'WINSTON COUNTY CONVENTION',
        'Shady Grove Church',
        'September 22, 1991',
    ): 'September 22, 1992',
    (
        'LIBERTY HILL BAPTIST CHURCH',
        'Boaz, Alabama',
        'September 26, 1994',
    ): 'September 26, 1993',
    (
        'JORDAN CHAPEL',
        'Newell, Randolph County, Alabama',
        'October 23, 1991',
    ): 'October 23, 1992',
    (
        'COY PUTMAN MEMORIAL',
        'Rocky Mount Primitive Baptist Church, Arab, Alabama',
        'October 23, 1193',
    ): 'October 23, 1993',
    (
        'FAYETTE COUNTY CONVENTION',
        'Bevill State Junior College, Fayette, Alabama',
        'August 7, 1934',
    ): 'August 7, 1994',
    (
        'GUM POND CHURCH',
        'Morgan County, Alabama',
        'September 25, 1974',
    ): 'September 25, 1994',
}


def infer_minutes_year(path):
    filename = os.path.basename(path)
    match = re.search(r'(\d{4})-big-minutes|Big_Minutes_(\d{4})', path)
    if match:
        return int(match.group(1) or match.group(2))

    match = re.search(r'(\d{4})', filename)
    if match:
        return int(match.group(1))

    return None


def date_ordinal(date_text):
    year_matches = YEAR_PATTERN.findall(date_text)
    first_date = FIRST_DATE_PATTERN.search(date_text)
    if not year_matches or not first_date:
        return None

    month = first_date.group(1).title()
    day = int(first_date.group(2))
    year = int(year_matches[-1])

    try:
        return datetime.datetime.strptime(
            '%s %d %d' % (month, day, year),
            '%B %d %Y',
        ).toordinal()
    except ValueError:
        return None


def reset_parser_caches():
    minutes_parser.LEADERS.clear()
    minutes_parser.SONGS.clear()
    minutes_parser.ALIASES.clear()
    minutes_parser.INVALID.clear()


def normalize_existing_leaders(conn):
    rows = conn.execute(
        'SELECT id, name FROM leaders WHERE name IS NOT NULL'
    ).fetchall()
    groups = {}
    for leader_id, name in rows:
        normalized = minutes_parser.normalize_leader_name(name)
        groups.setdefault(normalized, []).append((leader_id, name))

    renamed = 0
    merged = 0
    for normalized, leaders in groups.items():
        exact_ids = [
            leader_id for leader_id, name in leaders
            if name == normalized
        ]
        keep_id = min(exact_ids) if exact_ids else min(
            leader_id for leader_id, _name in leaders
        )

        keep_name = conn.execute(
            'SELECT name FROM leaders WHERE id=?',
            [keep_id],
        ).fetchone()[0]
        if keep_name != normalized:
            conn.execute(
                'UPDATE leaders SET name=? WHERE id=?',
                [normalized, keep_id],
            )
            renamed += 1

        for leader_id, _name in leaders:
            if leader_id == keep_id:
                continue
            conn.execute(
                'UPDATE song_leader_joins SET leader_id=? WHERE leader_id=?',
                [keep_id, leader_id],
            )
            conn.execute(
                'UPDATE leader_name_aliases SET leader_id=? WHERE leader_id=?',
                [keep_id, leader_id],
            )
            conn.execute('DELETE FROM leaders WHERE id=?', [leader_id])
            merged += 1

    return {'renamed': renamed, 'merged': merged}


def seed_existing_leaders(conn):
    for leader_id, name in conn.execute('SELECT id, name FROM leaders'):
        minutes_parser.LEADERS[name] = leader_id


def build_minutes_values(record, minutes_year, denson_year):
    name_upper = record['name'].upper()
    original_key = (
        record.get('raw_name', record['name']),
        record.get('raw_location', record['location']),
        record.get('raw_date', record['date']),
    )
    date = PRE1995_DATE_CORRECTIONS.get(original_key, record['date'])
    is_denson = 0 if (
        'SOUTHWEST TEXAS' in name_upper
        or '(COOPER BOOK)' in name_upper or '(COOPER BOCK)' in name_upper
        or original_key in PRE1995_NON_DENSON_OVERRIDES
    ) else 1
    return {
        'Name': record['name'],
        'Location': record['location'],
        'Date': date,
        'Minutes': record['normalized_minutes'],
        'Year': minutes_year,
        'IsDenson': is_denson,
        'GoodCt': 0,
        'ErrCt': 0,
        'AmbCt': 0,
        'CorrCt': 0,
        'ProbCt': 0,
        'TotalCt': 0,
        'ProbPercent': 0,
        'DensonYear': denson_year,
        'DateOrdinal': date_ordinal(date),
        'IsVirtual': 0,
    }


def find_existing_minutes_id(conn, values):
    row = conn.execute(
        '''
        SELECT id FROM minutes
        WHERE Name=? AND Location=? AND Date=? AND Year=? AND DensonYear=?
        ''',
        (
            values['Name'],
            values['Location'],
            values['Date'],
            values['Year'],
            values['DensonYear'],
        ),
    ).fetchone()
    return row[0] if row else None


def upsert_minutes_row(conn, values):
    minutes_id = find_existing_minutes_id(conn, values)
    if minutes_id:
        assignments = ', '.join('%s=?' % column for column in MINUTES_COLUMNS)
        conn.execute(
            'UPDATE minutes SET %s WHERE id=?' % assignments,
            [values[column] for column in MINUTES_COLUMNS] + [minutes_id],
        )
        conn.execute('DELETE FROM song_leader_joins WHERE minutes_id=?', [minutes_id])
        return minutes_id, False

    placeholders = ','.join('?' for _ in MINUTES_COLUMNS)
    conn.execute(
        'INSERT INTO minutes (%s) VALUES (%s)' % (
            ','.join(MINUTES_COLUMNS),
            placeholders,
        ),
        [values[column] for column in MINUTES_COLUMNS],
    )
    return conn.execute('SELECT last_insert_rowid()').fetchone()[0], True


def insert_big_minutes_file(
        conn,
        path,
        minutes_year=None,
        denson_year=1991,
        limit=None,
        dry_run=False):
    if minutes_year is None:
        minutes_year = infer_minutes_year(path)
    if minutes_year is None:
        raise ValueError('Could not infer minutes year from %s' % path)

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        records = split_big_minutes_text(f.read(), book_year=denson_year)

    if limit:
        records = records[:limit]

    reset_parser_caches()
    leader_cleanup = {'renamed': 0, 'merged': 0}
    if not dry_run:
        leader_cleanup = normalize_existing_leaders(conn)
    seed_existing_leaders(conn)

    inserted = 0
    updated = 0
    joins_before = conn.execute('SELECT COUNT(*) FROM song_leader_joins').fetchone()[0]

    for record in records:
        values = build_minutes_values(record, minutes_year, denson_year)
        parsed = minutes_parser.parse_minutes(values['Minutes'])

        if dry_run:
            leader_count = sum(len(session['leaders']) for session in parsed)
            print(
                '%s | %s | %s | %d sessions, %d leaders' % (
                    values['Name'],
                    values['Location'],
                    values['Date'],
                    len(parsed),
                    leader_count,
                )
            )
            continue

        minutes_id, was_inserted = upsert_minutes_row(conn, values)
        if was_inserted:
            inserted += 1
        else:
            updated += 1

        if values['IsDenson']:
            minutes_parser.insert_minutes(conn, parsed, minutes_id)

    if dry_run:
        return {
            'records': len(records),
            'inserted': 0,
            'updated': 0,
            'joins': 0,
            'leaders_renamed': 0,
            'leaders_merged': 0,
        }

    joins_after = conn.execute('SELECT COUNT(*) FROM song_leader_joins').fetchone()[0]
    return {
        'records': len(records),
        'inserted': inserted,
        'updated': updated,
        'joins': joins_after - joins_before,
        'leaders_renamed': leader_cleanup['renamed'],
        'leaders_merged': leader_cleanup['merged'],
    }


def main():
    parser = argparse.ArgumentParser(
        description='Insert pre-1995 Big Minutes OCR into a minutes database.'
    )
    parser.add_argument('path')
    parser.add_argument('--db', default='minutes_pre95.db')
    parser.add_argument('--year', type=int, default=None)
    parser.add_argument('--denson-year', type=int, default=1991)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        result = insert_big_minutes_file(
            conn,
            args.path,
            minutes_year=args.year,
            denson_year=args.denson_year,
            limit=args.limit,
            dry_run=args.dry_run,
        )
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(
        'records=%(records)d inserted=%(inserted)d updated=%(updated)d '
        'joins_delta=%(joins)d leaders_renamed=%(leaders_renamed)d '
        'leaders_merged=%(leaders_merged)d' % result
    )


if __name__ == '__main__':
    main()
