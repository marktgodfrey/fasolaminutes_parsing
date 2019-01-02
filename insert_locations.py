#!/usr/bin/env python
# encoding: utf-8

import re
import csv
import googlemaps
import util

def delete_locations(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM locations")
    curs.execute("DELETE FROM minutes_location_joins")
    conn.commit()
    curs.close()

def insert_locations(conn):
    f =  open('Singings Locations Fuzzy - locations_for_export.csv', 'rb')
    csvreader = csv.reader(f)
    curs = conn.cursor()
    csvreader.next() #headers
    for row in csvreader:
        # multilocation_day_id,minutes_id,name,address,lat_long,url,notes,gps_lat,gps_long,address1,city,county,state_province,postal_code,country
        name = row[2]
        address = row[3]
        lat_long = row[4]
        url = row[5]
        notes = row[6]

        location_id = 0

        if len(lat_long) > 0:
            gps = [a.strip() for a in lat_long.split(',')]
            # print gps
            if len(gps) == 2:
                gps_lat = gps[0]
                gps_long = gps[1]
            # else:
            #     print 'bad gps'

            address1 = None
            if len(address) > 0:
                m = re.match(r"(.+?),\s*(.+?)(?:,\s|\s\s)(.+?)\s(\d{5})", address)
                if m is not None:
                    address1 = m.group(1)
                    city = m.group(2)
                    county = '' #TODO
                    state_province = m.group(3)
                    postal_code = m.group(4)
                    country = 'USA'
                else:
                    print "weird address?? %s" % address

            if address1 is None:
                address1 = row[9]
                city = row[10]
                county = row[11]
                state_province = row[12]
                postal_code = row[13]
                country = row[14]

            print "%s - %s - %s - %s - %s - %s - %s - %s - %s" % (name, url, notes, gps_lat, gps_long, address1, city, county, state_province)

            curs.execute("SELECT id FROM locations WHERE gps_lat=? AND gps_long=?", [gps_lat,gps_long])
            location_row = curs.fetchone()
            if location_row is None:
                curs.execute("INSERT INTO locations (name, url, notes, gps_lat, gps_long, address, city, county, state_province, postal_code, country) VALUES (?,?,?,?,?,?,?,?,?,?,?)", [name, url, notes, gps_lat, gps_long, address1, city, county, state_province, postal_code, country])
                location_id = curs.lastrowid
            else:
                location_id = location_row[0]
        else:
            print 'no gps?!'

            curs.execute("SELECT id FROM locations WHERE name=?", [name])
            location_row = curs.fetchone()
            location_id = 0
            if location_row is None:
                curs.execute("INSERT INTO locations (name, url, notes) VALUES (?,?,?)", [name, url, notes])
                location_id = curs.lastrowid
            else:
                location_id = location_row[0]

        if location_id > 0:
            minutes_id = row[1]
            curs.execute("INSERT INTO minutes_location_joins (minutes_id, location_id) VALUES (?,?)", [minutes_id, location_id])

    conn.commit()
    curs.close()

def find_counties(conn):
    gmaps = googlemaps.Client(key='AIzaSyAX-p2w26PIk1wBQCKrIPoQwWS037qKiB4')
    curs = conn.cursor()
    curs.execute("SELECT id, gps_lat, gps_long FROM locations WHERE country='USA' AND county=''")
    rows = curs.fetchall()
    for row in rows:
        location_id = row[0]
        gps_lat = row[1]
        gps_long = row[2]

        # gps = '%f,%f' % (gps_lat, gps_long)
        # geocode_result = gmaps.geocode(gps)
        geocode_result = gmaps.reverse_geocode((gps_lat, gps_long))
        for c in geocode_result[0]['address_components']:
            if c['types'][0] == 'administrative_area_level_2':
                county = c['long_name']
                break

        if county:
            c = county.split(' ')
            if c[-1] == 'County':
                county = ' '.join(c[:-1])
            print 'found county: %f,%f %s' % (gps_lat, gps_long, county)
            curs.execute("UPDATE locations SET county=? WHERE id=?", [county, location_id])
        else:
            print 'county not found? %f,%f' % (gps_lat, gps_long)

    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    delete_locations(db)
    insert_locations(db)
    find_counties(db)
    db.close()
