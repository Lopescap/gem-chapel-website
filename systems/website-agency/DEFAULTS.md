# Website Agency — Defaults

These are the default patterns for websites you inherit and iterate on. If the client's site already diverges from these, follow what the site actually uses — this file is a reference, not a mandate. If you're adding something new to the site, prefer these defaults.

## Tech Stack
- **Framework:** Next.js (App Router)
- **Styling:** Inline styles with CSS custom properties (not Tailwind classes in components)
- **Language:** TypeScript
- **3D (desktop only):** Three.js + @react-three/fiber + @react-three/drei
- **Animation:** GSAP + ScrollTrigger (optional)
- **Smooth scroll:** Lenis (optional)
- **Component library:** shadcn/ui + 21st.dev community components (install via `npx shadcn@latest add`)

## Hosting / Delivery
- GitHub repository (one repo per project)
- Vercel auto-deploy from main/master branch
- ONE Vercel project per site — no CLI duplicates

## Git Discipline
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- No force-push to main without operator's approval
- Commit after each verified section, not at the end
- Tag known-good states (`v1.0`, `v1.1`, etc.) when the site hits a milestone the client cares about

## Image Pipeline
- AI generation: Nano Banana Pro (Google AI Ultra) or equivalent
- Depth maps: Immersity AI (Neural Depth 4.0, Edge Dilation ON)
- Format: PNG for depth maps, JPG or PNG for hero images
- ONE canonical version per image — delete superseded files

## Mobile Rules
- No WebGL, canvas, or 3D on mobile
- CSS `background-image: cover` for hero images
- Touch targets minimum 44px
- Test at 390px width (iPhone 15)
