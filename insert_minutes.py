#!/usr/bin/env python
# encoding: utf-8

import csv
import datetime
import re
import util

def delete_minutes(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM minutes")
    conn.commit()
    curs.close()


def insert_minutes(conn):
    curs = conn.cursor()

    reader = csv.reader(open("Minutes_All.txt", 'r'), delimiter='\t')
    next(reader)  # skip headers
    for row in reader:
        curs.execute('INSERT INTO minutes (Name, Location, Date, Minutes, \
            Year, IsDenson, GoodCt, ErrCt, AmbCt, CorrCt, ProbCt, TotalCt, \
            ProbPercent) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', row)

    conn.commit()
    curs.close()


def fix_denson(conn):
    curs = conn.cursor()

    reader = csv.reader(open("denson_override.csv", 'r'))
    next(reader)  # skip headers
    for row in reader:
        curs.execute("UPDATE minutes SET IsDenson=? WHERE Name LIKE ? AND \
            Date LIKE ?", (row[2], row[0], row[1]))

    conn.commit()
    curs.close()


def fix_virtual(conn):
    curs = conn.cursor()

    reader = csv.reader(open("virtual.csv", 'r'))
    next(reader)  # skip headers
    for row in reader:
        curs.execute("UPDATE minutes SET IsVirtual=? WHERE Name LIKE ? AND \
            Date LIKE ?", (row[2], row[0], row[1]))

    conn.commit()
    curs.close()


def do_ordinal_dates(conn):
    curs = conn.cursor()

    curs.execute("SELECT id, Date FROM minutes")
    rows = curs.fetchall()
    errcnt = 0
    for row in rows:
        s = row[1]
        s = re.sub("-\d+", "", s)  # remove date range
        s = s.replace(" Night", "")
        s = s.replace(" night", "")
        s = s.replace(",", "")

        d = None
        try:
            d = datetime.datetime.strptime(s, '%B %d %Y')
        except Exception as e:
            try:
                d = datetime.datetime.strptime(s, '%A %B %d %Y')
                # print str(d.toordinal())
            except Exception as ee:
                print(ee)
                print(s)
                errcnt += 1

        if d:
            # print(str(d.toordinal()))
            curs.execute("UPDATE minutes SET DateOrdinal=? WHERE id=?", [d.toordinal(), row[0]])
            conn.commit()

    conn.commit()
    curs.close()


if __name__ == '__main__':
    db = util.open_db()
    delete_minutes(db)
    insert_minutes(db)
    fix_denson(db)
    fix_virtual(db)
    do_ordinal_dates(db)
    db.close()
