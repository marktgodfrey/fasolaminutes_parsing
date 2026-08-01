import os
import re
import json
import csv
import sqlite3
import difflib
import time
import tempfile
import xml.etree.ElementTree as ET
from urllib.parse import quote
import requests

BASE_URL = 'https://archive.org/download'
METADATA_TIMEOUT = 30
METADATA_MAX_ATTEMPTS = 4
DEFAULT_METADATA_CACHE = os.path.join(os.path.dirname(__file__), 'metadata_cache')


def extract_pagenum(title):
    book_prefix = r'(?:SH|Sacred Harp|Denson|Cooper|CH|Christian Harmony|CSH|Colored Sacred Harp)'
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
    conn = sqlite3.connect(db_path)
    return conn


def metadata_cache_path(item_id, cache_dir=None):
    cache_dir = cache_dir or os.environ.get(
        'ARCHIVEORG_METADATA_CACHE',
        DEFAULT_METADATA_CACHE,
    )
    return os.path.join(cache_dir, quote(item_id, safe='') + '.json')


def read_cached_metadata(item_id, cache_dir=None):
    path = metadata_cache_path(item_id, cache_dir)
    try:
        with open(path, 'r') as cache_file:
            data = json.load(cache_file)
        if not isinstance(data, dict) or 'files' not in data:
            raise ValueError('cached response has no files metadata')
        return data
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        print('ignoring bad archive.org metadata cache for %s: %s' % (
            item_id,
            exc,
        ))
        return None


