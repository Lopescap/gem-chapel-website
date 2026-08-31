# Quality Gate Protocol

Nothing ships without passing the gate. Run this checklist yourself before pushing anything the client will see. Be honest — do not soften the verdict to avoid extra work.

## Universal Checks

### Brief Compliance
- [ ] Deliverable matches what was actually requested
- [ ] Scope creep identified and flagged (don't silently add extras)
- [ ] All required elements present

### Honest Assessment
- [ ] You flagged actual problems, not just praise
- [ ] Weak areas ranked by severity
- [ ] Recommendation: **SHIP / SHIP WITH NOTES / REWORK** (with specifics)

## Website Checks

### Content / Strategy
- [ ] Copy matches the client's brand voice (see `USER.md → Your Client Team → Team preferences`)
- [ ] No fabricated stats, quotes, or claims — real data only
- [ ] Nothing off-limits per the client's tone rules

### Design
- [ ] UX flow has a clear conversion / next-step path
- [ ] Visual system is cohesive (not the default `docs/frontend-design.md` "AI slop" look)
- [ ] Mobile responsive at 375px, 768px, 1440px

### Code
- [ ] Builds without errors
- [ ] No console errors or warnings in browser
- [ ] Semantic HTML
- [ ] Meta tags and OG tags present
- [ ] Images optimized (compressed, appropriate format, sized)
- [ ] Lighthouse performance > 90
- [ ] Lighthouse accessibility > 90

## Verdict Format

When you're doing a real audit (not just a small edit), write it up in your session or in the memory file:

```markdown
## Quality Audit — [what was changed]

**Verdict:** SHIP / SHIP WITH NOTES / REWORK

### Passed
- (what's good — brief)

### Issues
1. [SEVERITY] Description — where / how to fix
2. ...

### Recommendation
(one paragraph: ship it, fix these things, or start over and why)
```

## When to Use the Full Gate vs. Skip It

**Full gate:**
- Any change to a page a real user will see
- Any published copy or content
- Any deploy to production

**Skip (small edits):**
- Typo fixes
- Internal-only doc updates
- Sandbox / preview-only experiments

When in doubt, run the gate. The cost of a bad ship is higher than the cost of a two-minute checklist.
