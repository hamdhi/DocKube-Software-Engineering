"""Validate the in-app update flow against a mocked GitHub release.

This mirrors what the real 'Update App' button does: query the pinned
desktop-latest release, compare its version against the running APP_VERSION,
and decide whether to offer the download.
"""
import json
import sys
import unittest
from unittest.mock import patch, MagicMock

# Point sys.path at the desktop folder so app_update imports cleanly.
sys.path.insert(0, '.')
import app_update


RELEASE_140 = {
    'tag_name': 'desktop-latest',
    'name': 'Latest Desktop Build',
    'body': 'DocKube-Desktop v1.4.0\n',
    'html_url': 'https://github.com/hamdhi/DocKube-Software-Engineering/releases/tag/desktop-latest',
    'assets': [
        {
            'name': 'dockeybe.zip',
            'browser_download_url': 'https://github.com/hamdhi/DocKube-Software-Engineering/'
                                    'releases/download/desktop-latest/dockeybe.zip',
            'size': 31200000,
            'digest': 'sha256:' + 'a' * 64,
        },
    ],
}


class TestUpdateFlow(unittest.TestCase):
    def make_mock(self, release):
        body = json.dumps(release).encode('utf-8')

        class FakeResponse:
            def read(self, *args):
                return body
            def decode(self, *args, **kwargs):
                return body.decode('utf-8')
            def __enter__(self):
                return self
            def __exit__(self, *exc):
                pass

        return FakeResponse()

    def test_newer_version_is_offered(self):
        """Running 1.3.0 against a published 1.4.0 release must offer the download."""
        with patch.object(app_update.urllib.request, 'urlopen',
                          return_value=self.make_mock(RELEASE_140)):
            release = app_update.fetch_latest()
            status, message = app_update.assess(release, current_version='1.3.0')
            self.assertEqual(status, 'update')
            self.assertIn('1.4.0', message)

    def test_same_version_is_up_to_date(self):
        """Running 1.4.0 against a 1.4.0 release must report up to date."""
        release_140 = dict(RELEASE_140)
        with patch.object(app_update.urllib.request, 'urlopen',
                          return_value=self.make_mock(release_140)):
            release = app_update.fetch_latest()
            status, message = app_update.assess(release, current_version='1.4.0')
            self.assertEqual(status, 'current')
            self.assertIn('already installed', message)

    def test_older_version_is_up_to_date(self):
        """Running 1.4.0 against a 1.3.0 release must report up to date."""
        old = dict(RELEASE_140, body='DocKube-Desktop v1.3.0\n')
        with patch.object(app_update.urllib.request, 'urlopen',
                          return_value=self.make_mock(old)):
            release = app_update.fetch_latest()
            status, message = app_update.assess(release, current_version='1.4.0')
            self.assertEqual(status, 'current')
            self.assertIn('already installed', message)


if __name__ == '__main__':
    unittest.main(verbosity=2)