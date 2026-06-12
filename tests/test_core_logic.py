import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import core_logic
from core_logic import BlockerCore, BlockMode

class TestBlockerCore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        
        # Patch the paths in the core_logic module
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self):
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_init(self):
        core = BlockerCore()
        self.assertEqual(core.mode, BlockMode.NORMAL)
        self.assertIsInstance(core.blacklist, list)

    def test_write_hosts_file_atomic(self):
        core = BlockerCore()
        hosts_file = Path(self.test_dir) / "hosts"
        hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
        new_content = "127.0.0.1 localhost\n127.0.0.1 example.com\n"
        with patch('core_logic.HOSTS_PATH', str(hosts_file)):
            core._write_hosts_file(new_content)
        self.assertEqual(hosts_file.read_text(encoding="utf-8"), new_content)
        # No temp file residue left behind
        leftovers = [p for p in Path(self.test_dir).iterdir()
                     if p.name.startswith('hosts.') and p.name.endswith('.tmp')]
        self.assertEqual(leftovers, [])

    def test_import_config_rejects_invalid_hostnames(self):
        core = BlockerCore()
        import json
        import_file = Path(self.test_dir) / "import.json"
        import_file.write_text(json.dumps({
            "blacklist": ["https://www.example.com/feed", "not a hostname!", "ok.org", 123],
            "whitelist": ["good.net", ""],
        }), encoding="utf-8")
        self.assertTrue(core.import_config(import_file))
        self.assertIn("example.com", core.blacklist)
        self.assertIn("ok.org", core.blacklist)
        self.assertNotIn("not a hostname!", core.blacklist)
        self.assertIn("good.net", core.whitelist)
        self.assertNotIn("", core.whitelist)

    def test_password_hashing(self):
        core = BlockerCore()
        core.set_password("securepassword")
        self.assertTrue(core.verify_password("securepassword"))
        self.assertFalse(core.verify_password("wrongpassword"))
        
        # Verify it's using bcrypt (starts with $2b$ or $2a$)
        if core.password_hash:
            self.assertTrue(core.password_hash.startswith('$2b$') or core.password_hash.startswith('$2a$'))