def write_cached_metadata(item_id, data, cache_dir=None):
    path = metadata_cache_path(item_id, cache_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=os.path.dirname(path),
            prefix='.metadata-',
            suffix='.tmp',
            delete=False,
        ) as cache_file:
            temp_path = cache_file.name
            json.dump(data, cache_file)
        os.replace(temp_path, path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def fetch_with_retries(item_id, source_name, load):
    last_error = None
    for attempt in range(1, METADATA_MAX_ATTEMPTS + 1):
        try:
            return load()
        except (requests.RequestException, ET.ParseError, ValueError, RuntimeError) as exc:
            last_error = exc
            if attempt < METADATA_MAX_ATTEMPTS:
                delay = 2 ** (attempt - 1)
                print('archive.org %s attempt %d/%d failed for %s: %s; retrying in %ds' % (
                    source_name,
                    attempt,
                    METADATA_MAX_ATTEMPTS,
                    item_id,
                    exc,
                    delay,
                ))
                time.sleep(delay)

    raise RuntimeError(
        'archive.org %s failed after %d attempts for %s: %s' % (
            source_name,
            METADATA_MAX_ATTEMPTS,
            item_id,
            last_error,
        )
    )


def fetch_partial_files(item_id):
    url = 'https://archive.org/metadata/%s/files?extended_err=1' % item_id

    def load():
        response = requests.get(url, timeout=METADATA_TIMEOUT)
        if response.status_code >= 400:
            raise RuntimeError('HTTP %s' % response.status_code)
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError('response is not a JSON object')
        if 'result' not in data:
            error = data.get('error', 'response has keys %s' % sorted(data.keys()))
            raise RuntimeError(str(error))
        if not isinstance(data['result'], list):
            raise RuntimeError('files result is not a list')
        return data['result']

    return fetch_with_retries(item_id, 'partial files metadata', load)


def fetch_files_xml(item_id):
    filename = quote(item_id, safe='') + '_files.xml'
    url = '%s/%s/%s' % (BASE_URL, quote(item_id, safe=''), filename)

    def load():
        response = requests.get(url, timeout=METADATA_TIMEOUT)
        if response.status_code >= 400:
            raise RuntimeError('HTTP %s' % response.status_code)
        root = ET.fromstring(response.content)
        if root.tag != 'files':
            raise RuntimeError('XML root is %s, not files' % root.tag)
        files = []
        for node in root.findall('file'):
            file_data = dict(node.attrib)
            for child in node:
                file_data[child.tag] = child.text
            files.append(file_data)
        return files

    return fetch_with_retries(item_id, 'files.xml metadata', load)


def fetch_item_metadata(item_id, cache_dir=None):
    refresh = os.environ.get('ARCHIVEORG_REFRESH_METADATA', '').lower() in (
        '1', 'true', 'yes',
    )
    if not refresh:
        cached_data = read_cached_metadata(item_id, cache_dir)
        if cached_data is not None:
            return cached_data

    try:
        files = fetch_partial_files(item_id)
    except RuntimeError as partial_error:
        print('%s; falling back to canonical files.xml' % partial_error)
        try:
            files = fetch_files_xml(item_id)
        except RuntimeError as xml_error:
            raise RuntimeError('%s; fallback also failed: %s' % (
                partial_error,
                xml_error,
            )) from xml_error

    data = {'files': files}
    try:
        write_cached_metadata(item_id, data, cache_dir)
    except (OSError, TypeError) as exc:
        print('could not cache archive.org metadata for %s: %s' % (
            item_id,
            exc,
        ))
    return data


def read_item(item_id, cache_dir=None):
    data = fetch_item_metadata(item_id, cache_dir)

    songs = []
    for file in data['files']:
        if 'format' not in file or file['format'] != 'VBR MP3':
            continue

        if 'title' not in file:
            print(f'missing title! {item_id} {file}')
            continue

        title = file['title']
        if 'mosquito' in item_id:
            comps = title.split('.')
            if len(comps) < 2:
                continue

            if len(comps) > 2 and comps[2] == 'v02':  # :(
                continue

            title = title.split('.')[-1]

        pagenum = extract_pagenum(title)
        if not pagenum:
            # print('no pagenum? %s %s' % (file, title))
            continue

        url = os.path.join(BASE_URL, item_id, file['name'])
        print('%s,%s' % (pagenum, url))
        songs.append((pagenum, url))
    return songs


def insert_songs(conn, minutes_id, book_year, songs_audio, check_seq=True):
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

        curs.execute("SELECT songs.id FROM songs \
                    INNER JOIN book_song_joins ON songs.id = book_song_joins.song_id \
                    INNER JOIN books ON books.id = book_song_joins.book_id \
                    WHERE books.year == ? AND page_num IN (?, ?)", [book_year, pagenum, altpage])
        row = curs.fetchone()
        if row:
            song_id = row[0]
            songs.append(song_id)
            urls.append(url)
            pages.append(pagenum)
        else:
            print("no song id: " + pagenum)

    if check_seq:
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
            for id in join_ids:
                curs.execute("UPDATE song_leader_joins SET audio_url=? WHERE id=?", (url, id))
            print("update: %5s %5r %s" % (pagenum, join_ids, url))
    print('---------')

    conn.commit()
    curs.close()


def map_items(conn, minutes):
    failures = []
    for minutes_id, item_id, book_year in minutes:
        try:
            songs = read_item(item_id)
        except RuntimeError as exc:
            print('skipping archive.org item %s after metadata failure: %s' % (
                item_id,
                exc,
            ))
            failures.append((item_id, str(exc)))
            continue
        insert_songs(
            conn,
            minutes_id,
            book_year,
            songs,
            check_seq=(item_id != 'sacredharp2025edition'),
        )
    return failures


if __name__ == "__main__":
    conn = open_db()

    curs = conn.cursor()
    reader = csv.reader(open('minutes_to_audio.csv', 'r'))
    minutes = []
    for row in reader:
        name = row[0]
        date = row[1]
        item_id = row[2]
        curs.execute("SELECT id, DensonYear FROM minutes \
                WHERE Name IS ? AND \
                Date IS ?", [name, date])
        id_row = curs.fetchone()
        if id_row:
            minutes_id = id_row[0]
            book_year = id_row[1]
            minutes.append((minutes_id, item_id, book_year))
        else:
            print("no minutes: " + row[0])
    curs.close()

    failures = map_items(conn, minutes)
    conn.close()

    if failures:
        details = '\n'.join('  %s: %s' % failure for failure in failures)
        raise SystemExit(
            'archive.org metadata failed for %d item(s):\n%s' % (
                len(failures),
                details,
            )
        )
