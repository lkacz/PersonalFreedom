import unittest
import json
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from productivity_ai import ProductivityAnalyzer

class TestProductivityAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.stats_path = os.path.join(self.test_dir, "stats.json")
        
        # Create dummy stats
        self.test_stats = {
            "total_focus_time": 18000,
            "sessions_completed": 25,
            "sessions_cancelled": 3,
            "daily_stats": {}
        }
        
        # Add some daily stats
        today = datetime.now().strftime("%Y-%m-%d")
        self.test_stats["daily_stats"][today] = {
            "focus_time": 3600,
            "sessions": 3
        }
        
        with open(self.stats_path, 'w') as f:
            json.dump(self.test_stats, f)

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_load_stats(self):
        analyzer = ProductivityAnalyzer(self.stats_path)
        self.assertEqual(analyzer.stats['total_focus_time'], 18000)

    def test_predict_optimal_session_length(self):
        analyzer = ProductivityAnalyzer(self.stats_path)
        # With high completion rate (25/28 > 0.8), should be 45
        self.assertEqual(analyzer.predict_optimal_session_length(), 45)

if __name__ == '__main__':
    unittest.main()
