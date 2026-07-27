# Niblet authoring invariants

## Reveal and navigation

- The released manifest is the only source for public lessons and categories.
- Never hardcode previous/next lesson links inside `body.html`; the publisher computes them from the released list.
- Previous appears when a released predecessor exists. Next appears only when its successor is already released.
- Never expose future lesson titles, category names, URLs, metadata, or assets.

## Art direction

- Niblet is not one reusable lesson template with different colors.
- Each category must establish a distinct visual world: palette, typography, motion language, spatial metaphor, and interaction vocabulary.
- Lessons in one category should feel related, but each lesson needs its own `scene-<slug>` treatment and concept-specific composition.
- Removing a lesson's visual effects should remove part of how the concept is explained, not merely decoration.
- Do not reuse the prior lesson's layout by default. Select the smallest interaction that teaches the concept: focused comparison, diagram, timeline, draggable control, sequencer, mixer, or full lab.
- When creating the first lesson in a new category, add and verify a corresponding `.theme-<category>` world in `niblet/static/theme.css`. It must be structurally distinct from existing category worlds, not a color swap.
- Add a `.scene-<slug>` treatment for every new lesson and verify it on desktop and a true 390px mobile viewport.

## Audio and verification

- Use native, pre-rendered, non-silent audio with `controls`, `playsinline`, and no autoplay when sound is required.
- Run the complete tests, local mobile/desktop checks, Pages deployment, and live URL/media verification before announcing the lesson.
