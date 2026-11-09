#!/usr/bin/env python3

# Allow direct execution
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import re
import tempfile

from yt_dlp.cookies import YoutubeDLCookieJar


class TestYoutubeDLCookieJar(unittest.TestCase):
    def test_save_loaded_file_object(self):
        contents = '# Netscape HTTP Cookie File\nexample.invalid\tFALSE\t/\tTRUE\t0\ttest\tvalue\n'
        cookiefile = io.StringIO(contents)
        cookiejar = YoutubeDLCookieJar(cookiefile)
        cookiejar.load()
        self.assertEqual(cookiefile.tell(), len(contents))

        cookiejar.save()
        self.assertTrue(cookiefile.getvalue().startswith('# Netscape HTTP Cookie File\n'))
        self.assertNotIn('\0', cookiefile.getvalue())
        self.assertFalse(cookiefile.closed)

        cookiefile.seek(0)
        reloaded = YoutubeDLCookieJar(cookiefile)
        reloaded.load()
        self.assertEqual(reloaded.get_cookie_header('https://example.invalid/'), 'test=value')

    def test_save_file_object_repeatedly(self):
        cookiefile = io.StringIO()
        cookiejar = YoutubeDLCookieJar(cookiefile)
        cookiejar.load(filename='./test/testdata/cookies/session_cookies.txt')
        cookiejar.save()
        expected = cookiefile.getvalue()
        for _ in range(2):
            cookiejar.save()
            self.assertEqual(cookiefile.getvalue(), expected)

    def test_save_file_object_removes_old_contents(self):
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as cookiefile:
            cookiefile.write('old contents' * 100)
            cookiejar = YoutubeDLCookieJar(cookiefile)
            cookiejar.save()
            cookiefile.seek(0)
            contents = cookiefile.read()
            self.assertTrue(contents.startswith('# Netscape HTTP Cookie File\n'))
            self.assertNotIn('\0', contents)
            self.assertNotIn('old contents', contents)
            self.assertFalse(cookiefile.closed)
            cookiefile.seek(0)
            reloaded = YoutubeDLCookieJar(cookiefile)
            reloaded.load()
            self.assertFalse(list(reloaded))

    def test_open_file_object_preserves_read_position(self):
        cookiefile = io.StringIO('before;after')
        cookiefile.seek(7)
        with YoutubeDLCookieJar().open(cookiefile) as stream:
            self.assertIs(stream, cookiefile)
            self.assertEqual(stream.read(), 'after')
        self.assertFalse(cookiefile.closed)

    def test_keep_session_cookies(self):
        cookiejar = YoutubeDLCookieJar('./test/testdata/cookies/session_cookies.txt')
        cookiejar.load()
        tf = tempfile.NamedTemporaryFile(delete=False)
        try:
            cookiejar.save(filename=tf.name)
            temp = tf.read().decode()
            self.assertTrue(re.search(
                r'www\.foobar\.foobar\s+FALSE\s+/\s+TRUE\s+0\s+YoutubeDLExpiresEmpty\s+YoutubeDLExpiresEmptyValue', temp))
            self.assertTrue(re.search(
                r'www\.foobar\.foobar\s+FALSE\s+/\s+TRUE\s+0\s+YoutubeDLExpires0\s+YoutubeDLExpires0Value', temp))
        finally:
            tf.close()
            os.remove(tf.name)

    def test_strip_httponly_prefix(self):
        cookiejar = YoutubeDLCookieJar('./test/testdata/cookies/httponly_cookies.txt')
        cookiejar.load()

        def assert_cookie_has_value(key):
            self.assertEqual(cookiejar._cookies['www.foobar.foobar']['/'][key].value, key + '_VALUE')

        assert_cookie_has_value('HTTPONLY_COOKIE')
        assert_cookie_has_value('JS_ACCESSIBLE_COOKIE')

    def test_malformed_cookies(self):
        cookiejar = YoutubeDLCookieJar('./test/testdata/cookies/malformed_cookies.txt')
        cookiejar.load()
        # Cookies should be empty since all malformed cookie file entries
        # will be ignored
        self.assertFalse(cookiejar._cookies)

    def test_get_cookie_header(self):
        cookiejar = YoutubeDLCookieJar('./test/testdata/cookies/httponly_cookies.txt')
        cookiejar.load()
        header = cookiejar.get_cookie_header('https://www.foobar.foobar')
        self.assertIn('HTTPONLY_COOKIE', header)

    def test_get_cookies_for_url(self):
        cookiejar = YoutubeDLCookieJar('./test/testdata/cookies/session_cookies.txt')
        cookiejar.load()
        cookies = cookiejar.get_cookies_for_url('https://www.foobar.foobar/')
        self.assertEqual(len(cookies), 2)
        cookies = cookiejar.get_cookies_for_url('https://foobar.foobar/')
        self.assertFalse(cookies)


if __name__ == '__main__':
    unittest.main()
