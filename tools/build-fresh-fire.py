#!/usr/bin/env python3
"""
build-fresh-fire.py — Generator for the Fresh Fire for Today section.

Zero third-party dependencies. Reads tools/fresh-fire-bundle.json (the single
source of truth) and writes entry and index HTML files into resources/fresh-fire/.

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


# ── URL helpers ────────────────────────────────────────────────────────────

def href_url(pattern, slug=None):
    """Root-relative URL for href attributes in page content.
    Replaces {origin} with empty string so links stay on the current domain.
    """
    url = pattern.replace("{origin}", "")
    if slug is not None:
        url = url.replace("{slug}", slug)
    return url


def abs_url(pattern, origin, slug=None):
    """Absolute URL for canonical/OG/JSON-LD use.
    Replaces {origin} with the actual origin string.
    """
    url = pattern.replace("{origin}", origin)
    if slug is not None:
        url = url.replace("{slug}", slug)
    return url


def fill_head(title, meta_desc, canonical_url, head_tpl):
    """Fill head template placeholders for any page."""
    h = head_tpl
    h = h.replace("{{TITLE}}", f"{esc(title)} — GEM Chapel")
    h = h.replace("{{META_DESC}}", esc(meta_desc))
    h = h.replace("{{CANONICAL_URL}}", esc(canonical_url))
    h = h.replace("{{OG_DESC}}", esc(meta_desc))
    h = h.replace("{{OG_TYPE}}", "website")
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


HUB_HREF = None  # set at runtime in main()


def build_entry(entry, origin, entries, head_tpl, nav_tpl, footer_tpl, bundle, patterns):
    """Build one devotional entry page per Prompt 3 spec."""
    p = patterns
    # Head — canonical URLs stay absolute
    canonical_url = abs_url(p["entry"], origin, entry["slug"])
    meta_desc = entry["summary"][:160]
    head = fill_head(entry["title"], meta_desc, canonical_url, head_tpl)

    h1 = esc(entry["title"])

    summary_html = ""
    if entry.get("summary"):
        summary_html = f'    <p class="ff-in-short"><strong>In short:</strong> {esc(entry["summary"])}</p>\n'

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

    blocks_html = render_blocks(entry.get("blocks", []))

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

    scriptures_html = ""
    scripture_books = entry.get("scripture_books", [])
    if scripture_books:
        items = []
        for sb in scripture_books:
            name = esc(sb.get("name", ""))
            book_url = href_url(p["scripture"], sb["slug"])
            items.append(f'        <li><a href="{book_url}">{name}</a></li>')
        scriptures_html = (
            '    <div class="ff-scriptures">\n'
            '      <h3>Scriptures Referenced</h3>\n'
            '      <ul>\n'
            + "\n".join(items) +
            '\n      </ul>\n'
            '    </div>\n'
        )

    series_html = ""
    if entry.get("series"):
        s_name = entry["series"]
        s_part = entry.get("series_part", 0)
        s_total = entry.get("series_total", 0)
        siblings = []
        for s in bundle["indexes"]["series"]:
            if s["name"] == s_name:
                for p_sib in s["parts"]:
                    if p_sib["slug"] != entry["slug"]:
                        siblings.append(p_sib)
                break
        series_items = ""
        for sib in siblings:
            sib_url = href_url(p["entry"], sib["slug"])
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

    themes = bundle["taxonomy"]["facets"]["theme"]["terms"]
    needs = bundle["taxonomy"]["facets"]["need"]["terms"]

    tag_items = []
    for t_slug in entry.get("themes", []):
        label = esc(themes[t_slug]["label"])
        if themes[t_slug].get("has_page", False):
            tag_url = href_url(p["theme"], t_slug)
            tag_items.append(render_tag(label, tag_url))
        else:
            tag_items.append(render_tag(label))
    for n_slug in entry.get("needs", []):
        label = esc(needs[n_slug]["label"])
        if needs[n_slug].get("has_page", False):
            tag_url = href_url(p["need"], n_slug)
            tag_items.append(render_tag(label, tag_url))
        else:
            tag_items.append(render_tag(label))

    tags_html = ""
    if tag_items:
        tags_html = '    <div class="ff-tags">\n' + "\n".join(tag_items) + "\n    </div>\n"

    current_order = entry["order"]
    prev_entry = next_entry = None
    for e in entries:
        if e["order"] == current_order - 1:
            prev_entry = e
        if e["order"] == current_order + 1:
            next_entry = e

    prev_link = next_link = ""
    if prev_entry:
        prev_url = href_url(p["entry"], prev_entry["slug"])
        prev_link = f'      <a href="{prev_url}" class="ff-prev">&larr; {esc(prev_entry["title"])}</a>\n'
    if next_entry:
        next_url = href_url(p["entry"], next_entry["slug"])
        next_link = f'      <a href="{next_url}" class="ff-next">{esc(next_entry["title"])} &rarr;</a>\n'

    prev_next = ""
    if prev_link or next_link:
        prev_next = f"""    <nav class="ff-prev-next">
{prev_link}{next_link}    </nav>
"""

    hub_href = href_url(p["hub"])

    page = f"""<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav_tpl}

