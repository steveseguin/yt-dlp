#!/usr/bin/env python3

# Allow direct execution
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import io

from yt_dlp import webvtt


class TestWebVTT(unittest.TestCase):
    def test_write_cue_separator(self):
        for ending in ('', '\n', '\r', '\r\n'):
            with self.subTest(ending=ending):
                fragment = f'WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nFirst caption{ending}'
                header, first = webvtt.parse_fragment(fragment.encode())
                _, second = webvtt.parse_fragment(
                    b'WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nSecond caption')
                output = io.StringIO()
                for block in (header, first, second):
                    block.write_into(output)
                cues = list(webvtt.parse_fragment(output.getvalue().encode()))[1:]
                self.assertEqual(len(cues), 2)
                self.assertEqual([cue.text.rstrip('\r\n') for cue in cues], ['First caption', 'Second caption'])
                self.assertEqual([(cue.start, cue.end) for cue in cues], [(0, 90000), (90000, 180000)])

    def test_write_empty_cue(self):
        cue = webvtt.CueBlock(id=None, start=0, end=90000, settings=None, text='')
        output = io.StringIO()
        cue.write_into(output)
        self.assertEqual(output.getvalue(), '00:00:00.000 --> 00:00:01.000\n\n')

    def test_preserve_terminated_payload(self):
        for text in ('One line\n', 'Two\nlines\n', 'Two\r\nlines\r\n'):
            with self.subTest(text=text):
                cue = webvtt.CueBlock(id='cue-id', start=0, end=90000, settings='align:start', text=text)
                output = io.StringIO()
                cue.write_into(output)
                self.assertEqual(output.getvalue(), f'cue-id\n00:00:00.000 --> 00:00:01.000 align:start\n{text}\n')

    def test_write_multiline_unterminated_payload(self):
        for newline in ('\n', '\r', '\r\n'):
            with self.subTest(newline=newline):
                text = f'First line{newline}Second line'
                cue = webvtt.CueBlock(id=None, start=0, end=90000, settings=None, text=text)
                output = io.StringIO()
                cue.write_into(output)
                self.assertEqual(output.getvalue(), f'00:00:00.000 --> 00:00:01.000\n{text}\n\n')


if __name__ == '__main__':
    unittest.main()
