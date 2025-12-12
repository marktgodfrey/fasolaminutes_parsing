import json
import csv

def main():
    with open('SongData_1991.json', 'r') as jsonfile:
        songs = json.load(jsonfile)

    with open('song_extras.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip headers
        for row in reader:
            song_idx = int(row[0])-1
            keys = row[1].replace("b", "♭").replace("#", "♯").replace("min", "Minor")
            if not "Minor" in keys or ", " in keys:
                keys = keys + " Major"
            songs[song_idx]['keys'] = keys
            songs[song_idx]['times'] = row[2]
            songs[song_idx]['orientation'] = row[3]
            songs[song_idx]['three_liner'] = row[4] == "1"

    with open('SongData_1991.json', 'w') as jsonfile:
        json.dump(songs, jsonfile, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()