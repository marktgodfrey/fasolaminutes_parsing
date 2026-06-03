#!/usr/bin/env python
# encoding: utf-8

import argparse
import csv
import json
import re
import sys

from parse_minutes import parse_minutes


MONTH_PATTERN = (
    'January|February|March|April|May|June|July|August|September|October|'
    'November|December'
)

DATE_PATTERN = re.compile(
    r'^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?[,]?\s*'
    r'(?:' + MONTH_PATTERN + r'),?\s+'
    r'\d{1,2}'
    r'(?:\s*(?:,|--|-|to)\s*(?:' + MONTH_PATTERN + r')?\s*\d{1,2})?'
    r',?\s*\d{4}$',
    re.IGNORECASE,
)

UPPER_TITLE_PATTERN = re.compile(r'^[A-Z0-9][A-Z0-9\s&\'().,#/-]+$')
PAGE_TOKEN_PATTERN = re.compile(r'\b(\d{1,3}[tb]?)\b')
PAGE_PROSE_PATTERN = re.compile(
    r'\b(pages?|pg\.?)\s+(?:on\s+)?(\d{1,3}[tb]?)\b',
    re.IGNORECASE,
)
ADDRESS_ENTRY_PATTERN = re.compile(
    r"^[A-Z][A-Za-z'.-]+,\s+(?:[A-Z][A-Za-z'.&-]+|[A-Z]\.)\b"
)
NAME_BEFORE_PAGE_PATTERN = (
    r"(?:[A-Z][A-Za-z’'.-]*|[A-Z]\.)"
    r"(?:\s+(?:and\s+)?(?:[A-Z][A-Za-z’'.-]*|[A-Z]\.)){0,4}"
)


def _looks_like_title(line):
    stripped = line.strip()
    if not stripped:
        return False
    if DATE_PATTERN.match(stripped):
        return False
    if re.match(r'^SINGING HELD IN \d{4}$', stripped, re.IGNORECASE):
        return False
    if UPPER_TITLE_PATTERN.match(stripped):
        return True

    letters = re.findall(r'[A-Za-z]', stripped)
    if not letters:
        return False
    uppercase = sum(1 for letter in letters if letter.isupper())
    return (
        uppercase / float(len(letters)) >= 0.60
        and bool(re.search(r'\b(SINGING|CONVENTION|CHURCH|MEMORIAL)\b', stripped))
    )


def _title_start(lines, location_idx):
    idx = location_idx - 1
    while idx >= 0 and not lines[idx].strip():
        idx -= 1

    title_idxs = []
    while idx >= 0 and _looks_like_title(lines[idx]) and len(title_idxs) < 4:
        title_idxs.append(idx)
        idx -= 1

    if not title_idxs:
        return None

    return min(title_idxs)


def find_big_minutes_headers(text, start_after='NOTES:'):
    """Find likely three-line singing headers in old Big Minutes OCR text."""
    lines = text.splitlines()
    start_idx = 0
    if start_after:
        for idx, line in enumerate(lines):
            if line.strip().upper() == start_after.upper():
                start_idx = idx + 1
                break

    headers = []
    for idx in range(start_idx, len(lines)):
        date = lines[idx].strip()
        if not DATE_PATTERN.match(date):
            continue

        location_idx = idx - 1
        while location_idx >= start_idx and not lines[location_idx].strip():
            location_idx -= 1
        if location_idx < start_idx:
            continue

        title_start = _title_start(lines, location_idx)
        if title_start is None:
            continue

        title = ' '.join(
            line.strip() for line in lines[title_start:location_idx]
            if line.strip()
        )
        location = lines[location_idx].strip()
        if not title or not location:
            continue

        headers.append({
            'name': title,
            'location': location,
            'date': date,
            'line': title_start + 1,
            'start': title_start,
            'body_start': idx + 1,
        })

    return headers


def split_big_minutes_text(text, book_year=1991):
    """Split one OCR yearbook text into per-singing records."""
    lines = text.splitlines()
    headers = find_big_minutes_headers(text)
    minutes_end = _find_minutes_end(lines, headers[-1]['body_start'] if headers else 0)
    records = []

    for idx, header in enumerate(headers):
        end = headers[idx + 1]['start'] if idx + 1 < len(headers) else minutes_end
        raw_text = '\n'.join(lines[header['body_start']:end]).strip()
        records.append({
            'name': header['name'],
            'location': header['location'],
            'date': header['date'],
            'line': header['line'],
            'minutes': raw_text,
            'normalized_minutes': normalize_pre1995_minutes(raw_text, book_year),
            'book_year': book_year,
        })

    return records