<section class="article-hero">
  <div class="article-hero-bg"></div>
  <div class="article-hero-content">
    <a href="{hub_href}" class="article-back-link">&larr; All Fresh Fire</a>
    <h1 class="article-hero-title">{h1}</h1>
  </div>
</section>

<section class="article-body-section">
  <article>
    <div class="article-body-content">
{summary_html}{ks_html}{blocks_html}{prayer_html}{confession_html}{scriptures_html}{series_html}{tags_html}{prev_next}
      <a href="{hub_href}" class="btn-outline" style="margin-top:2rem;">&larr; All Fresh Fire</a>
    </div>
  </article>
</section>

{footer_tpl}
<script src="/script.js"></script>
</body>
</html>
"""
    return page


def build_term_index(term_type, term_slug, term_data, entries_for_term, origin, head_tpl, nav_tpl, footer_tpl, patterns):
    """Build an index page for a theme, need, or scripture term."""
    p = patterns
    canonical = abs_url(p[term_type], origin, term_slug)
    title = term_data["label"]
    meta_desc = term_data.get("definition", "")[:160] if term_data.get("definition") else f"Devotionals about {term_data['label']}"
    head = fill_head(title, meta_desc, canonical, head_tpl)

    hero_title = esc(title)

    definition_html = ""
    if term_data.get("definition"):
        definition_html = f'    <p>{esc(term_data["definition"])}</p>\n'

    entries_html = ""
    if entries_for_term:
        items = []
        for entry in entries_for_term:
            item_title = esc(entry["title"])
            item_summary = esc(entry["summary"]) if entry.get("summary") else ""
            entry_url = href_url(p["entry"], entry["slug"])
            items.append(f'      <li><a href="{entry_url}"><strong>{item_title}</strong><br>{item_summary}</a></li>')
        entries_html = (
            '    <ul class="ff-entry-list">\n'
            + "\n".join(items) +
            '\n    </ul>\n'
        )

    hub_href = href_url(p["hub"])

    page = f"""<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav_tpl}

<section class="article-hero">
  <div class="article-hero-bg"></div>
  <div class="article-hero-content">
    <a href="{hub_href}" class="article-back-link">&larr; All Fresh Fire</a>
    <h1 class="article-hero-title">{hero_title}</h1>
  </div>
</section>

<section class="article-body-section">
  <article>
    <div class="article-body-content">
{definition_html}{entries_html}
      <a href="{hub_href}" class="btn-outline" style="margin-top:2rem;">&larr; All Fresh Fire</a>
    </div>
  </article>
</section>

