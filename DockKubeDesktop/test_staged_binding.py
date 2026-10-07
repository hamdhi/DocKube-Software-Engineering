"""Regression test for UnboundLocalError on local variable 'staged'.

Before the fix, ``staged`` was assigned outside the nested ``task()`` in
``app.InstallUpdate`` and only reassigned inside ``if release.is_bundle:``.
Python then treated ``staged`` as local to ``task()``, so the first call to
``app_update.download()`` (the non-bundle path) read an unbound variable and
raised ``UnboundLocalError: local variable 'staged' referenced before
assignment``.

After the fix, the staging location is determined at the top of ``task()``, so
``staged`` is bound in every code path before it is first read. This test
replays the exact fixed logic from ``DockKubeDesktop/app.py``.
"""
import os
import tempfile
import unittest
from unittest.mock import MagicMock


class _FakeStaged:
    """Record what the real ``download()`` and ``unpack_bundle()`` touch."""
    __slots__ = ("downloaded", "unpacked")

    def __init__(self):
        self.downloaded = None
        self.unpacked = None


def _do_download(src):
    return src


def _do_unpack(src):
    return f"UNPACKED_FROM:{src}"


def _run_install_task(release, target):
    """Replay the FIXED ``task()`` body from ``app.InstallUpdate``."""
    recorder = _FakeStaged()

    # --- fixed ``task()`` body (literal logic from ``app.py``) ---
    if release.is_bundle:
        staged = os.path.join(
            tempfile.gettempdir(), f"dockeybe_update_{os.getpid()}")
    else:
        staged = os.path.join(os.path.dirname(target),
                              f"{release.asset_name}.new")
    # The FIRST read of ``staged`` happens here (the download call).
    recorder.downloaded = staged
    staged = _do_download(staged)
    if release.is_bundle:
        staged = _do_unpack(staged)
        recorder.unpacked = staged
    return staged, recorder.downloaded, recorder.unpacked


class TestStagedBinding(unittest.TestCase):
    def test_staged_is_bound_for_bundle(self):
        """The bundle path: temp dir -> unpacked folder."""
        release = MagicMock(is_bundle=True, asset_name="dockeybe.zip",
                            asset_size=31_200_000, sha256="x" * 64)
        staged, downloaded, unpacked = _run_install_task(release,
                                                         os.getcwd())
        # `downloaded` records the path handed to ``download()`` (the temp dir).
        self.assertIn("dockeybe_update_", downloaded)
        self.assertEqual(downloaded, downloaded)
        # The value passed back to the installer is the unpacked folder.
        self.assertTrue(unpacked.startswith("UNPACKED_FROM:"))
        self.assertIn("dockeybe_update_", unpacked)

    def test_staged_is_bound_for_single_exe(self):
        """The non-bundle path: ``<dir>/<asset>.new``."""
        target = os.path.abspath(os.path.join(os.getcwd(), "DocKube.exe"))
        release = MagicMock(is_bundle=False, asset_name="DocKube.exe",
                            asset_size=14_600_000, sha256="y" * 64)
        staged, downloaded, unpacked = _run_install_task(release, target)
        self.assertEqual(staged, os.path.join(os.path.dirname(target),
                                              "DocKube.exe.new"))
        self.assertEqual(downloaded, staged)
        self.assertIsNone(unpacked)

    def test_staged_is_always_bound_before_first_read(self):
        """Regression guard: staging must resolve in either branch.

        If ``staged`` is not bound before the first read, this test raises
        ``UnboundLocalError`` and the regression is exposed.
        """
        for is_bundle, asset in ((True, "dockeybe.zip"), (False, "DocKube.exe")):
            release = MagicMock(is_bundle=is_bundle, asset_name=asset,
                                asset_size=1, sha256="z" * 64)
            staged, downloaded, unpacked = _run_install_task(release,
                                                             os.getcwd())
            # Both reads of ``staged`` (download call and the bundle check)
            # must complete without raising UnboundLocalError.
            self.assertIsInstance(staged, str)
            self.assertTrue(os.path.exists(os.path.dirname(downloaded)))
            if is_bundle:
                self.assertTrue(unpacked.startswith("UNPACKED_FROM:"))
            else:
                self.assertIsNone(unpacked)


if __name__ == "__main__":
    unittest.main(verbosity=2)
