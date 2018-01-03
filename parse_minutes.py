#!/usr/bin/env python
# encoding: utf-8

import re
import os
import csv
import util

bad_words = [
    'Chairman',
    'Chairperson',
    'Chairwoman',
    'Chairmen',
    'Chair',
    'Chairlady',
    'Chairpersons',
    'Chairs',
    'Singing',
    'Secretary',
    'Secretaries',
    'Director',
    'Committee',
    'Committees',
    'Convention',
    'Sacred',
    'Musical',
    'Methodist',
    'Baptist',
    'Episcopal',
    'Anglican',
    'Mennonite',
    'Catholic',
    'Pastor',
    'Minister',
    'Ministry',
    'National',
    'Library',
    'Shape',
    'Note',
    'State',
    'Sacra',
    'United',
    'Memorial',
    'Alabama',
    'Mississippi',
    'Arrangement',
    'Arrangements',
    'Arranging',
    'College',
    'University',
    'Courthouse',
    'Meetinghouse',
    'Friends',
    'Seminary',
    'Cemetary',
    'SHMHA',
    'Seek',
    'President',
    'Vice',
    'After',
    'Then',
    'Academy',
    'Officers',
    'Chaplain',
    'Fasola',
    'FaSoLa',
    'Southern',
    'Western',
    'Northwestern',
    'North',
    'Pacific',
    'Northern',
    'International',
    'Center',
    'African',
    'American',
    'School',
    'Elementary',
    'Highway',
    'Outgoing',
    'Recreation',
    'City',
    'County',
    'Avenue',
    'Public',
    'Publishing',
    'Primitive',
    'Mountain',
    'Annual',
    'Department',
    'Presbyterian',
    'Conference',
    'Railroad',
    'Society',
    'Historical',
    'Association',
    'Professor',
    'Associate',
    'Municipal',
    'Building',
    'Labor',
    'County',
    'Line',
    'Elder']

non_denson = [
    'ACH',
    'AH',
    'AV',
    'CB',
    'CH',
    'EH\s1',
    'EH\s2',
    'EH1',
    'EH2',
    'SoH',
    'GH',
    'HS',
    'ICH',
    'KsH',
    'KH',
    'LD',
    'MH',
    'NH',
    'NHC',
    'OSH',
    'ShH',
    'ScH',
    'WB']

def build_bad_words():
    ss = ''
    for s in bad_words:
        ss += s + '|'
    ss = ss[:-1]
    return ss

def build_non_denson():
    ss = ''
    for s in non_denson:
        ss += r'\(' + s + r'\)|'
    ss = ss[:-1]
    return ss

def parse_csv(filename, debug_print=False):
    session_count = 1
    d = []
    leaders = []
    pagenum_pattern = re.compile(r'\d{2,3}[tb]?')
    with open(filename, 'rb') as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            (pagenum, name) = row
            if pagenum == 'BREAK':
                if debug_print: print 'BREAK: ' + name
                d.append({'session': session_count, 'leaders': leaders})
                session_count += 1
                leaders = []
            elif pagenum_pattern.match(pagenum):
                leaders.append({'name': name.decode('utf-8'), 'song': pagenum})
                if debug_print: print '***name: ' + name + '\tsong: ' + pagenum
            elif debug_print:
                print 'SKIP song: ' + pagenum
    if leaders:
        d.append({'session': session_count, 'leaders': leaders})
    return d

def parse_minutes(s, debug_print=False):
    session_count = 0
    sessions = re.split('RECESS|LUNCH',s)
    d = []
    for session in sessions:
        session_count += 1

        # name_pattern = re.compile('(?<=Chairman\s)[A-Z]\.\s[A-Z]\.\s[A-Z]\w+|[A-Z]\.\s[A-Z]\.\s[A-Z]\w+|(?<=Chairman\s)[A-Z][\w]*?\s[A-Z][\w]*?\s[A-Z]\w+|(?<=Chairman\s)[A-Z][\w]*?\s[A-Z]\w+|[A-Z][\w]*?\s[A-Z][\w]*?\s[A-Z]\w+|[A-Z][\w]*?\s[A-Z]\w+');
        name_pattern = re.compile(ur'(\A|(?<=\s))((?!' + build_bad_words() + ur')(?<!for\s)[A-Z\u00C0-\u024F]([\u00C0-\u024F\w’-]+|\.\s|\.)\s?){2,5}', re.UNICODE)
        # pagenum_pattern = re.compile('[\[\{/](\d{2,3}[tb]?)[\]\}]')
        pagenum_pattern = re.compile(r'[\[\{/\s](\d{2,3}[tb]?)([\]\}\s]|$)(?!' + build_non_denson() + r')')

        dd = []
        leaders = re.split(r'\v|called to order|\:\s|(?<=[^\.][^A-Z\]\}])\.(\s|\Z)|(?<=[\]\}”\)])[;\.\:]|;', session)  #double quotes!
        for chunk in leaders:
            if chunk and (len(chunk) > 2):
                if debug_print: print chunk
                songs = re.finditer(pagenum_pattern, chunk)
                first_song = None
                for song in songs:
                    if not first_song:
                        first_song = song
                    pagenum = song.group(1)
                    # print pagenum
                    leaders = re.finditer(name_pattern, chunk)
                    for leader in leaders:
                        if leader.end() <= first_song.start()+1:
                            name = leader.group(0)
                            name = name.strip() # TODO: should be able to incorporate this into regex......
                            dd.append({'name': name, 'song': pagenum})
                            if debug_print: print '***name: ' + name + '\tsong: ' + pagenum
                        # else:
                            # print "%d %d"%(leader.end(), first_song.start())
                if debug_print: print "---chunk----------"

        d.append({'session': session_count, 'leaders': dd})
        # print "---session----------"
    # print d
    return d

