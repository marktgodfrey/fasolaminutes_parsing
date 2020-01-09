#!/usr/bin/env python
# encoding: utf-8

import csv
import util

def delete_minutes(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM minutes")
    conn.commit()
    curs.close()

def insert_minutes(conn):
    curs = conn.cursor()

    reader = csv.reader(open("Minutes_All.txt", 'rb'), delimiter='\t')
    reader.next() # skip headers
    for row in reader:
        curs.execute('INSERT INTO minutes (Name, Location, Date, Minutes, \
            Year, IsDenson, GoodCt, ErrCt, AmbCt, CorrCt, ProbCt, TotalCt, \
            ProbPercent) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', row)

    conn.commit()
    curs.close()

def fix_denson(conn):
    curs = conn.cursor()

    reader = csv.reader(open("denson_override.csv", 'rb'))
    reader.next() # skip headers
    for row in reader:
        curs.execute("UPDATE minutes SET IsDenson=? WHERE Name LIKE ? AND \
            Date LIKE ?", (row[2], row[0], row[1]))

    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    delete_minutes(db)
    insert_minutes(db)
    fix_denson(db)
    db.close()
