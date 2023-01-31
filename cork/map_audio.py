# -*- coding: utf-8 -*-
import sqlite3
import difflib
import os
import re
import csv
import requests


def open_db():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'minutes.db'))
    return conn


def parse_csv(conn, filename, minutes_id):
    with open(filename, 'r') as f:
        print('parsing csv file: %s' % filename)
        song_data = list(csv.reader(f))
        parse_section(conn, minutes_id, song_data)


def parse_section(conn, minutes_id, song_data):
    print("Parsing %d" % (minutes_id))
    curs = conn.cursor()

    # make lists of recording urls and song ids
    songs = []
    pages = []
    urls = []
    for pagenum, url in song_data:
        pagenum = pagenum.lower()
        if pagenum[-1:] in ('t', 'b'):
            altpage = pagenum[:-1]
        else:
            altpage = pagenum + 't'

        curs.execute("SELECT id FROM songs WHERE PageNum IN (?, ?)", [pagenum, altpage])
        row = curs.fetchone()
        if row:
            song_id = row[0]
            songs.append(song_id)
            urls.append(url)
            pages.append(pagenum)
        else:
            print("no song id: " + pagenum)

    # make list of songs and ids from the minutes
    minutes_songs = []
    minutes_ids = []
    curs.execute("SELECT id, song_id FROM song_leader_joins WHERE minutes_id=?", [minutes_id])
    for id, song_id in curs:
        if not minutes_songs or minutes_songs[-1] != song_id:
            minutes_songs.append(song_id)
            minutes_ids.append([id])
        else:
            minutes_ids[-1].append(id)

    # get the longest subsequence from recordings and minutes
    s = difflib.SequenceMatcher(a=songs, b=minutes_songs)
    last_a = 0
    for a, b, n in s.get_matching_blocks():
        for pagenum, url in zip(pages[last_a:a], urls[last_a:a]):
            print("skip: %5s %s" % (pagenum, url))
        last_a = a+n
        for pagenum, url, join_ids in zip(pages[a:a+n], urls[a:a+n], minutes_ids[b:b+n]):
            for id in join_ids:
                curs.execute("UPDATE song_leader_joins SET audio_url=? WHERE id=?", (url, id))
            print("update: %5s %5r %s" % (pagenum, join_ids, url))

            # # check the URL exists
            # resp = requests.head(url)
            # if resp.status_code != 200:
            #     print('missing audio! ' + url)

    conn.commit()
    curs.close()


if __name__ == '__main__':
    conn = open_db()

    curs = conn.cursor()
    reader = csv.reader(open('minutes_to_audio.csv', 'r'))
    minutes = []
    for row in reader:
        date = row[0]
        filename = row[1]
        curs.execute("SELECT id FROM minutes \
            WHERE Name LIKE 'Ireland%Convention' AND \
            Date LIKE ?", [date])
        id_row = curs.fetchone()
        if row:
            minutes_id = id_row[0]
            minutes.append((minutes_id, row[1]))
        else:
            print("no minutes for date: " + row[0])
    curs.close()

    print(minutes)
    for minutes_id, filename in minutes:
        parse_csv(conn, filename, minutes_id)

    conn.close()
