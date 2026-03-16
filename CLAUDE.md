# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **GEM Chapel** (Great Expectations Ministries International) website — a static, single-page church website deployed on Vercel. No build system, package manager, or test framework.

## Architecture

The site is split into three files:
- **`index.html`** — semantic HTML structure with section landmarks
- **`styles.css`** — all CSS including design tokens, responsive breakpoints, and animations
- **`script.js`** — IIFE-wrapped vanilla JS for interactivity

### HTML Sections (in order)
Navigation → Hero → About → Activities → Leadership → Resources (Articles) → Books → Branches → Donate → Contact → Footer

Decorative `section-divider` elements separate major content groups.

### CSS Design System (`:root` variables)
- **Colors:** `--flame-gold`, `--flame-orange`, `--flame-deep`, `--flame-ember` (fire theme); `--dark-bg`, `--dark-surface`, `--dark-card` (backgrounds); `--cream`, `--cream-muted`, `--white` (text)
- **Fonts:** `--font-display` (Fraunces — headings), `--font-body` (Outfit — body), `--font-accent` (Cormorant Garamond — decorative/quotes)
- **Easing:** `--ease-out-expo`, `--ease-out-back` for consistent motion
- Responsive breakpoints at 1024px, 768px, and 480px

### JavaScript Features
- Scroll-triggered navbar with blur backdrop
- Active nav link highlighting based on scroll position
- Animated hamburger toggle with full-screen mobile overlay
- DOM-based flame particle system (responsive particle count)
- IntersectionObserver-based scroll reveal (`.reveal` / `.visible`), elements unobserved after reveal
- Animated counters on `[data-count]` elements (years of ministry, branch count)
- Smooth anchor scrolling with navbar offset compensation
- Form validation with shake animation feedback

## Other Assets (git-ignored)

- **`Fresh Fire/`** — PDF devotional publications (~90MB, not in repo)
- **`Logos/`** — JPG logo variants
- **`GEM WEBSITES- UPDATED INFO.docx`** — Reference document with updated church info
- **`gem-chapel-website.html`** — Original single-file version (superseded by index.html)

## Development

Open `index.html` directly in a browser, or use any static file server:
```
python3 -m http.server
```

Deployed via Vercel with zero configuration (static site auto-detected from `index.html`).
