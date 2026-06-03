#!/usr/bin/env zsh
set -euo pipefail

PYTHON=${PYTHON:-python3}
DB_PATH="${PWD}/minutes_pre95.db"
export MINUTES_DB="${DB_PATH}"

rm -f "${DB_PATH}"
sqlite3 "${DB_PATH}" < minutes_schema.sql

"${PYTHON}" insert_books.py
"${PYTHON}" insert_songs.py
"${PYTHON}" insert_minutes.py
"${PYTHON}" create_aliases.py
"${PYTHON}" parse_minutes.py

for minutes_text in ./*-big-minutes/*/Big_Minutes_*.txt; do
    if [[ -f "${minutes_text}" ]]; then
        "${PYTHON}" insert_pre1995_minutes.py "${minutes_text}" --db "${DB_PATH}"
    fi
done

"${PYTHON}" insert_locations.py
"${PYTHON}" create_leader_stats.py
"${PYTHON}" create_song_stats.py
"${PYTHON}" create_song_neighbors.py
#"${PYTHON}" map_minutes_audio.py
#pushd ./bostonsing
#scrapy crawl singing
#popd
#pushd ./phillysacredharp
#scrapy crawl singing
#popd
#pushd ./cork
#"${PYTHON}" map_audio.py
#popd
#pushd ./archiveorg
#"${PYTHON}" map_audio.py
#popd
"${PYTHON}" create_index.py
sqlite3 "${DB_PATH}" "VACUUM;"
