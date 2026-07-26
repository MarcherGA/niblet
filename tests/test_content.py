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


if __name__ == "__main__":
    unittest.main()
