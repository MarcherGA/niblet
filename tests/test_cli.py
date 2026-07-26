from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class BuildCliTests(unittest.TestCase):
    def test_build_script_runs_directly_from_any_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "site"
            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "build.py"),
                    "--as-of",
                    "2026-07-27",
                    "--output",
                    str(output),
                    "--secret",
                    "test-secret",
                ],
                cwd="/tmp",
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((output / "test-secret" / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
