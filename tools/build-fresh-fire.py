#!/usr/bin/env python3
"""
build-fresh-fire.py — Generator for the Fresh Fire for Today section.

Zero third-party dependencies. Reads tools/fresh-fire-bundle.json (the single
source of truth) and writes 92 entry HTML files into resources/fresh-fire/.

Usage:
    python3 tools/build-fresh-fire.py

Idempotent: two runs produce byte-identical output.
"""

import json, os, html as html_mod, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_PATH = os.path.join(ROOT, "tools", "fresh-fire-bundle.json")
TEMPLATE_DIR = os.path.join(ROOT, "tools", "templates")
OUTPUT_DIR = os.path.join(ROOT, "resources", "fresh-fire")

HEAD_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "head.txt")
NAV_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "nav.txt")
FOOTER_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "footer.txt")


def esc(text):
    return html_mod.escape(text, quote=True)


def load_bundle():
    with open(BUNDLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_templates():
    with open(HEAD_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        head = f.read()
    with open(NAV_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        nav = f.read()
    with open(FOOTER_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        footer = f.read()
    return head, nav, footer


def resolve_url(pattern, origin, slug=None):
    """Resolve a URL from a url_patterns template, replacing {origin} and optionally {slug}."""
    url = pattern.replace("{origin}", origin)
    if slug is not None:
        url = url.replace("{slug}", slug)
    return url


def fill_head(entry, origin, head_tpl, patterns):
    """Fill head template placeholders for an entry page."""
    canonical_url = resolve_url(patterns["entry"], origin, entry["slug"])
    meta_desc = entry["summary"][:160]
    h = head_tpl
    h = h.replace("{{TITLE}}", f"{esc(entry['title'])} \u2014 GEM Chapel")
    h = h.replace("{{META_DESC}}", esc(meta_desc))
    h = h.replace("{{CANONICAL_URL}}", esc(canonical_url))
    h = h.replace("{{OG_DESC}}", esc(meta_desc))
    h = h.replace("{{OG_TYPE}}", "article")
    return h


def render_blocks(blocks):
    parts = []
    for block in blocks:
        t = block["type"]
        text = esc(block["text"])
        if t == "heading":
            parts.append(f"      <h2>{text}</h2>\n")
        else:
            parts.append(f"      <p>{text}</p>\n")
    return "".join(parts)


def render_tag(label, url=None):
    if url:
        return f'      <a href="{url}" class="ff-tag">{label}</a>'
    return f'      <span class="ff-tag">{label}</span>'


def build_entry(entry, origin, entries, head_tpl, nav_tpl, footer_tpl, bundle, patterns):
    """Build one devotional entry page per Prompt 3 spec."""
    head = fill_head(entry, origin, head_tpl, patterns)

    # 1. H1
    h1 = esc(entry["title"])

    # 2. Summary
    summary_html = ""
    if entry.get("summary"):
        summary_html = f'    <p class="ff-in-short"><strong>In short:</strong> {esc(entry["summary"])}</p>\n'

    # 3. Key scripture blockquote (omitted when key_scripture is empty)
    ks_html = ""
    ks_ref = entry.get("key_scripture", "")
    ks_text = entry.get("key_scripture_text", "")
    if ks_ref:
        ks_html = f"""    <div class="ff-key-scripture">
      <blockquote>{esc(ks_text)}
        <footer>&mdash; {esc(ks_ref)}</footer>
      </blockquote>
    </div>
"""

    # 4. Blocks
    blocks_html = render_blocks(entry.get("blocks", []))

    # 5. Prayer & Confession
    prayer_html = ""
    if entry.get("prayer"):
        prayer_html = f"""    <div class="ff-prayer">
      <h3>Prayer</h3>
      <p>{esc(entry["prayer"])}</p>
    </div>
"""
    confession_html = ""
    if entry.get("confession"):
        confession_html = f"""    <div class="ff-confession">
      <h3>Confession</h3>
      <p>{esc(entry["confession"])}</p>
    </div>
"""

    # 6. Scriptures referenced — all 47 books get pages
    scriptures_html = ""
    scripture_books = entry.get("scripture_books", [])
    if scripture_books:
        items = []
        for sb in scripture_books:
            name = esc(sb.get("name", ""))
            book_url = resolve_url(patterns["scripture"], origin, sb["slug"])
            items.append(f'        <li><a href="{book_url}">{name}</a></li>')
        scriptures_html = (
            '    <div class="ff-scriptures">\n'
            '      <h3>Scriptures Referenced</h3>\n'
            '      <ul>\n'
            + "\n".join(items) +
            '\n      </ul>\n'
            '    </div>\n'
        )

    # 7. Series
    series_html = ""
    if entry.get("series"):
        s_name = entry["series"]
        s_part = entry.get("series_part", 0)
        s_total = entry.get("series_total", 0)
        siblings = []
        for s in bundle["indexes"]["series"]:
            if s["name"] == s_name:
                for p in s["parts"]:
                    if p["slug"] != entry["slug"]:
                        siblings.append(p)
                break
        series_items = ""
        for sib in siblings:
            sib_url = resolve_url(patterns["entry"], origin, sib["slug"])
            series_items += f'        <li><a href="{sib_url}">{esc(sib["title"])}</a></li>\n'
        series_html = (
            f'    <div class="ff-series">\n'
            f'      <h3>Series: {esc(s_name)}</h3>\n'
            f'      <p>Part {s_part} of {s_total}</p>\n'
            f'      <ul>\n'
            f'{series_items}'
            f'      </ul>\n'
            f'    </div>\n'
        )

    # 8. Tag chips — link only when has_page is true
    themes = bundle["taxonomy"]["facets"]["theme"]["terms"]
    needs = bundle["taxonomy"]["facets"]["need"]["terms"]

    tag_items = []
    for t_slug in entry.get("themes", []):
        label = esc(themes[t_slug]["label"])
        if themes[t_slug].get("has_page", False):
            tag_url = resolve_url(patterns["theme"], origin, t_slug)
            tag_items.append(render_tag(label, tag_url))
        else:
            tag_items.append(render_tag(label))
    for n_slug in entry.get("needs", []):
        label = esc(needs[n_slug]["label"])
        if needs[n_slug].get("has_page", False):
            tag_url = resolve_url(patterns["need"], origin, n_slug)
            tag_items.append(render_tag(label, tag_url))
        else:
            tag_items.append(render_tag(label))

    tags_html = ""
    if tag_items:
        tags_html = '    <div class="ff-tags">\n' + "\n".join(tag_items) + "\n    </div>\n"

    # 9. Previous / Next by order
    current_order = entry["order"]
    prev_entry = next_entry = None
    for e in entries:
        if e["order"] == current_order - 1:
            prev_entry = e
        if e["order"] == current_order + 1:
            next_entry = e

    prev_link = next_link = ""
    if prev_entry:
        prev_url = resolve_url(patterns["entry"], origin, prev_entry["slug"])
        prev_link = f'      <a href="{prev_url}" class="ff-prev">&larr; {esc(prev_entry["title"])}</a>\n'
    if next_entry:
        next_url = resolve_url(patterns["entry"], origin, next_entry["slug"])
        next_link = f'      <a href="{next_url}" class="ff-next">{esc(next_entry["title"])} &rarr;</a>\n'

    prev_next = ""
    if prev_link or next_link:
        prev_next = f"""    <nav class="ff-prev-next">
{prev_link}{next_link}    </nav>
"""

    # Assemble
    page = f"""<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav_tpl}

<section class="article-hero">
  <div class="article-hero-bg"></div>
  <div class="article-hero-content">
    <a href="{resolve_url(patterns['hub'], origin)}" class="article-back-link">&larr; All Fresh Fire</a>
    <h1 class="article-hero-title">{h1}</h1>
  </div>
</section>

<section class="article-body-section">
  <article>
    <div class="article-body-content">
{summary_html}{ks_html}{blocks_html}{prayer_html}{confession_html}{scriptures_html}{series_html}{tags_html}{prev_next}
      <a href="{resolve_url(patterns['hub'], origin)}" class="btn-outline" style="margin-top:2rem;">&larr; All Fresh Fire</a>
    </div>
  </article>
</section>

{footer_tpl}
<script src="/script.js"></script>
</body>
</html>
"""
    return page


# ── Validation ──────────────────────────────────────────────────────────────

def validate(bundle):
    errors = []
    facets = bundle["taxonomy"]["facets"]
    entries = bundle["entries"]

    if len(entries) != 92:
        errors.append(f"Expected 92 entries, got {len(entries)}")

    slugs = [e["slug"] for e in entries]
    dupes = [s for s, c in Counter(slugs).items() if c > 1]
    if dupes:
        errors.append(f"Duplicate slugs: {dupes}")

    orders = [e["order"] for e in entries]
    expected = set(range(1, 93))
    actual = set(orders)
    missing = expected - actual
    extra = actual - expected
    if missing:
        errors.append(f"Missing orders: {sorted(missing)}")
    if extra:
        errors.append(f"Extra orders: {sorted(extra)}")

    for entry_key, fname in [("themes", "theme"), ("needs", "need"),
                              ("practices", "practice"), ("attributes", "attribute")]:
        entry_vals = set()
        for e in entries:
            entry_vals.update(e.get(entry_key, []))
        tax_terms = set(facets[fname].get("terms", {}).keys())
        unresolved = entry_vals - tax_terms
        if unresolved:
            errors.append(f"Unresolved {fname} refs: {unresolved}")

    for e in entries:
        for i, block in enumerate(e.get("blocks", [])):
            if block.get("type") not in ("paragraph", "heading"):
                errors.append(f"Entry {e['slug']} block {i}: invalid type '{block.get('type')}'")

    for e in entries:
        for field in ("slug", "order", "title", "summary", "blocks"):
            if field not in e or e[field] is None:
                errors.append(f"Entry missing '{field}': {e.get('slug', '?')}")

    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    print("✓ Validation passed")


def post_check(output_dir):
    placeholder = "REPLACE_WITH_CONFIRMED_ORIGIN"
    for dirpath, dirnames, filenames in os.walk(output_dir):
        for fn in filenames:
            if fn.endswith(".html"):
                fp = os.path.join(dirpath, fn)
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                    if placeholder in content:
                        print(f"FAIL: {fp} contains '{placeholder}'", file=sys.stderr)
                        sys.exit(1)
                    if "'REPLACE_WITH_CONFIRMED_ORIGIN'" in content or '"REPLACE_WITH_CONFIRMED_ORIGIN"' in content:
                        print(f"FAIL: {fp} contains escaped placeholder", file=sys.stderr)
                        sys.exit(1)
    print("✓ Post-check: no placeholder in output")


def collect_404s(entries, bundle, origin, patterns):
    """Report pages that are linked as <a> but don't exist yet."""
    themes = bundle["taxonomy"]["facets"]["theme"]["terms"]
    needs = bundle["taxonomy"]["facets"]["need"]["terms"]
    missing = set()
    for e in entries:
        for t in e.get("themes", []):
            if themes[t].get("has_page", False):
                missing.add(resolve_url(patterns["theme"], origin, t))
        for n in e.get("needs", []):
            if needs[n].get("has_page", False):
                missing.add(resolve_url(patterns["need"], origin, n))
        for sb in e.get("scripture_books", []):
            missing.add(resolve_url(patterns["scripture"], origin, sb["slug"]))
    return sorted(missing)


def main():
    bundle = load_bundle()
    head_tpl, nav_tpl, footer_tpl = load_templates()
    validate(bundle)

    origin = bundle["collection"]["origin"]
    patterns = bundle["collection"]["url_patterns"]
    entries = bundle["entries"]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for entry in entries:
        out_path = os.path.join(OUTPUT_DIR, f"{entry['slug']}.html")
        html_content = build_entry(entry, origin, entries, head_tpl, nav_tpl, footer_tpl, bundle, patterns)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"✓ Wrote {len(entries)} entry pages to {OUTPUT_DIR}")
    post_check(OUTPUT_DIR)

    missing = collect_404s(entries, bundle, origin, patterns)
    print(f"\n✓ Generation complete.")
    print(f"\n--- Links that will 404 ({len(missing)} total) ---")
    for url in missing:
        print(f"  {url}")
    actual_scriptures = len(bundle["indexes"]["scripture_books"])
    print(f"\nExpected: {actual_scriptures} scripture books + 8 themes (has_page) + 3 needs (has_page) = {actual_scriptures + 8 + 3}")


if __name__ == "__main__":
    main()