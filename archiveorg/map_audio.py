import os
import re
import json
import csv
import sqlite3
import difflib
import requests

BASE_URL = 'https://archive.org/download'


def open_db():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'minutes.db'))
    return conn


def read_item(item_id):
    response = requests.get('https://archive.org/metadata/' + item_id)
    data = json.loads(response.text)
    songs = []
    for file in data['files']:
        if 'format' not in file or file['format'] != 'VBR MP3':
            continue

        if len(file['title'].split('.')) < 2:
            # print(file['title'].split('.'))
            continue

        if file['title'].split('.')[2] == 'v02':  # :(
            continue

        title = file['title'].split('.')[-1]
        m = re.search(r'^(\d+[tb]?)', title)
        pagenum = m.group() if m else None
        if not pagenum:
            # print('no pagenum? %s %s' % (file, title))
            continue

        if pagenum[0] == '0':
            pagenum = pagenum[1:]

        url = os.path.join(BASE_URL, item_id, file['name'])
        print('%s,%s' % (pagenum, url))
        songs.append((pagenum, url))
    return songs


def insert_songs(conn, minutes_id, songs_audio):
    print("Parsing %d" % (minutes_id))
    curs = conn.cursor()

    # make lists of recording urls and song ids
    songs = []
    pages = []
    urls = []
    for pagenum, url in songs_audio:
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
    for join_id, song_id in curs:
        if not minutes_songs or minutes_songs[-1] != song_id:
            minutes_songs.append(song_id)
            minutes_ids.append([join_id])
        else:
            minutes_ids[-1].append(join_id)

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

    print('---------')

    conn.commit()
    curs.close()


if __name__ == "__main__":
    conn = open_db()

    curs = conn.cursor()
    reader = csv.reader(open('minutes_to_audio.csv', 'r'))
    minutes = []
    for row in reader:
        name = row[0]
        date = row[1]
        item_id = row[2]
        curs.execute("SELECT id FROM minutes \
                WHERE Name IS ? AND \
                Date IS ?", [name, date])
        id_row = curs.fetchone()
        if id_row:
            minutes_id = id_row[0]
            minutes.append((minutes_id, item_id))
        else:
            print("no minutes: " + row[0])
    curs.close()

    for minutes_id, item_id in minutes:
        songs = read_item(item_id)
        insert_songs(conn, minutes_id, songs)

    conn.close()