{footer_tpl}
<script src="/script.js"></script>
</body>
</html>
"""
    return page


def build_names_of_god_index(attributes_entries, origin, head_tpl, nav_tpl, footer_tpl, patterns):
    """Build the names-of-god index page with all 9 attribute entries."""
    p = patterns
    canonical = abs_url(p["names_of_god"], origin)
    head = fill_head("Names of God", "Devotionals exploring the names and attributes of God", canonical, head_tpl)

    hero_title = "Names of God"

    definition_html = '    <p>Exploring the divine nature and attributes of God through devotionals focused on His names and characteristics.</p>\n'

    entries_html = ""
    if attributes_entries:
        items = []
        for entry in attributes_entries:
            item_title = esc(entry["title"])
            item_summary = esc(entry["summary"]) if entry.get("summary") else ""
            entry_url = href_url(p["entry"], entry["slug"])
            items.append(f'      <li><a href="{entry_url}"><strong>{item_title}</strong><br>{item_summary}</a></li>')
        entries_html = (
            '    <ul class="ff-entry-list">\n'
            + "\n".join(items) +
            '\n    </ul>\n'
        )

    hub_href = href_url(p["hub"])

    page = f"""<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav_tpl}

<section class="article-hero">
  <div class="article-hero-bg"></div>
  <div class="article-hero-content">
    <a href="{hub_href}" class="article-back-link">&larr; All Fresh Fire</a>
    <h1 class="article-hero-title">{hero_title}</h1>
  </div>
</section>

<section class="article-body-section">
  <article>
    <div class="article-body-content">
{definition_html}{entries_html}
      <a href="{hub_href}" class="btn-outline" style="margin-top:2rem;">&larr; All Fresh Fire</a>
    </div>
  </article>
</section>

{footer_tpl}
<script src="/script.js"></script>
</body>
</html>
"""
    return page


def build_hub_navigation(patterns, bundle):
    """Build navigation block linking to theme, need, scripture, and names-of-god pages.
    Uses root-relative hrefs."""
    p = patterns
    themes = bundle["taxonomy"]["facets"]["theme"]["terms"]
    needs = bundle["taxonomy"]["facets"]["need"]["terms"]

    theme_links = []
    for slug, data in themes.items():
        if data.get("has_page", False):
            url = href_url(p["theme"], slug)
            label = esc(data["label"])
            theme_links.append(f'      <li><a href="{url}">{label}</a></li>')

    theme_nav = ""
    if theme_links:
        theme_nav = (
            '    <div class="ff-hub-nav">\n'
            '      <h3>Themes</h3>\n'
            '      <ul>\n'
            + "\n".join(theme_links) +
            '\n      </ul>\n'
            '    </div>\n'
        )

    need_links = []
    for slug, data in needs.items():
        if data.get("has_page", False):
            url = href_url(p["need"], slug)
            label = esc(data["label"])
            need_links.append(f'      <li><a href="{url}">{label}</a></li>')

    need_nav = ""
    if need_links:
        need_nav = (
            '    <div class="ff-hub-nav">\n'
            '      <h3>Needs</h3>\n'
            '      <ul>\n'
            + "\n".join(need_links) +
            '\n      </ul>\n'
            '    </div>\n'
        )

    scriptures = bundle["indexes"]["scripture_books"]
    scripture_links = []
    for book in scriptures:
        url = href_url(p["scripture"], book["slug"])
        label = esc(book["name"])
        scripture_links.append(f'      <li><a href="{url}">{label}</a></li>')

    scripture_nav = ""
    if scripture_links:
        scripture_nav = (
            '    <div class="ff-hub-nav">\n'
            '      <h3>Scriptures</h3>\n'
            '      <ul>\n'
            + "\n".join(scripture_links) +
            '\n      </ul>\n'
            '    </div>\n'
        )

    names_url = href_url(p["names_of_god"])
    names_nav = f'    <div class="ff-hub-nav">\n      <h3><a href="{names_url}">Names of God</a></h3>\n    </div>\n'

    nav_block = (
        '    <div class="ff-hub-navigation">\n'
        f'{theme_nav}'
        f'{need_nav}'
        f'{scripture_nav}'
        f'{names_nav}'
        '    </div>\n'
    )
    return nav_block


def build_hub(all_entries, origin, head_tpl, nav_tpl, footer_tpl, patterns, bundle):
    """Build the main hub index.html page with all entries and navigation."""
    p = patterns
    canonical = abs_url(p["hub"], origin)
    head = fill_head("Fresh Fire for Today", "Search and explore daily devotional readings from the Fresh Fire for Today series by Great Expectations Ministries.", canonical, head_tpl)

    hero_section = """<section class="article-hero">
  <div class="article-hero-bg"></div>
  <div class="article-hero-content">
    <h1 class="article-hero-title">Fresh Fire for Today</h1>
  </div>
