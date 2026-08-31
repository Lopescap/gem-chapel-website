# Design Tokens — [Project Name]

Copy into project's `app/globals.css` as CSS custom properties.
Copy into `tailwind.config.ts` as extended theme values.

## Colors

```css
:root {
  /* Backgrounds */
  --bg-primary: #0C0B09;
  --bg-secondary: #161412;
  --bg-card: #1A1816;

  /* Text */
  --text-primary: #F2EDE8;
  --text-secondary: #8A8580;
  --text-muted: #5A5550;

  /* Accent */
  --accent-gold: #C9A96E;
  --accent-gold-dim: #8B7D5A;

  /* Functional */
  --border: #2A2622;
  --overlay: rgba(12, 11, 9, 0.9);
}
```

## Typography

```css
:root {
  --font-display: 'Playfair Display', serif;  /* Headlines */
  --font-body: 'Inter', sans-serif;            /* Body, nav, UI */
  --font-mono: 'JetBrains Mono', monospace;    /* Stats, data */
}
```

### Scale
| Token | Size | Use |
|-------|------|-----|
| `--text-hero` | `clamp(48px, 8vw, 120px)` | Hero titles |
| `--text-h1` | `clamp(32px, 5vw, 72px)` | Page titles |
| `--text-h2` | `clamp(24px, 3vw, 42px)` | Section headers |
| `--text-body` | `18px` / `16px mobile` | Paragraphs |
| `--text-small` | `13px` | Labels, nav |
| `--text-stat` | `clamp(36px, 6vw, 64px)` | Stat numbers |

## Spacing

```css
:root {
  --space-section: 120px;    /* Between major sections */
  --space-block: 64px;       /* Between content blocks */
  --space-element: 24px;     /* Between related elements */
  --content-width: 800px;    /* Max width for text content */
  --page-padding: 80px;      /* Desktop side padding */
  --page-padding-mobile: 24px;
}
```

## Responsive Breakpoints

| Name | Width | Notes |
|------|-------|-------|
| Mobile | `< 768px` | Single column, no WebGL, touch targets 44px+ |
| Tablet | `768px–1024px` | Flexible grid, reduced spacing |
| Desktop | `> 1024px` | Full layout, WebGL enabled |

## Components

### Nav
- Height: 64px, fixed top
- Background: transparent → `var(--overlay)` on scroll
- Logo: `var(--font-body)` 14px weight-600 uppercase tracking-0.3em
- Links: `var(--font-body)` 13px weight-500 uppercase tracking-0.15em

### Hero
- Height: 100vh (sticky/fixed)
- Image: `background-size: cover; background-position: center`
- Gradient overlay: `linear-gradient(to bottom, rgba(bg, 0.3) 0%, rgba(bg, 0.1) 30%, rgba(bg, 0.1) 50%, rgba(bg, 0.5) 80%, rgba(bg, 1) 100%)`
- Title: centered, `var(--text-hero)`, text-shadow for readability

### Section
- Max width: `var(--content-width)` centered
- Padding: `var(--space-section)` vertical

### Cards
- Background: `var(--bg-card)`
- Border: 1px `var(--border)`
- Border-radius: 8px
- Hover: scale(1.02) + border-color `var(--accent-gold-dim)`

### Footer
- Background: `var(--bg-secondary)`
- Minimal: logo + copyright + nav links

---

**Instructions for Designer:** Customize these tokens for the project. Override any value. Add project-specific tokens. Delete unused ones. This is a starting point, not a constraint.

**Instructions for Builder:** These are law. Do not deviate. If the spec says `var(--accent-gold)`, use `var(--accent-gold)`. If you need a color not in tokens, add a `TODO:` comment.
