# Niblet

A reveal-based interactive learning site: one lesson unlocks each day, and a category appears only when its first lesson is released.

## Local build

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build.py --as-of 2026-07-27
python3 -m http.server 8809 --directory public
```

The personal site is intentionally published beneath an unlisted path. Future lesson packages may exist locally, but the publisher excludes their content, metadata, categories, and assets from `public/` until their release date.
