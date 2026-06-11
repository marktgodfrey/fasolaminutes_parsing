#!/usr/bin/env python3
import csv
import difflib
import json
import os
import re
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def extract_pagenum(title):
    book_prefix = (
        r'(?:SH|Sacred Harp|Denson|Cooper|CH|Christian Harmony|CSH|'
        r'Colored Sacred Harp)'
    )
    if re.search(r'^\d+\s+' + book_prefix + r'\b', title, re.IGNORECASE):
        return None

    m = re.search(r'^(\d+[tb]?)\b', title, re.IGNORECASE)
    if not m:
        m = re.search(
            r'^' + book_prefix + r'\s+(\d+[tb]?)\b',
            title,
            re.IGNORECASE,
        )

    pagenum = m.group(1) if m else None
    if pagenum and pagenum[0] == '0':
        pagenum = pagenum[1:]

    return pagenum


def open_db():
    db_path = os.environ.get(
        'MINUTES_DB',
        os.path.join(os.path.dirname(__file__), '..', 'minutes.db'),
    )
    return sqlite3.connect(db_path)


def read_tracks(path):
    with open(path, 'r', encoding='utf-8') as f:
        tracks = json.load(f)

    songs = []
    for track in tracks:
        title = track.get('title', '')
        pagenum = extract_pagenum(title)
        if not pagenum:
            print('no pagenum: %s' % title)
            continue

        url = track.get('src')
        if not url:
            print('missing src: %s' % title)
            continue

        songs.append((pagenum, url))

    return songs


def resolve_song_id(curs, book_year, pagenum):
    pagenum = pagenum.lower()
    if pagenum[-1:] in ('t', 'b'):
        altpage = pagenum[:-1]
    else:
        altpage = pagenum + 't'

    curs.execute(
        """
        SELECT songs.id
        FROM songs
        INNER JOIN book_song_joins ON songs.id = book_song_joins.song_id
        INNER JOIN books ON books.id = book_song_joins.book_id
        WHERE books.year == ? AND page_num IN (?, ?)
        """,
        [book_year, pagenum, altpage],
    )
    row = curs.fetchone()
    return (row[0], pagenum) if row else (None, pagenum)


def insert_songs(conn, minutes_id, book_year, songs_audio, label, check_seq=True):
    print('Parsing %s minutes_id=%s book_year=%s' % (label, minutes_id, book_year))
    curs = conn.cursor()

    songs = []
    pages = []
    urls = []
    for pagenum, url in songs_audio:
        song_id, clean_pagenum = resolve_song_id(curs, book_year, pagenum)
        if song_id:
            songs.append(song_id)
            urls.append(url)
            pages.append(clean_pagenum)
        else:
            print('no song id: ' + pagenum)

    updates = 0
    skips = 0
    if check_seq:
        minutes_songs = []
        minutes_ids = []
        curs.execute(
            'SELECT id, song_id FROM song_leader_joins WHERE minutes_id=?',
            [minutes_id],
        )
        for join_id, song_id in curs:
            if not minutes_songs or minutes_songs[-1] != song_id:
                minutes_songs.append(song_id)
                minutes_ids.append([join_id])
            else:
                minutes_ids[-1].append(join_id)

        matcher = difflib.SequenceMatcher(a=songs, b=minutes_songs)
        last_a = 0
        for a, b, n in matcher.get_matching_blocks():
            for pagenum, url in zip(pages[last_a:a], urls[last_a:a]):
                skips += 1
                print('skip:   %5s %s' % (pagenum, url))
            last_a = a + n

            for pagenum, url, join_ids in zip(
                pages[a:a + n],
                urls[a:a + n],
                minutes_ids[b:b + n],
            ):
                updates += len(join_ids)
                for join_id in join_ids:
                    curs.execute(
                        'UPDATE song_leader_joins SET audio_url=? WHERE id=?',
                        (url, join_id),
                    )
                print('update: %5s %5r %s' % (pagenum, join_ids, url))
    else:
        minutes_ids = {}
        # TODO: there's a bug here if there's multiple lessons for the same song, eg minutes_id=7128 song_id=280
        for song_id in songs:
            curs.execute("SELECT id FROM song_leader_joins WHERE minutes_id=? AND song_id=?", [minutes_id, song_id])
            minutes_ids[song_id] = []
            for join_id, in curs:
                minutes_ids[song_id].append(join_id)
            if len(minutes_ids[song_id]) == 0:
                print('lesson not found for song: %s' % song_id)

        for pagenum, song_id, url in zip(pages, songs, urls):
            join_ids = minutes_ids[song_id]
            updates += len(join_ids)
            for id in join_ids:
                curs.execute("UPDATE song_leader_joins SET audio_url=? WHERE id=?", (url, id))
            print("update: %5s %5r %s" % (pagenum, join_ids, url))

    conn.commit()
    curs.close()
    print('summary: updates=%s skips=%s' % (updates, skips))
    print('---------')
    return updates, skips


def read_minutes_to_audio(csv_path):
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        for row in csv.reader(f):
            if not row or row[0].startswith('#'):
                continue
            if len(row) != 4:
                raise ValueError('expected 4 columns in %s: %r' % (csv_path, row))
            yield row


def find_minutes(conn, name, date):
    curs = conn.cursor()
    curs.execute(
        """
        SELECT id, DensonYear
        FROM minutes
        WHERE Name IS ? AND Date IS ?
        """,
        [name, date],
    )
    rows = curs.fetchall()
    curs.close()
    return rows

def str_to_bool(s):
    return s.strip().capitalize() == "true"

if __name__ == '__main__':
    csv_path = BASE_DIR / 'minutes_to_audio.csv'
    conn = open_db()

    total_updates = 0
    total_skips = 0
    for name, date, filename, check_seq in read_minutes_to_audio(csv_path):
        rows = find_minutes(conn, name, date)
        if not rows:
            print('no minutes: %r %r' % (name, date))
            continue
        if len(rows) > 1:
            print('ambiguous minutes: %r %r ids=%r' % (
                name,
                date,
                [row[0] for row in rows],
            ))
            continue

        check_seq = str_to_bool(check_seq)

        minutes_id, book_year = rows[0]
        tracks_path = BASE_DIR / filename
        songs_audio = read_tracks(tracks_path)
        label = '%s / %s / %s' % (name, date, filename)
        updates, skips = insert_songs(conn, minutes_id, book_year, songs_audio, label, check_seq=check_seq)
        total_updates += updates
        total_skips += skips

    conn.close()
    print('total: updates=%s skips=%s' % (total_updates, total_skips))
