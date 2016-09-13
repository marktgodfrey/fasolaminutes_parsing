#!/usr/bin/env python
# encoding: utf-8

import csv
import sqlite3

def main():
    conn = sqlite3.connect("minutes.db")
    conn.text_factory = str
    curs = conn.cursor()

    reader = csv.reader(open("Minutes_All.txt",'rb'), delimiter='\t')
    reader.next() # skip headers
    for row in reader:
        if row[4] == '2015':  #change this to only insert new minutes
            curs.execute('INSERT INTO minutes (Name, Location, Date, Minutes, Year, IsDenson, GoodCt, ErrCt, AmbCt, CorrCt, ProbCt, TotalCt, ProbPercent) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', row)
            conn.commit()

    curs.close()


if __name__ == '__main__':
    main()