def _find_minutes_end(lines, start_idx=0):
    for idx in range(start_idx, len(lines)):
        if not ADDRESS_ENTRY_PATTERN.match(lines[idx].strip()):
            continue

        address_count = 0
        scan_end = min(len(lines), idx + 8)
        for scan_idx in range(idx, scan_end):
            if not ADDRESS_ENTRY_PATTERN.match(lines[scan_idx].strip()):
                break
            address_count += 1

        if address_count >= 4:
            return idx

    for idx in range(start_idx, len(lines)):
        line = lines[idx]
        if not re.match(r'^\d{1,3}$', line.strip()):
            continue

        next_idx = idx + 1
        while next_idx < len(lines) and not lines[next_idx].strip():
            next_idx += 1

        if next_idx < len(lines) and ADDRESS_ENTRY_PATTERN.match(lines[next_idx].strip()):
            return idx

    return len(lines)


def _valid_page_token(token):
    page = token[:-1] if token[-1:] in ('t', 'b') else token
    if not page.isdigit():
        return False
    page_num = int(page)
    return 30 <= page_num <= 573


def _format_page_token(token, book_year):
    if '-' in token:
        return token
    return '[%s-%s]' % (token, book_year)


def normalize_pre1995_minutes(text, book_year=1991):
    """Convert likely old-style Denson page references to parser syntax."""
    text = PAGE_PROSE_PATTERN.sub(
        lambda m: '%s %s' % (m.group(1), _format_page_token(m.group(2), book_year)),
        text,
    )

    def replace_token(match):
        token = match.group(1)
        if not _valid_page_token(token):
            return token

        before = text[max(0, match.start() - 1):match.start()]
        after = text[match.end():match.end() + 1]
        if before == '[' or after == ']':
            return token

        return _format_page_token(token, book_year)

    text = PAGE_TOKEN_PATTERN.sub(replace_token, text)
    return separate_pre1995_comma_list_leaders(text, book_year)


def separate_pre1995_comma_list_leaders(text, book_year=1991):
    """Add separators when old comma-list minutes switch leaders mid-clause."""
    page = r'\[\d{1,3}[tb]?-%s\]' % book_year
    return re.sub(
        r'(%s)[,\s]+(?=(%s),?\s+%s)' % (
            page,
            NAME_BEFORE_PAGE_PATTERN,
            page,
        ),
        r'\1; ',
        text,
    )


def parse_big_minutes_text(text, book_year=1991):
    records = split_big_minutes_text(text, book_year=book_year)
    for record in records:
        record['parsed_minutes'] = parse_minutes(record['normalized_minutes'])
    return records


def _summary_rows(records):
    for record in records:
        leader_count = sum(
            len(session['leaders']) for session in record.get('parsed_minutes', [])
        )
        yield {
            'line': record['line'],
            'name': record['name'],
            'location': record['location'],
            'date': record['date'],
            'sessions': len(record.get('parsed_minutes', [])),
            'leaders': leader_count,
        }


def main():
    parser = argparse.ArgumentParser(
        description='Split and parse pre-1995 Big Minutes OCR text.'
    )
    parser.add_argument('path')
    parser.add_argument('--book-year', type=int, default=1991)
    parser.add_argument(
        '--format',
        choices=('summary', 'json', 'tsv'),
        default='summary',
    )
    args = parser.parse_args()

    with open(args.path, 'r', encoding='utf-8', errors='replace') as f:
        records = parse_big_minutes_text(f.read(), book_year=args.book_year)

    if args.format == 'json':
        print(json.dumps(records, indent=2))
        return

    rows = list(_summary_rows(records))
    if args.format == 'tsv':
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=('line', 'name', 'location', 'date', 'sessions', 'leaders'),
            delimiter='\t',
        )
        writer.writeheader()
        writer.writerows(rows)
        return

    print('found %d singings' % len(rows))
    for row in rows[:20]:
        print(
            '%(line)d: %(name)s | %(location)s | %(date)s | '
            '%(sessions)d sessions, %(leaders)d leaders' % row
        )
    if len(rows) > 20:
        print('... %d more' % (len(rows) - 20))


if __name__ == '__main__':
    main()
