# Cross-Validation Protocol

When you're uncertain about the quality of something you produced, get a second opinion before shipping. Adapted from steipete's "oracle" pattern.

## When to Cross-Validate

- You just wrote something complex enough to hide bugs.
- You're producing content that a real user will see (published copy, a new page).
- Your gut says "this feels generic" or "I'm not sure if this is good."
- Any output that will be the foundation for downstream work.

## How It Works

The goal: have a fresh set of eyes evaluate the artifact without knowing what you were told to produce. That avoids confirmation bias.

### Method 1: Oracle CLI (if installed on this VM)

```bash
npx -y @steipete/oracle --engine browser -p "Review this artifact for [specific criteria]" --file "path/to/artifact"
```

### Method 2: Manual second pass by you

1. Pretend you did not write this. Read only the output — not the prompt or intent.
2. Ask: does this meet the quality bar in `docs/quality-gate.md`?
3. Note specific issues, not vibes ("the hero copy buries the value prop in paragraph 3" not "the hero feels weak").
4. If issues exist, fix them or explicitly flag them in your ship notes.

### Method 3: Ask your operator

If you truly can't tell if something is good, ping Pilate. Better to pause than to ship something you're not confident in.

## Rules

- Cross-validation is for high-stakes outputs, not every step. Don't run it on typo fixes.
- The reviewer (whether it's a tool, a second pass, or Pilate) should evaluate the **artifact**, not the intent.
- If the review disagrees with your original judgment, take it seriously. Don't defend, investigate.
