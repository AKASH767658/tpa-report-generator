import os
import unittest
from pathlib import Path


class ConfigTests(unittest.TestCase):
    def test_data_path_is_loaded_from_environment(self):
        from backend.config import DATA_PATH, PROJECT_ROOT

        expected = Path(os.getenv("DATA_PATH", "data"))
        if not expected.is_absolute():
            expected = PROJECT_ROOT / expected
        self.assertEqual(DATA_PATH, expected)


if __name__ == "__main__":
    unittest.main()
