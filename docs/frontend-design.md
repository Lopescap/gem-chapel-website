# Frontend Design Rules

Mandatory guidelines for any agent producing visual design or frontend code. Combines steipete's anti-slop rules with Anthropic's frontend-design plugin.

## The Problem

AI-generated frontends converge on the same generic look: Inter font, purple gradients, white cards, predictable grids, flat solid backgrounds. This is "AI slop." Our sites must not look like they came from a template generator.

## Design Thinking (Before Coding)

Before writing any code, commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick a direction — brutally minimal, maximalist, retro-futuristic, organic, luxury, playful, editorial, brutalist, art deco, industrial, etc. Commit fully.
- **Constraints**: Framework, performance, accessibility requirements.
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work — the key is intentionality, not intensity.

## Typography
- Choose fonts that are beautiful, unique, and interesting.
- NEVER default to Inter, Roboto, Arial, or system fonts.
- Pair a distinctive display font with a refined body font.
- Unexpected, characterful font choices. Vary between projects — never converge on the same font (e.g., Space Grotesk) across generations.
- Type hierarchy matters: size, weight, spacing should create clear visual rhythm.

## Color & Theme
- Commit to a cohesive palette. Use CSS variables for consistency.
- Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- Bold accents beat timid gradients.
- If you can't explain why you chose a color, you didn't choose it — you defaulted.

## Motion & Animation
- Use animations for effects and micro-interactions.
- Prioritize CSS-only solutions for HTML. Use Framer Motion for React when available.
- Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.
- Use scroll-triggering and hover states that surprise.
- If it doesn't serve a purpose, cut it.

## Spatial Composition
- Unexpected layouts beat predictable grids.
- Asymmetry. Overlap. Diagonal flow. Grid-breaking elements.
- Generous negative space OR controlled density — both work when intentional.
- White space is design, not emptiness.

## Backgrounds & Visual Details (CRITICAL — Avoid Flatness)
- Create atmosphere and depth. NEVER default to flat solid color backgrounds.
- Apply creative forms:
  - **Gradient meshes** — multi-point gradients for organic depth
  - **Noise/grain textures** — subtle overlays (2-5% opacity) for tactile feel
  - **Geometric patterns** — SVG-based, theme-appropriate
  - **Layered transparencies** — overlapping elements with opacity
  - **Dramatic shadows** — box-shadow, drop-shadow for dimensional elements
  - **Decorative borders** — not just 1px solid gray
  - **Custom cursors** — when appropriate for the brand
  - **Grain overlays** — CSS or SVG noise for photographic depth
- Every section should have visual depth. If a section is just text on a solid color, it needs work.

## Banned Patterns (AI Slop)
- ❌ Inter / Roboto / Arial as primary font
- ❌ Purple-on-white color schemes
- ❌ Generic card grids with rounded corners
- ❌ Predictable hero → features → testimonials → CTA layout (unless the brief demands it)
- ❌ Gradient blobs as decoration
- ❌ Flat solid-color section backgrounds with no texture or depth
- ❌ Stock-photo-style placeholder imagery language
- ❌ Cookie-cutter design that lacks context-specific character

## Implementation Complexity
Match implementation complexity to the aesthetic vision:
- **Maximalist designs** need elaborate code with extensive animations and effects
- **Minimalist designs** need restraint, precision, and careful attention to spacing, typography, and subtle details
- Elegance comes from executing the vision well, not from adding more stuff

## What Good Looks Like
- Opinionated. You should be able to describe the aesthetic in one phrase.
- Consistent. Every element should feel like it belongs to the same system.
- Intentional. Every choice has a reason. "It looked nice" is not a reason.
- **Atmospheric.** The page should feel like a place, not a document.
- **Memorable.** Someone should remember one specific thing about it.

---
*Adapted from steipete's anti-slop rules + Anthropic's frontend-design plugin (anthropics/claude-code)*
