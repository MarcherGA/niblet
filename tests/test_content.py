from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
LESSONS = ROOT / "content" / "lessons"


class LessonMediaTests(unittest.TestCase):
    def test_every_audio_reference_exists_and_is_nontrivial(self) -> None:
        references = []
        for body in LESSONS.glob("*/body.html"):
            text = body.read_text(encoding="utf-8")
            for source in re.findall(r'<audio\b[^>]*\bsrc="([^"]+)"', text):
                references.append((body.parent, source))
        self.assertGreater(len(references), 10)
        for lesson_dir, source in references:
            with self.subTest(lesson=lesson_dir.name, source=source):
                self.assertTrue(source.startswith("assets/"))
                asset = lesson_dir / source
                self.assertTrue(asset.is_file(), f"Missing audio asset: {asset}")
                self.assertGreater(asset.stat().st_size, 2_000, f"Audio is suspiciously small: {asset}")

    def test_audio_tags_are_ios_inline_and_do_not_autoplay(self) -> None:
        for body in LESSONS.glob("*/body.html"):
            text = body.read_text(encoding="utf-8")
            for tag in re.findall(r"<audio\b[^>]*>", text):
                with self.subTest(lesson=body.parent.name, tag=tag):
                    self.assertIn("playsinline", tag)
                    self.assertNotIn("autoplay", tag)


class LabDiagnosticTests(unittest.TestCase):
    def test_v2_tests_four_broad_modes_with_counterbalanced_assignments(self) -> None:
        html = (ROOT / "lab" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "lab" / "lab.js").read_text(encoding="utf-8")
        for mode in ("text-static", "narrated-animation", "audio-first", "guided-manipulation"):
            self.assertIn(mode, html + script)
        self.assertIn("counterbalance", script)
        self.assertIn("WILLIAMS_ROWS", script)
        self.assertIn("broadAssignments", script)
        self.assertIn("familiarity", script)
        self.assertIn("assessment", script)
        self.assertIn("concept-motion", script)
        self.assertIn("Answer recorded.", script)
        self.assertIn("modeScores", script)

    def test_v2_supports_delayed_retention_and_resume(self) -> None:
        script = (ROOT / "lab" / "lab.js").read_text(encoding="utf-8")
        self.assertIn("niblet-learning-lab-v2", script)
        self.assertIn("delayedAvailableAt", script)
        self.assertIn("day1LocalDate", script)
        self.assertIn("18*60*60*1000", script)
        self.assertIn("localStorage", script)
        self.assertIn("delayed", script)
        self.assertTrue((ROOT / "lab" / "pilot" / "index.html").is_file())

    def test_lab_rejects_fixed_learning_style_claims(self) -> None:
        html = (ROOT / "lab" / "index.html").read_text(encoding="utf-8")
        self.assertIn("not a fixed learning-style diagnosis", html)
        self.assertIn("may change", html)


if __name__ == "__main__":
    unittest.main()
