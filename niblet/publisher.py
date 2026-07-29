from __future__ import annotations

import html
import json
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any


class BuildError(RuntimeError):
    """Raised when released content cannot be published safely."""


REQUIRED = {
    "number",
    "title",
    "slug",
    "category",
    "category_title",
    "release_date",
    "minutes",
}


def _released_lessons(content_dir: Path, as_of: date) -> list[dict[str, Any]]:
    lessons: list[dict[str, Any]] = []
    lessons_root = content_dir / "lessons"
    if not lessons_root.exists():
        return lessons
    for lesson_dir in sorted(p for p in lessons_root.iterdir() if p.is_dir()):
        metadata_path = lesson_dir / "lesson.json"
        if not metadata_path.is_file():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            release = date.fromisoformat(metadata["release_date"])
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise BuildError(f"Invalid metadata in {metadata_path}: {exc}") from exc
        if release > as_of:
            continue
        missing = REQUIRED - metadata.keys()
        if missing:
            raise BuildError(f"Missing metadata fields in {metadata_path}: {sorted(missing)}")
        body_path = lesson_dir / "body.html"
        if not body_path.is_file():
            raise BuildError(f"Released lesson is missing body.html: {lesson_dir.name}")
        metadata = dict(metadata)
        metadata.setdefault("summary", metadata["title"])
        metadata.setdefault("glyph", str(metadata["number"]))
        metadata.setdefault("accent", "blue")
        metadata["source_dir"] = lesson_dir
        metadata["body"] = body_path.read_text(encoding="utf-8")
        metadata["url"] = f"lessons/{metadata['number']:03d}-{metadata['slug']}/"
        lessons.append(metadata)
    lessons.sort(key=lambda item: (item["number"], item["release_date"]))
    numbers = [item["number"] for item in lessons]
    if len(numbers) != len(set(numbers)):
        raise BuildError("Released lesson numbers must be unique")
    return lessons


def _manifest(lessons: list[dict[str, Any]], built_on: date) -> dict[str, Any]:
    categories: list[dict[str, Any]] = []
    by_slug: dict[str, dict[str, Any]] = {}
    public_lessons: list[dict[str, Any]] = []
    for lesson in lessons:
        if lesson["category"] not in by_slug:
            category = {
                "slug": lesson["category"],
                "title": lesson["category_title"],
                "first_lesson": lesson["number"],
                "lesson_count": 0,
            }
            categories.append(category)
            by_slug[lesson["category"]] = category
        by_slug[lesson["category"]]["lesson_count"] += 1
        public_lessons.append(
            {
                key: lesson[key]
                for key in (
                    "number",
                    "title",
                    "slug",
                    "category",
                    "release_date",
                    "minutes",
                    "url",
                    "summary",
                    "glyph",
                    "accent",
                )
            }
        )
    return {
        "brand": "Niblet",
        "built_on": built_on.isoformat(),
        "categories": categories,
        "lessons": public_lessons,
    }