</section>

<section class="ff-search-section">
  <div class="ff-search-inner">
    <div class="ff-search-bar">
      <svg class="ff-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
      <input type="text" id="ff-search-input" class="ff-search-input" placeholder="Search devotionals...">
    </div>
    <div id="ff-results"></div>
  </div>
</section>"""

    items = []
    for entry in all_entries:
        item_title = esc(entry["title"])
        item_summary = esc(entry["summary"]) if entry.get("summary") else ""
        entry_url = href_url(p["entry"], entry["slug"])
        items.append(f'      <li><a href="{entry_url}"><strong>{item_title}</strong><br>{item_summary}</a></li>')
    entries_html = (
        '    <ul class="ff-entry-list">\n'
        + "\n".join(items) +
        '\n    </ul>\n'
    )

    nav_block = build_hub_navigation(p, bundle)

    page = f"""<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav_tpl}

{hero_section}

<section class="article-body-section">
  <article>
    <div class="article-body-content">
{entries_html}
{nav_block}
    </div>
  </article>
</section>

{footer_tpl}
<script src="/script.js"></script>
<script src="fresh-fire-search.js"></script>
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


def check_absolute_hrefs(output_dir, origin):
    """Warn if any page content hrefs use the absolute origin URL.
    This catches content hrefs that should be root-relative."""
    print("Checking for absolute hrefs in page content ...")
    found = 0
    for dirpath, dirnames, filenames in os.walk(output_dir):
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            fp = os.path.join(dirpath, fn)
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()

            import re
            # Look for href="<origin>/resources/fresh-fire/..." which should be root-relative
            pattern = re.escape(origin) + r'/resources/fresh-fire/'
            matches = re.findall(r'href="' + pattern + r'[^"]*"', content)
            # Exclude the canonical/OG URLs in <head>
            in_head = True
            for m in matches:
                # Only flag matches that are NOT inside <link> or <meta> tags
                pos = content.find(m)
                before = content[max(0,pos-100):pos]
                if 'link rel="canonical"' in before or 'og:url' in before or 'og:image' in before:
                    continue
                found += 1
                print(f"  ABSOLUTE HREF in {fp}: {m[:80]}...")
    if found:
        print(f"  FAIL: {found} content hrefs use absolute origin URL.", file=sys.stderr)
        sys.exit(1)
    print("  ✓ No absolute hrefs in page content.")


def collect_404s(entries, bundle, patterns):
    """Report pages that are linked as <a> but don't exist yet."""
    themes = bundle["taxonomy"]["facets"]["theme"]["terms"]
    needs = bundle["taxonomy"]["facets"]["need"]["terms"]
    missing = set()
    for e in entries:
        for t in e.get("themes", []):
            if themes[t].get("has_page", False):
                missing.add(href_url(patterns["theme"], t))
        for n in e.get("needs", []):
            if needs[n].get("has_page", False):
                missing.add(href_url(patterns["need"], n))
        for sb in e.get("scripture_books", []):
            missing.add(href_url(patterns["scripture"], sb["slug"]))
    return sorted(missing)


