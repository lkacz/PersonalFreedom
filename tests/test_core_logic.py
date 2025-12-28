import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch
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

    def test_password_hashing(self):
        core = BlockerCore()
        core.set_password("securepassword")
        self.assertTrue(core.verify_password("securepassword"))
        self.assertFalse(core.verify_password("wrongpassword"))
        
        # Verify it's using bcrypt (starts with $2b$ or $2a$)
        if core.password_hash:
            self.assertTrue(core.password_hash.startswith('$2b$') or core.password_hash.startswith('$2a$'))

if __name__ == '__main__':
    unittest.main()