def _landing_html(manifest: dict[str, Any]) -> str:
    latest = manifest["lessons"][-1] if manifest["lessons"] else None
    latest_card = ""
    if latest:
        latest_card = f'''<a class="latest" href="{html.escape(latest['url'])}">
          <span class="latest-num">{latest['number']:02d}</span>
          <span><small class="eyebrow">Newest niblet · {latest['minutes']} min</small>
          <h2>{html.escape(latest['title'])}</h2></span><span class="arrow">→</span></a>'''
    categories = "".join(
        f'''<section class="category"><div class="category-title"><i></i>
        <h2>{html.escape(category['title'])}</h2>
        <span class="chip">{category['lesson_count']} unlocked</span></div>
        <div class="lesson-grid">'''
        + "".join(
            f'''<a class="lesson-card" href="{html.escape(lesson['url'])}">
              <span class="number">{lesson['number']:02d}</span>
              <span class="chip">Lesson {lesson['number']:02d}</span>
              <h3>{html.escape(lesson['title'])}</h3>
              <p>{html.escape(lesson['summary'])}</p>
              <span class="card-foot"><span>{lesson['minutes']} min</span><span>enter ↗</span></span>
            </a>'''
            for lesson in manifest["lessons"]
            if lesson["category"] == category["slug"]
        )
        + "</div></section>"
        for category in manifest["categories"]
    )
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
    <meta name="theme-color" content="#f5f0e4"><title>Niblet · one curious thing a day</title>
    <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
    <link rel="stylesheet" href="assets/theme.css"></head><body><div class="noise"></div>
    <nav><a class="brand" href="./">Nibl<b></b>et</a><span class="nav-meta">{len(manifest['lessons'])} collected · growing daily</span></nav>
    <main class="landing"><section class="hero"><div><span class="eyebrow">One curious thing · every day</span>
    <h1>Small bites.<br><em>Big brain.</em></h1>
    <p class="hero-copy">A learning collection that reveals itself slowly. No infinite syllabus. Just today's strange little door.</p></div>
    <div class="specimen" aria-hidden="true"><div class="orbit"></div><div class="crumb">{len(manifest['lessons'])}</div></div></section>
    {latest_card}<div class="section-head"><h2>Your collection</h2><span class="chip">New subjects appear when they begin</span></div>
    {categories}<div class="coming">◌ The next niblet appears at lesson time. Future rooms do not exist yet.</div></main>
    <script src="assets/app.js"></script></body></html>'''


def _lesson_html(
    lesson: dict[str, Any],
    *,
    previous: dict[str, Any] | None = None,
    following: dict[str, Any] | None = None,
) -> str:
    accent = {"coral": "#ff6b56", "mint": "#86f2c1", "pink": "#ff9fe4"}.get(
        lesson.get("accent"), "#3157ff"
    )
    previous_link = ""
    if previous:
        previous_link = f'''<a class="journey-card previous" data-nav="previous" href="../{previous['number']:03d}-{html.escape(previous['slug'])}/">
          <span class="journey-kicker">← Previous niblet</span><strong>{html.escape(previous['title'])}</strong><small>#{previous['number']:02d}</small></a>'''
    if following:
        following_link = f'''<a class="journey-card next" data-nav="next" href="../{following['number']:03d}-{html.escape(following['slug'])}/">
          <span class="journey-kicker">Next revealed niblet →</span><strong>{html.escape(following['title'])}</strong><small>#{following['number']:02d}</small></a>'''
    else:
        following_link = '''<div class="journey-card locked"><span class="journey-kicker">Next niblet</span><strong>Still under the napkin</strong><small>Reveals at 19:05</small></div>'''
    theme_class = f"theme-{lesson['category']}"
    scene_class = f"scene-{lesson['slug']}"
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
    <meta name="theme-color" content="{accent}">
    <title>Niblet {lesson['number']:02d} · {html.escape(lesson['title'])}</title>
    <link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml">
    <link rel="stylesheet" href="../../assets/theme.css"></head>
    <body class="lesson-page {html.escape(theme_class)} {html.escape(scene_class)}" style="--accent:{accent}"><div class="noise"></div>
    <nav><a class="brand" href="../../">Nibl<b></b>et</a><span class="nav-meta">Niblet {lesson['number']:02d} · {lesson['minutes']} min</span></nav>
    <header class="lesson-top"><div class="lesson-intro"><span class="eyebrow">{html.escape(lesson['category_title'])} · #{lesson['number']:02d}</span>
    <h1>{html.escape(lesson['title'])}</h1><p>{html.escape(lesson['summary'])}</p></div>
    <div class="lesson-art" aria-hidden="true"><span class="glyph">{html.escape(str(lesson['glyph']))}</span></div></header>
    <main class="lesson-wrap"><article class="lesson-body">{lesson['body']}</article>
    <nav class="lesson-journey" aria-label="Lesson navigation">{previous_link}{following_link}</nav></main>
    <footer class="footer-nav"><a href="../../">← All unlocked niblets</a><span>Niblet · one curious thing a day</span></footer>
    <script src="../../assets/app.js"></script></body></html>'''


def build_site(
    content_dir: str | Path,
    output_dir: str | Path,
    *,
    as_of: date,
    secret: str,
) -> Path:
    content_dir = Path(content_dir)
    output_dir = Path(output_dir)
    if not secret or "/" in secret or secret in {".", ".."}:
        raise BuildError("Secret must be one safe path segment")

    lessons = _released_lessons(content_dir, as_of)
    manifest = _manifest(lessons, as_of)

    output_dir.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(tempfile.mkdtemp(prefix=".niblet-build-", dir=output_dir))
    staged = temp_parent / secret
    final = output_dir / secret
    backup = output_dir / f".{secret}.previous"
    try:
        staged.mkdir(parents=True)
        (staged / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (staged / "index.html").write_text(_landing_html(manifest), encoding="utf-8")
        static_dir = Path(__file__).with_name("static")
        if static_dir.is_dir():
            shutil.copytree(static_dir, staged / "assets")
        learning_lab = content_dir.parent / "lab"
        if learning_lab.is_dir():
            shutil.copytree(learning_lab, staged / "learning-lab")
        for index, lesson in enumerate(lessons):
            lesson_root = staged / lesson["url"]
            lesson_root.mkdir(parents=True)
            previous = lessons[index - 1] if index > 0 else None
            following = lessons[index + 1] if index + 1 < len(lessons) else None
            (lesson_root / "index.html").write_text(
                _lesson_html(lesson, previous=previous, following=following),
                encoding="utf-8",
            )
            assets = lesson["source_dir"] / "assets"
            if assets.is_dir():
                shutil.copytree(assets, lesson_root / "assets")

        if backup.exists():
            shutil.rmtree(backup)
        if final.exists():
            final.rename(backup)
        staged.rename(final)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if not final.exists() and backup.exists():
            backup.rename(final)
        raise
    finally:
        shutil.rmtree(temp_parent, ignore_errors=True)
    return final