class TestBlockUnblockRoundTrip(unittest.TestCase):
    """Verify blocking fully reverts: hosts file, session state, bypass server."""

    BASE_HOSTS = "# Copyright (c) 1993-2009 Microsoft Corp.\n127.0.0.1 localhost\n"

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.hosts_file = Path(self.test_dir) / "hosts"
        self.hosts_file.write_text(self.BASE_HOSTS, encoding="utf-8")

        self.patchers = [
            patch('core_logic.HOSTS_PATH', str(self.hosts_file)),
            patch('core_logic.CONFIG_PATH', Path(self.test_dir) / "config.json"),
            patch('core_logic.STATS_PATH', Path(self.test_dir) / "stats.json"),
            patch('core_logic.SESSION_STATE_PATH', Path(self.test_dir) / ".session_state.json"),
            patch.object(BlockerCore, 'is_admin', return_value=True),
            patch.object(BlockerCore, '_flush_dns', return_value=None),
        ]
        for p in self.patchers:
            p.start()

        self.core = BlockerCore()
        self.core.bypass_logger = MagicMock()

    def tearDown(self):
        for p in self.patchers:
            p.stop()
        shutil.rmtree(self.test_dir)

    def test_block_then_unblock_restores_hosts(self):
        success, _ = self.core.block_sites(duration_seconds=60)
        self.assertTrue(success)
        content = self.hosts_file.read_text(encoding="utf-8")
        self.assertIn(core_logic.MARKER_START, content)
        self.assertIn(core_logic.MARKER_END, content)
        self.assertIn("localhost", content)
        self.assertTrue(self.core.is_blocking)
        self.assertTrue(self.core.session_state_path.exists())
        self.core.bypass_logger.start_server.assert_called_once()

        success, _ = self.core.unblock_sites(force=True)
        self.assertTrue(success)
        content = self.hosts_file.read_text(encoding="utf-8")
        self.assertNotIn(core_logic.MARKER_START, content)
        self.assertNotIn(core_logic.MARKER_END, content)
        self.assertNotIn(core_logic.REDIRECT_IP + " ", content.replace("127.0.0.1 localhost", ""))
        self.assertEqual(content, self.BASE_HOSTS.strip() + "\n")
        self.assertFalse(self.core.is_blocking)
        self.assertIsNone(self.core.session_id)
        self.assertFalse(self.core.session_state_path.exists())
        self.core.bypass_logger.stop_server.assert_called_once()

    def test_strict_mode_unblock_requires_then_accepts_password(self):
        self.core.set_password("secret123")
        self.core.mode = BlockMode.STRICT
        success, _ = self.core.block_sites(duration_seconds=60)
        self.assertTrue(success)

        # Wrong/missing password must not unblock
        success, message = self.core.unblock_sites(password="wrong")
        self.assertFalse(success)
        self.assertTrue(self.core.is_blocking)
        self.assertIn(core_logic.MARKER_START, self.hosts_file.read_text(encoding="utf-8"))

        success, _ = self.core.unblock_sites()
        self.assertFalse(success)
        self.assertTrue(self.core.is_blocking)

        # Correct password unblocks and leaves no markers behind
        success, _ = self.core.unblock_sites(password="secret123")
        self.assertTrue(success)
        self.assertFalse(self.core.is_blocking)
        self.assertNotIn(core_logic.MARKER_START, self.hosts_file.read_text(encoding="utf-8"))
        self.assertFalse(self.core.session_state_path.exists())

    def test_strict_mode_force_unblock_bypasses_password(self):
        self.core.set_password("secret123")
        self.core.mode = BlockMode.STRICT
        self.core.block_sites(duration_seconds=60)

        success, _ = self.core.unblock_sites(force=True)
        self.assertTrue(success)
        self.assertFalse(self.core.is_blocking)
        self.assertNotIn(core_logic.MARKER_START, self.hosts_file.read_text(encoding="utf-8"))

    def test_emergency_cleanup_removes_all_traces(self):
        self.core.set_password("secret123")
        self.core.mode = BlockMode.STRICT
        self.core.block_sites(duration_seconds=60)

        success, _ = self.core.emergency_cleanup()
        self.assertTrue(success)
        content = self.hosts_file.read_text(encoding="utf-8")
        self.assertNotIn(core_logic.MARKER_START, content)
        self.assertNotIn(core_logic.MARKER_END, content)
        self.assertFalse(self.core.is_blocking)
        self.assertIsNone(self.core.session_id)
        self.assertFalse(self.core.session_state_path.exists())
        self.core.bypass_logger.stop_server.assert_called_once()

    def test_double_block_is_rejected(self):
        self.core.block_sites(duration_seconds=60)
        success, message = self.core.block_sites(duration_seconds=60)
        self.assertFalse(success)
        self.assertIn("Already blocking", message)

    def test_unblock_idempotent_when_not_blocking(self):
        # Unblocking with no prior block must not corrupt the hosts file
        success, _ = self.core.unblock_sites(force=True)
        self.assertTrue(success)
        self.assertEqual(
            self.hosts_file.read_text(encoding="utf-8"),
            self.BASE_HOSTS.strip() + "\n",
        )

    def test_session_state_written_before_hosts_mutation(self):
        """Crash-recovery invariant: the session-state file must be written
        BEFORE the hosts file is mutated, so a crash during the write always
        leaves a recoverable state file. Verified by call ordering."""
        calls = []
        real_write = self.core._write_hosts_file
        real_save = self.core.save_session_state

        def tracked_write(content):
            calls.append("write_hosts")
            return real_write(content)

        def tracked_save(duration):
            calls.append("save_state")
            return real_save(duration)

        with patch.object(self.core, '_write_hosts_file', side_effect=tracked_write), \
             patch.object(self.core, 'save_session_state', side_effect=tracked_save):
            success, _ = self.core.block_sites(duration_seconds=60)

        self.assertTrue(success)
        self.assertEqual(calls, ["save_state", "write_hosts"],
                         "session state must be saved before the hosts file is written")
        # After a successful block, both blocks and the recovery file exist
        self.assertIn(core_logic.MARKER_START, self.hosts_file.read_text(encoding="utf-8"))
        self.assertTrue(self.core.session_state_path.exists())

    def test_failed_hosts_write_leaves_no_phantom_session(self):
        """If the hosts write fails, block_sites must roll back the recovery
        state so we don't leave a session-state file with no actual blocks."""
        with patch.object(self.core, '_write_hosts_file',
                          side_effect=PermissionError("denied")):
            success, message = self.core.block_sites(duration_seconds=60)

        self.assertFalse(success)
        self.assertFalse(self.core.is_blocking)
        self.assertIsNone(self.core.session_id)
        self.assertFalse(self.core.session_state_path.exists(),
                         "phantom session-state file left after failed hosts write")
        # Hosts file must be untouched
        self.assertNotIn(core_logic.MARKER_START, self.hosts_file.read_text(encoding="utf-8"))

    def test_orphaned_blocks_recoverable_after_crash_during_write(self):
        """End-to-end: with the new ordering, a crash right after the hosts
        write (state already saved) is detectable and cleanable by recovery."""
        # Simulate: state saved, blocks written, then process 'crashed' (state
        # file persists, is_blocking lost). A fresh core must recover.
        self.core.block_sites(duration_seconds=60)
        self.assertTrue(self.core.session_state_path.exists())
        self.assertIn(core_logic.MARKER_START, self.hosts_file.read_text(encoding="utf-8"))

        # Fresh instance simulating next launch after a crash
        recovered = BlockerCore()
        recovered.bypass_logger = MagicMock()
        # Force the recorded pid to look dead so it's treated as orphaned
        with patch.object(recovered, '_is_process_running', return_value=False):
            orphan = recovered.check_orphaned_session()
            self.assertIsNotNone(orphan, "orphaned blocks not detected by recovery")
            success, _ = recovered.recover_from_crash()
        self.assertTrue(success)
        self.assertNotIn(core_logic.MARKER_START, self.hosts_file.read_text(encoding="utf-8"))
        self.assertFalse(recovered.session_state_path.exists())


if __name__ == '__main__':
    unittest.main()