def insert_minutes(conn, d, minutes_id, debug_print=False):

    curs = conn.cursor()
    for session in d:
        for leader in session['leaders']:

            #get song_id
            song_id = 0
            curs.execute("SELECT id FROM songs WHERE PageNum=?", [leader['song']])
            row = curs.fetchone()
            if row is not None:
                song_id = row[0]
            if song_id == 0:
                if leader['song'][-1:] == 't' or leader['song'][-1:] == 'b':
                    #check for song without "t" or "b"
                    curs.execute("SELECT id FROM songs WHERE PageNum=?", [leader['song'][0:-1]])
                    row = curs.fetchone()
                    if row is not None:
                        song_id = row[0]
                else:
                    #check for song on "top"
                    curs.execute("SELECT id FROM songs WHERE PageNum=?", [leader['song']+'t'])
                    row = curs.fetchone()
                    if row is not None:
                        song_id = row[0]
            if song_id == 0:
                print leader
                print "\tno song id! %s"%(leader['song'])
                continue

            #find leader by name if exists, create if not
            name = leader['name']

            curs.execute("SELECT name FROM leader_name_invalid WHERE name=?", [name])
            row = curs.fetchone()
            if row is not None:
                if debug_print: print "invalid name! %s"%(name)
                continue

            curs.execute("SELECT name FROM leader_name_aliases WHERE alias=?", [name])
            row = curs.fetchone()
            if row is not None:
                if debug_print: print "replacing %s with %s"%(name, row[0])
                name = row[0]

            if name is '?':
                # marked as a "bad" name in the alias table so let's just ignore this altogether
                continue

            curs.execute("SELECT * FROM leaders WHERE name=?", [name])
            row = curs.fetchone()
            leader_id = 0
            if row is None:
                curs.execute("INSERT INTO leaders (name) VALUES (?)", [name])
                conn.commit()
                leader_id = curs.lastrowid
                curs.execute("UPDATE leader_name_aliases SET leader_id=? WHERE name=?", [leader_id, name])
            else:
                leader_id = row[0]

            if song_id and leader_id and minutes_id:
                curs.execute("INSERT INTO song_leader_joins (song_id, leader_id, minutes_id) VALUES (?,?,?)", (song_id, leader_id, minutes_id))
                conn.commit()
            else:
                print "problem?! %d %d %d"%(song_id, leader_id, minutes_id)

    curs.close()

def parse_all_minutes(conn):
    curs = conn.cursor()

    # 3928 - camp fasola 2012
    # 3542 - ireland
    curs.execute("SELECT Minutes, Name, Date, id, isDenson FROM minutes")
    rows = curs.fetchall()
    for row in rows:

        if row[4] == 0:
            continue

        print "%s on %s"%(row[1],row[2])

        d = None
        filename = 'minutes/%s' % util.minutes_to_csv(row[1], row[2])
        if os.path.isfile(filename):
            print "    FROM FILE: " + filename
            d = parse_csv(filename)
        else:
            s = row[0]
            d = parse_minutes(s)

        minutes_id = row[3]
        insert_minutes(conn, d, minutes_id)
        conn.commit()

    curs.close()

def parse_minutes_by_id(conn, minutes_id):
    curs = conn.cursor()

    # 3928 - camp fasola 2012
    # 3542 - ireland
    curs.execute("SELECT Minutes, Name, Date, id, isDenson FROM minutes WHERE id=?", [minutes_id])
    rows = curs.fetchall()
    for row in rows:

        if row[4] == 0:
            continue

        print "%s on %s"%(row[1],row[2])

        s = row[0]
        d = parse_minutes(s)

        minutes_id = row[3]
        insert_minutes(conn, d, minutes_id)
        conn.commit()

    curs.close()

def clear_minutes(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM leaders")
    curs.execute("DELETE FROM song_leader_joins")
    curs.execute("DELETE FROM sqlite_sequence WHERE name='leaders'")
    curs.execute("DELETE FROM sqlite_sequence WHERE name='song_leader_joins'")
    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    clear_minutes(db)
    parse_all_minutes(db)
    # parse_minutes_by_id(db, 5165)
    db.close()
