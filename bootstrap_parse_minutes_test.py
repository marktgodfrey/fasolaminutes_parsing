#!/usr/bin/env python
# encoding: utf-8

import json
import util
from parse_minutes import parse_minutes

TEST_MINUTES = [{'name': 'wakefield_2016', 'id': 5202},
                {'name': 'antioch_birthday_1999', 'id': 802},
                {'name': 'delong-roberts_2005', 'id': 2131},
                {'name': 'alpharetta_2003', 'id': 1673},
                {'name': 'holly_springs_2011', 'id': 3614},
                {'name': 'al_state_2010', 'id': 3499},
                {'name': 'union_2010', 'id': 3478},
                {'name': 'seed_and_feed_1995', 'id': 49},
                {'name': 'ireland_2011', 'id': 3542},
                {'name': 'mtn_heritage_2012', 'id': 3992},
                {'name': 'state_line_1996', 'id': 221},
                {'name': 'rogers_memorial_2007', 'id': 2509},
                {'name': 'newcastle_2010', 'id': 3350},
                {'name': 'minn_state_2012', 'id': 3987},
                {'name': 'portland_2017', 'id': 5312},
                {'name': 'king_schoolhouse_1996', 'id': 265},
                {'name': 'midwest_2005', 'id': 2109}]

def extract_minutes_text(conn):
    curs = conn.cursor()

    for minutes in TEST_MINUTES:
        curs.execute("SELECT Minutes FROM minutes WHERE id=?", [minutes['id']])
        minutes_text = curs.fetchone()[0]
        with open('test/%s.txt' % minutes['name'], 'w') as txt_file:
            txt_file.write(minutes_text)

        parsed_minutes = parse_minutes(minutes_text)
        with open('test/%s.json' % minutes['name'], 'w') as json_file:
            json.dump(parsed_minutes, json_file)

    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    extract_minutes_text(db)
    db.close()