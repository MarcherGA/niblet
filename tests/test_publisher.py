from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from niblet.publisher import BuildError, build_site


class PublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.content = root / "content"
        self.output = root / "public"
        self.secret = "blue-comet"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def lesson(
        self,
        *,
        number: int,
        title: str,
        category: str,
        category_title: str,
        release_date: str,
        slug: str,
        body: str = "<p>Lesson body</p>",
        assets: dict[str, bytes] | None = None,
    ) -> None:
        lesson_dir = self.content / "lessons" / f"{number:03d}-{slug}"
        lesson_dir.mkdir(parents=True)
        (lesson_dir / "lesson.json").write_text(
            json.dumps(
                {
                    "number": number,
                    "title": title,
                    "slug": slug,
                    "category": category,
                    "category_title": category_title,
                    "release_date": release_date,
                    "minutes": 9,
                }
            ),
            encoding="utf-8",
        )
        (lesson_dir / "body.html").write_text(body, encoding="utf-8")
        for name, data in (assets or {}).items():
            path = lesson_dir / "assets" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def manifest(self) -> dict:
        return json.loads(
            (self.output / self.secret / "manifest.json").read_text(encoding="utf-8")
        )

    def test_future_lesson_is_not_deployed_or_listed(self) -> None:
        self.lesson(
            number=1,
            title="Beat and Meter",
            category="rhythm",
            category_title="Rhythm Foundations",
            release_date="2026-07-27",
            slug="beat-and-meter",
        )
        self.lesson(
            number=2,
            title="Intervals",
            category="ear-training",
            category_title="Ear Training",
            release_date="2026-07-28",
            slug="intervals",
            body="TOP SECRET FUTURE CONTENT",
        )

        build_site(self.content, self.output, as_of=date(2026, 7, 27), secret=self.secret)

        manifest = self.manifest()
        self.assertEqual([1], [lesson["number"] for lesson in manifest["lessons"]])
        self.assertFalse(
            (self.output / self.secret / "lessons" / "002-intervals").exists()
        )
        deployed_text = "".join(
            p.read_text(encoding="utf-8", errors="ignore")
            for p in (self.output / self.secret).rglob("*")
            if p.is_file()
        )
        self.assertNotIn("TOP SECRET FUTURE CONTENT", deployed_text)

    def test_category_appears_only_when_its_first_lesson_releases(self) -> None:
        self.lesson(
            number=1,
            title="Beat and Meter",
            category="rhythm",
            category_title="Rhythm Foundations",
            release_date="2026-07-27",
            slug="beat-and-meter",
        )
        self.lesson(
            number=2,
            title="Intervals",
            category="ear-training",
            category_title="Ear Training",
            release_date="2026-07-28",
            slug="intervals",
        )

        build_site(self.content, self.output, as_of=date(2026, 7, 27), secret=self.secret)
        self.assertEqual(["rhythm"], [c["slug"] for c in self.manifest()["categories"]])

        build_site(self.content, self.output, as_of=date(2026, 7, 28), secret=self.secret)
        self.assertEqual(
            ["rhythm", "ear-training"],
            [c["slug"] for c in self.manifest()["categories"]],
        )

    def test_released_lesson_has_stable_direct_url_and_copied_assets(self) -> None:
        self.lesson(
            number=9,
            title="Rhythmic Anticipation",
            category="rhythm",
            category_title="Rhythm Foundations",
            release_date="2026-07-27",
            slug="rhythmic-anticipation",
            assets={"example.mp3": b"ID3-test-audio"},
        )

        build_site(self.content, self.output, as_of=date(2026, 7, 27), secret=self.secret)

        lesson = self.manifest()["lessons"][0]
        self.assertEqual(
            "lessons/009-rhythmic-anticipation/", lesson["url"]
        )
        lesson_root = self.output / self.secret / lesson["url"]
        self.assertTrue((lesson_root / "index.html").is_file())
        self.assertEqual(b"ID3-test-audio", (lesson_root / "assets/example.mp3").read_bytes())

    def test_bottom_navigation_uses_only_released_neighbors(self) -> None:
        self.lesson(number=1, title="One", category="rhythm", category_title="Rhythm", release_date="2026-07-27", slug="one")
        self.lesson(number=2, title="Two", category="rhythm", category_title="Rhythm", release_date="2026-07-28", slug="two")
        self.lesson(number=3, title="Three", category="ear", category_title="Ear", release_date="2026-07-29", slug="three")

        build_site(self.content, self.output, as_of=date(2026, 7, 28), secret=self.secret)
        first = (self.output / self.secret / "lessons/001-one/index.html").read_text(encoding="utf-8")
        second = (self.output / self.secret / "lessons/002-two/index.html").read_text(encoding="utf-8")

        self.assertNotIn('data-nav="previous"', first)
        self.assertIn('data-nav="next" href="../002-two/"', first)
        self.assertIn('data-nav="previous" href="../001-one/"', second)
        self.assertNotIn('data-nav="next"', second)
        self.assertNotIn("003-three", first + second)

    def test_lesson_page_has_category_theme_and_unique_scene_class(self) -> None:
        self.lesson(
            number=5,
            title="Syncopation",
            category="rhythm-foundations",
            category_title="Rhythm Foundations",
            release_date="2026-07-27",
            slug="syncopation",
        )
        build_site(self.content, self.output, as_of=date(2026, 7, 29), secret=self.secret)
        page = (self.output / self.secret / "lessons/005-syncopation/index.html").read_text(encoding="utf-8")
        self.assertIn("theme-rhythm-foundations", page)
        self.assertIn("scene-syncopation", page)

    def test_learning_style_lab_is_published_with_persistence_and_matched_trials(self) -> None:
        lab = self.content.parent / "lab"
        lab.mkdir()
        (lab / "index.html").write_text(
            '<script>localStorage.setItem("niblet-learning-lab", "x")</script>'
            '<section data-format="animation"></section>'
            '<section data-format="daw"></section>'
            '<button data-export-results>Export</button>',
            encoding="utf-8",
        )
        (lab / "assets").mkdir()
        (lab / "assets" / "sample.ogg").write_bytes(b"OggS-matched-sample")
        build_site(self.content, self.output, as_of=date(2026, 7, 29), secret=self.secret)
        page = (self.output / self.secret / "learning-lab/index.html").read_text(encoding="utf-8")
        self.assertIn("niblet-learning-lab", page)
        self.assertIn('data-format="animation"', page)
        self.assertIn('data-format="daw"', page)
        self.assertIn("data-export-results", page)
        self.assertEqual(
            b"OggS-matched-sample",
            (self.output / self.secret / "learning-lab/assets/sample.ogg").read_bytes(),
        )
    def test_invalid_lesson_does_not_replace_last_good_build(self) -> None:
        self.lesson(
            number=1,
            title="Beat and Meter",
            category="rhythm",
            category_title="Rhythm Foundations",
            release_date="2026-07-27",
            slug="beat-and-meter",
        )
        build_site(self.content, self.output, as_of=date(2026, 7, 27), secret=self.secret)
        original = (self.output / self.secret / "manifest.json").read_bytes()

        broken = self.content / "lessons" / "002-broken"
        broken.mkdir(parents=True)
        (broken / "lesson.json").write_text(
            json.dumps(
                {
                    "number": 2,
                    "title": "Broken",
                    "slug": "broken",
                    "category": "rhythm",
                    "category_title": "Rhythm Foundations",
                    "release_date": "2026-07-27",
                    "minutes": 9,
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(BuildError):
            build_site(self.content, self.output, as_of=date(2026, 7, 27), secret=self.secret)

        self.assertEqual(original, (self.output / self.secret / "manifest.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
