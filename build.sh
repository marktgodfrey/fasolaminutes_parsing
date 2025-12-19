sqlite3 -init minutes_schema.sql minutes.db ""
python insert_books.py
python insert_songs.py
python insert_minutes.py
python create_aliases.py
python parse_minutes.py
python insert_locations.py
python create_leader_stats.py
python create_song_stats.py
python create_song_neighbors.py
python map_minutes_audio.py
pushd ./bostonsing; scrapy crawl singing; popd
pushd ./shapenotecds; scrapy crawl singing; popd
pushd ./phillysacredharp; scrapy crawl singing; popd
pushd ./cork; python map_audio.py; popd
pushd ./archiveorg; python map_audio.py; popd
python create_index.py
sqlite3 minutes.db "VACUUM;"