def main():
    bundle = load_bundle()
    head_tpl, nav_tpl, footer_tpl = load_templates()
    validate(bundle)

    origin = bundle["collection"]["origin"]
    patterns = bundle["collection"]["url_patterns"]
    entries = bundle["entries"]

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Entry pages ──
    for entry in entries:
        out_path = os.path.join(OUTPUT_DIR, f"{entry['slug']}.html")
        html_content = build_entry(entry, origin, entries, head_tpl, nav_tpl, footer_tpl, bundle, patterns)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    print(f"✓ Wrote {len(entries)} entry pages to {OUTPUT_DIR}")

    # ── Theme index pages (only where has_page=true) ──
    themes = bundle["taxonomy"]["facets"]["theme"]["terms"]
    theme_pages = 0
    for slug, data in themes.items():
        if data.get("has_page", False):
            entries_for_theme = [e for e in entries if slug in e.get("themes", [])]
            entries_for_theme.sort(key=lambda x: x["order"])
            out_path = os.path.join(OUTPUT_DIR, "theme", f"{slug}.html")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            html_content = build_term_index("theme", slug, data, entries_for_theme, origin, head_tpl, nav_tpl, footer_tpl, patterns)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            theme_pages += 1
    print(f"✓ Wrote {theme_pages} theme index pages to {OUTPUT_DIR}/theme/")

    # ── Need index pages (only where has_page=true) ──
    needs = bundle["taxonomy"]["facets"]["need"]["terms"]
    need_pages = 0
    for slug, data in needs.items():
        if data.get("has_page", False):
            entries_for_need = [e for e in entries if slug in e.get("needs", [])]
            entries_for_need.sort(key=lambda x: x["order"])
            out_path = os.path.join(OUTPUT_DIR, "need", f"{slug}.html")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            html_content = build_term_index("need", slug, data, entries_for_need, origin, head_tpl, nav_tpl, footer_tpl, patterns)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            need_pages += 1
    print(f"✓ Wrote {need_pages} need index pages to {OUTPUT_DIR}/need/")

    # ── Scripture index pages ──
    scriptures = bundle["indexes"]["scripture_books"]
    scripture_pages = 0
    for book in scriptures:
        entries_for_book = [e for e in entries if any(sb["slug"] == book["slug"] for sb in e.get("scripture_books", []))]
        entries_for_book.sort(key=lambda x: x["order"])
        out_path = os.path.join(OUTPUT_DIR, "scripture", f"{book['slug']}.html")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        term_data = {"label": book["name"], "definition": f"Devotionals referencing {book['name']}"}
        html_content = build_term_index("scripture", book["slug"], term_data, entries_for_book, origin, head_tpl, nav_tpl, footer_tpl, patterns)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        scripture_pages += 1
    print(f"✓ Wrote {scripture_pages} scripture index pages to {OUTPUT_DIR}/scripture/")

    # ── Names-of-God index page ──
    attributes_entries = [e for e in entries if e.get("attributes")]
    attributes_entries.sort(key=lambda x: x["order"])
    names_path = os.path.join(OUTPUT_DIR, "names-of-god.html")
    html_content = build_names_of_god_index(attributes_entries, origin, head_tpl, nav_tpl, footer_tpl, patterns)
    with open(names_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✓ Wrote names-of-god index page to {names_path}")

    # ── Hub index page ──
    hub_path = os.path.join(OUTPUT_DIR, "index.html")
    html_content = build_hub(entries, origin, head_tpl, nav_tpl, footer_tpl, patterns, bundle)
    with open(hub_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✓ Rewrote hub index.html at {hub_path}")

    # ── Post checks ──
    post_check(OUTPUT_DIR)
    check_absolute_hrefs(OUTPUT_DIR, origin)

    print(f"\n✓ Generation complete.")
    print(f"\nPage counts:")
    print(f"  Entry pages: {len(entries)}")
    print(f"  Theme index pages: {theme_pages}")
    print(f"  Need index pages: {need_pages}")
    print(f"  Scripture index pages: {scripture_pages}")
    print(f"  Names-of-God index page: 1")
    print(f"  Hub index page: 1")


if __name__ == "__main__":
    main()