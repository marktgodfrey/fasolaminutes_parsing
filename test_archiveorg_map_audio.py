import json
import os
import tempfile
import unittest
from unittest.mock import patch

from archiveorg.map_audio import (
    extract_pagenum,
    fetch_item_metadata,
    map_items,
    read_item,
)


class _Response:
    status_code = 200

    def __init__(self, data=None, content=b''):
        self.data = data
        self.content = content

    def json(self):
        return self.data if self.data is not None else {
            'result': [
                {
                    'format': 'VBR MP3',
                    'name': "Sat Mar 23/01 SH 101t Canaan's Land.mp3",
                    'title': "SH 101t Canaan's Land",
                },
                {
                    'format': 'PNG',
                    'name': "Sat Mar 23/01 SH 101t Canaan's Land.png",
                    'title': "SH 101t Canaan's Land",
                },
            ],
        }


class ArchiveOrgMapAudioTest(unittest.TestCase):
    def test_extract_pagenum_from_bare_archive_title(self):
        self.assertEqual(extract_pagenum('048t Devotion'), '48t')

    def test_extract_pagenum_from_sacred_harp_archive_title(self):
        self.assertEqual(extract_pagenum("SH 101t Canaan's Land"), '101t')

    def test_extract_pagenum_ignores_track_number_prefixes(self):
        self.assertIsNone(extract_pagenum("01 SH 101t Canaan's Land"))

    def test_read_item_maps_sacred_harp_archive_titles(self):
        with tempfile.TemporaryDirectory() as cache_dir, patch(
            'archiveorg.map_audio.requests.get',
            return_value=_Response(),
        ):
            songs = read_item('2019-georgia-state-sacred-harp', cache_dir)

        self.assertEqual(
            songs,
            [
                (
                    '101t',
                    "https://archive.org/download/2019-georgia-state-sacred-harp/Sat Mar 23/01 SH 101t Canaan's Land.mp3",
                ),
            ],
        )

    def test_metadata_error_is_retried(self):
        error_response = _Response({'error': 'servers unavailable'})
        good_response = _Response({'result': []})

        with tempfile.TemporaryDirectory() as cache_dir:
            with patch(
                'archiveorg.map_audio.requests.get',
                side_effect=[error_response, good_response],
            ) as get, patch('archiveorg.map_audio.time.sleep') as sleep:
                data = fetch_item_metadata('08-rogers-memorial', cache_dir)

        self.assertEqual(data, {'files': []})
        self.assertEqual(get.call_count, 2)
        get.assert_called_with(
            'https://archive.org/metadata/08-rogers-memorial/files?extended_err=1',
            timeout=30,
        )
        sleep.assert_called_once_with(1)

    def test_metadata_error_fails_after_all_retries(self):
        response = _Response({'error': 'servers unavailable'}, b'not XML')

        with tempfile.TemporaryDirectory() as cache_dir:
            with patch(
                'archiveorg.map_audio.requests.get',
                return_value=response,
            ), patch('archiveorg.map_audio.time.sleep'):
                with self.assertRaisesRegex(
                    RuntimeError,
                    'partial files metadata failed.*fallback also failed',
                ):
                    fetch_item_metadata('2017-06-03-holly-springs', cache_dir)

            self.assertEqual(os.listdir(cache_dir), [])

    def test_successful_metadata_is_reused_from_cache(self):
        response = _Response({'result': [{'name': 'track.mp3'}]})

        with tempfile.TemporaryDirectory() as cache_dir:
            with patch(
                'archiveorg.map_audio.requests.get',
                return_value=response,
            ) as get:
                first = fetch_item_metadata('cached-item', cache_dir)
                second = fetch_item_metadata('cached-item', cache_dir)

            self.assertEqual(first, second)
            self.assertEqual(get.call_count, 1)
            with open(os.path.join(cache_dir, 'cached-item.json')) as cache_file:
                self.assertEqual(json.load(cache_file), first)

    def test_refresh_metadata_bypasses_cache(self):
        old_response = _Response({'result': [{'name': 'old.mp3'}]})
        new_response = _Response({'result': [{'name': 'new.mp3'}]})

        with tempfile.TemporaryDirectory() as cache_dir:
            with patch(
                'archiveorg.map_audio.requests.get',
                side_effect=[old_response, new_response],
            ) as get:
                fetch_item_metadata('cached-item', cache_dir)
                with patch.dict(
                    os.environ,
                    {'ARCHIVEORG_REFRESH_METADATA': '1'},
                ):
                    refreshed = fetch_item_metadata('cached-item', cache_dir)

            self.assertEqual(refreshed, {'files': [{'name': 'new.mp3'}]})
            self.assertEqual(get.call_count, 2)

    def test_files_xml_is_used_when_partial_metadata_fails(self):
        error_response = _Response({'error': 'item metadata may be invalid'})
        xml = b'''<files>
          <file name="track.mp3" source="original">
            <format>VBR MP3</format><title>60</title>
          </file>
        </files>'''
        xml_response = _Response(content=xml)

        with tempfile.TemporaryDirectory() as cache_dir:
            with patch(
                'archiveorg.map_audio.requests.get',
                side_effect=[error_response] * 4 + [xml_response],
            ) as get, patch('archiveorg.map_audio.time.sleep'):
                data = fetch_item_metadata('11-24-2013-alstate', cache_dir)

        self.assertEqual(data, {'files': [{
            'name': 'track.mp3',
            'source': 'original',
            'format': 'VBR MP3',
            'title': '60',
        }]})
        self.assertEqual(get.call_count, 5)
        get.assert_called_with(
            'https://archive.org/download/11-24-2013-alstate/11-24-2013-alstate_files.xml',
            timeout=30,
        )

    def test_map_items_continues_after_metadata_failure(self):
        conn = object()
        minutes = [
            (1, 'broken-item', 1991),
            (2, 'healthy-item', 1991),
        ]

        with patch(
            'archiveorg.map_audio.read_item',
            side_effect=[RuntimeError('metadata invalid'), [('101t', 'audio-url')]],
        ), patch('archiveorg.map_audio.insert_songs') as insert:
            failures = map_items(conn, minutes)

        self.assertEqual(failures, [('broken-item', 'metadata invalid')])
        insert.assert_called_once_with(
            conn,
            2,
            1991,
            [('101t', 'audio-url')],
            check_seq=True,
        )


if __name__ == '__main__':
    unittest.main()
