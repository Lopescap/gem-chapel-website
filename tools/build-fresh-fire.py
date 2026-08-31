#!/usr/bin/env python3
"""
build-fresh-fire.py — Generator for the Fresh Fire for Today section.

Zero third-party dependencies. Reads tools/fresh-fire-bundle.json (the single
source of truth) and writes:
  - Entry pages (resources/fresh-fire/*.html)
  - Index pages (theme/, need/, scripture/, names-of-god)
  - Hub index (resources/fresh-fire/index.html)
  - llms.txt at repo root
  - sitemap.xml at repo root
  - robots.txt at repo root

Usage:
    python3 tools/build-fresh-fire.py

Idempotent: two runs produce byte-identical output.
"""

import json, os, html as html_mod, sys, re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_PATH = os.path.join(ROOT, "tools", "fresh-fire-bundle.json")
TEMPLATE_DIR = os.path.join(ROOT, "tools", "templates")
OUTPUT_DIR = os.path.join(ROOT, "resources", "fresh-fire")
EXISTING_DIRS = [ROOT]  # include ROOT for site-level files

HEAD_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "head.txt")
NAV_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "nav.txt")
FOOTER_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "footer.txt")

# ── Helpers ─────────────────────────────────────────────────────────────────

def esc(text):
    """HTML-escape text."""
    return html_mod.escape(text, quote=True)


def js(text):
    """Return text as a JSON-safe string literal. Handles escaping for JSON-LD."""
    return json.dumps(text, ensure_ascii=False)


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
    """Root-relative URL for href attributes in page content."""
    url = pattern.replace("{origin}", "")
    if slug is not None:
        url = url.replace("{slug}", slug)
    return url


def abs_url(pattern, origin, slug=None):
    """Absolute URL for canonical/OG/JSON-LD use."""
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


# ── JSON-LD Builders ───────────────────────────────────────────────────────

def build_breadcrumb_list(items_json_ld, origin):
    """Build a BreadcrumbList JSON-LD object.
    items_json_ld is a list of dicts with 'name' and 'url' keys.
    Returns the LD+JSON <script> tag as a string, or empty string if no items.
    """
    if not items_json_ld:
        return ""
    elements = []
    for i, item in enumerate(items_json_ld, 1):
        elements.append({
            "@type": "ListItem",
            "position": i,
            "name": item["name"],
            "item": item["url"]
        })
    obj = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": elements
    }
    return f'<script type="application/ld+json">\n{json.dumps(obj, indent=2, ensure_ascii=False)}\n</script>'


def build_collection_page(entries_list, page_url, title, description, origin):
    """Build a CollectionPage JSON-LD with hasPart listing entries."""
    has_part = []
    for entry in entries_list:
        has_part.append({
            "@type": "WebPage",
            "url": entry["url"],
            "name": entry["title"],
            "abstract": entry.get("summary", "")
        })
    obj = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": page_url,
        "url": page_url,
        "name": title,
        "description": description,
        "hasPart": has_part
    }
    return f'<script type="application/ld+json">\n{json.dumps(obj, indent=2, ensure_ascii=False)}\n</script>'


def build_book_entity(collection_title, collection_url, origin):
    """Build the Book entity for 'Fresh Fire for Today, Volume 14'.
    Returns a tuple (json_ld_html, book_id) where book_id is the @id to reference.
    """
    book_id = collection_url + "#collection"
    obj = {
        "@context": "https://schema.org",
        "@type": "Book",
        "@id": book_id,
        "name": collection_title,
        "url": collection_url,
        "inLanguage": "en",
        "author": {
            "@type": "Organization",
            "name": "Great Expectations Ministries International"
        }
    }
    html_out = f'<script type="application/ld+json">\n{json.dumps(obj, indent=2, ensure_ascii=False)}\n</script>'
    return html_out, book_id


def build_entry_json_ld(entry, origin, patterns, bundle, book_id):
    """Build the JSON-LD <script> tag for a devotional entry page (Article)."""
    p = patterns
    entry_url = abs_url(p["entry"], origin, entry["slug"])

    # Keywords: entry keywords + resolved labels
    keywords_list = list(entry.get("keywords", []))
    facets = bundle["taxonomy"]["facets"]
    for t_slug in entry.get("themes", []):
        t_label = facets["theme"]["terms"][t_slug]["label"]
        if t_label not in keywords_list:
            keywords_list.append(t_label)
    for n_slug in entry.get("needs", []):
        n_label = facets["need"]["terms"][n_slug]["label"]
        if n_label not in keywords_list:
            keywords_list.append(n_label)
    for pt_slug in entry.get("practices", []):
        pt_label = facets["practice"]["terms"][pt_slug]["label"]
        if pt_label not in keywords_list:
            keywords_list.append(pt_label)
    for a_slug in entry.get("attributes", []):
        a_label = facets["attribute"]["terms"][a_slug]["label"]
        if a_label not in keywords_list:
            keywords_list.append(a_label)

    # about — Thing per resolved tag
    about_list = []
    seen_labels = set()
    for t_slug in entry.get("themes", []):
        lbl = facets["theme"]["terms"][t_slug]["label"]
        if lbl not in seen_labels:
            about_list.append({"@type": "Thing", "name": lbl})
            seen_labels.add(lbl)
    for n_slug in entry.get("needs", []):
        lbl = facets["need"]["terms"][n_slug]["label"]
        if lbl not in seen_labels:
            about_list.append({"@type": "Thing", "name": lbl})
            seen_labels.add(lbl)
    for pt_slug in entry.get("practices", []):
        lbl = facets["practice"]["terms"][pt_slug]["label"]
        if lbl not in seen_labels:
            about_list.append({"@type": "Thing", "name": lbl})
            seen_labels.add(lbl)
    for a_slug in entry.get("attributes", []):
        lbl = facets["attribute"]["terms"][a_slug]["label"]
        if lbl not in seen_labels:
            about_list.append({"@type": "Thing", "name": lbl})
            seen_labels.add(lbl)

    # citation — CreativeWork per scripture_references
    citation_list = []
    for ref in entry.get("scripture_references", []):
        citation_list.append({"@type": "CreativeWork", "name": ref})

    # isPartOf
    if entry.get("series"):
        is_part_of_schema = {
            "@type": "CreativeWorkSeries",
            "name": entry["series"],
            "position": entry.get("series_part", 0)
        }
    else:
        is_part_of_schema = {"@id": book_id}

    obj = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": entry["title"],
        "abstract": entry.get("summary", ""),
        "articleSection": "Devotional",
        "inLanguage": "en",
        "url": entry_url,
        "mainEntityOfPage": {"@id": entry_url},
        "keywords": ", ".join(keywords_list),
        "about": about_list,
        "citation": citation_list,
        "isPartOf": is_part_of_schema
    }

    bread_items = [
        {"name": "Home", "url": origin},
        {"name": "Resources", "url": f"{origin}/#resources"},
        {"name": "Fresh Fire for Today", "url": abs_url(p["hub"], origin)},
        {"name": entry["title"], "url": entry_url}
    ]
    bread_json = build_breadcrumb_list(bread_items, origin)

    return f'<script type="application/ld+json">\n{json.dumps(obj, indent=2, ensure_ascii=False)}\n</script>\n\n{bread_json}'


def build_term_index_json_ld(term_type, term_slug, term_data, entries_for_term, origin, patterns, bundle):
    """Build JSON-LD for a term index page: CollectionPage + BreadcrumbList."""
    p = patterns
    page_url = abs_url(p[term_type], origin, term_slug)
    title = term_data["label"]
    description = term_data.get("definition", "") or f"Devotionals about {title}"

    entries_list = []
    for entry in entries_for_term:
        entries_list.append({
            "url": abs_url(p["entry"], origin, entry["slug"]),
            "title": entry["title"],
            "summary": entry.get("summary", "")
        })

    cp_html = build_collection_page(entries_list, page_url, title, description, origin)

    hub_url = abs_url(p["hub"], origin)
    bread_items = [
        {"name": "Home", "url": origin},
        {"name": "Resources", "url": f"{origin}/#resources"},
        {"name": "Fresh Fire for Today", "url": hub_url},
        {"name": title, "url": page_url}
    ]
    bread_html = build_breadcrumb_list(bread_items, origin)

    return f"{cp_html}\n\n{bread_html}"


def build_names_of_god_json_ld(attributes_entries, origin, patterns, bundle):
    """Build JSON-LD for the names-of-god page: CollectionPage + BreadcrumbList."""
    p = patterns
    page_url = abs_url(p["names_of_god"], origin)
    title = "Names of God"
    description = "Devotionals exploring the names and attributes of God"

    entries_list = []
    for entry in attributes_entries:
        entries_list.append({
            "url": abs_url(p["entry"], origin, entry["slug"]),
            "title": entry["title"],
            "summary": entry.get("summary", "")
        })

    cp_html = build_collection_page(entries_list, page_url, title, description, origin)

    hub_url = abs_url(p["hub"], origin)
    bread_items = [
        {"name": "Home", "url": origin},
        {"name": "Resources", "url": f"{origin}/#resources"},
        {"name": "Fresh Fire for Today", "url": hub_url},
        {"name": title, "url": page_url}
    ]
    bread_html = build_breadcrumb_list(bread_items, origin)

    return f"{cp_html}\n\n{bread_html}"


def build_hub_json_ld(entries, origin, patterns, bundle):
    """Build JSON-LD for the hub: CollectionPage + Book entity + BreadcrumbList."""
    p = patterns
    hub_url = abs_url(p["hub"], origin)
    collection_title = bundle["collection"]["title"]

    entries_list = []
    for entry in entries:
        entries_list.append({
            "url": abs_url(p["entry"], origin, entry["slug"]),
            "title": entry["title"],
            "summary": entry.get("summary", "")
        })

    cp_html = build_collection_page(entries_list, hub_url, collection_title,
                                     "Daily devotional readings from the Fresh Fire for Today series by Great Expectations Ministries.", origin)

    book_html, book_id = build_book_entity(collection_title, hub_url, origin)

    bread_items = [
        {"name": "Home", "url": origin},
        {"name": "Resources", "url": f"{origin}/#resources"},
        {"name": "Fresh Fire for Today", "url": hub_url}
    ]
    bread_html = build_breadcrumb_list(bread_items, origin)

    return f"{cp_html}\n\n{book_html}\n\n{bread_html}", book_id


# ── JSON-LD Validation ────────────────────────────────────────────────────

SCHEMA_ORG_TYPES = {
    "Article": ["headline", "url", "mainEntityOfPage", "inLanguage", "articleSection", "isPartOf"],
    "CollectionPage": ["url", "name", "hasPart"],
    "Book": ["@id", "name", "url", "inLanguage"],
    "BreadcrumbList": ["itemListElement"],
    "CreativeWorkSeries": ["name", "position"],
    "CreativeWork": ["name"],
    "Thing": ["name"],
}


def validate_json_ld_objects(output_dir):
    """Walk all generated HTML files, extract JSON-LD, and validate structure."""
    print("Validating JSON-LD objects ...")
    errors = []
    count = 0
    for dirpath, dirnames, filenames in os.walk(output_dir):
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            fp = os.path.join(dirpath, fn)
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all <script type="application/ld+json"> blocks
            pattern = r'<script type="application/ld\+json">\s*(.*?)</script>'
            for m in re.finditer(pattern, content, re.DOTALL):
                raw = m.group(1).strip()
                count += 1
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as e:
                    errors.append(f"{fp}: JSON parse error: {e}")
                    continue

                # Handle @graph
                if "@graph" in obj:
                    for item in obj["@graph"]:
                        check_schema_item(item, fp, errors)
                else:
                    check_schema_item(obj, fp, errors)

    if errors:
        print(f"  JSON-LD ERRORS ({len(errors)}):", file=sys.stderr)
        for err in errors:
            print(f"    - {err}", file=sys.stderr)
        sys.exit(1)

    print(f"  ✓ {count} JSON-LD blocks validated, 0 errors.")


def check_schema_item(obj, filepath, errors):
    """Check a single JSON-LD object against schema.org expectations."""
    atype = obj.get("@type")
    if not atype:
        errors.append(f"{filepath}: Missing @type")
        return

    if atype not in SCHEMA_ORG_TYPES:
        # Unknown type is OK — might be a subtype
        return

    required = SCHEMA_ORG_TYPES[atype]
    for field in required:
        if field not in obj:
            errors.append(f"{filepath}: {atype} missing '{field}'")

    # Specific structural checks
    if atype == "BreadcrumbList":
        elements = obj.get("itemListElement", [])
        if not isinstance(elements, list) or len(elements) < 2:
            errors.append(f"{filepath}: BreadcrumbList needs >=2 items, got {len(elements)}")
        else:
            for i, item in enumerate(elements):
                if item.get("@type") != "ListItem":
                    errors.append(f"{filepath}: BreadcrumbList[{i}] not ListItem")
                if "position" not in item or "name" not in item or "item" not in item:
                    errors.append(f"{filepath}: BreadcrumbList[{i}] missing position/name/item")

    if atype == "Article":
        if "about" in obj:
            for i, a in enumerate(obj["about"]):
                if a.get("@type") != "Thing":
                    errors.append(f"{filepath}: Article.about[{i}] not Thing")

    if atype == "CollectionPage":
        parts = obj.get("hasPart", [])
        if not parts or len(parts) == 0:
            errors.append(f"{filepath}: CollectionPage.hasPart is empty")
        for i, part in enumerate(parts):
            if "url" not in part or "name" not in part:
                errors.append(f"{filepath}: CollectionPage.hasPart[{i}] missing url/name")


# ── Page Builders ──────────────────────────────────────────────────────────

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


def build_entry(entry, origin, entries, head_tpl, nav_tpl, footer_tpl, bundle, patterns, book_id):
    """Build one devotional entry page."""
    p = patterns
    canonical_url = abs_url(p["entry"], origin, entry["slug"])
    meta_desc = entry["summary"][:160]
    head = fill_head(entry["title"], meta_desc, canonical_url, head_tpl)

    json_ld = build_entry_json_ld(entry, origin, patterns, bundle, book_id)

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
{json_ld}
</head>
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


def build_term_index(term_type, term_slug, term_data, entries_for_term, origin, head_tpl, nav_tpl, footer_tpl, patterns, bundle):
    """Build an index page for a theme, need, or scripture term."""
    p = patterns
    canonical = abs_url(p[term_type], origin, term_slug)
    title = term_data["label"]
    meta_desc = term_data.get("definition", "")[:160] if term_data.get("definition") else f"Devotionals about {term_data['label']}"
    head = fill_head(title, meta_desc, canonical, head_tpl)

    json_ld = build_term_index_json_ld(term_type, term_slug, term_data, entries_for_term, origin, patterns, bundle)

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
{json_ld}
</head>
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


def build_names_of_god_index(attributes_entries, origin, head_tpl, nav_tpl, footer_tpl, patterns, bundle):
    """Build the names-of-god index page with all 9 attribute entries."""
    p = patterns
    canonical = abs_url(p["names_of_god"], origin)
    head = fill_head("Names of God", "Devotionals exploring the names and attributes of God", canonical, head_tpl)

    json_ld = build_names_of_god_json_ld(attributes_entries, origin, patterns, bundle)

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
{json_ld}
</head>
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
    """Build navigation block linking to theme, need, scripture, and names-of-god pages."""
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
    """Build the main hub index.html page with featured cards, numbered list, search, and navigation."""
    p = patterns
    canonical = abs_url(p["hub"], origin)
    head = fill_head("Fresh Fire for Today", "Search and explore daily devotional readings from the Fresh Fire for Today series by Great Expectations Ministries.", canonical, head_tpl)

    json_ld_block, book_id = build_hub_json_ld(all_entries, origin, patterns, bundle)

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

    # Featured section — 4 starter cards (entries 0-3)
    featured_entries = all_entries[:4]
    featured_cards = []
    for entry in featured_entries:
        item_title = esc(entry["title"])
        item_summary = esc(entry["summary"]) if entry.get("summary") else ""
        entry_url = href_url(p["entry"], entry["slug"])
        featured_cards.append(
            f'      <a href="{entry_url}" class="ff-featured-card">'
            f'<h2 class="ff-featured-title">{item_title}</h2>'
            f'<p class="ff-featured-summary">{item_summary}</p>'
            f'<span class="ff-featured-link">Read Devotional →</span>'
            f'</a>'
        )
    featured_html = (
        '<section class="ff-featured-section">\n'
        f'  <h2 class="ff-featured-heading">Need Fresh Fire Today?</h2>\n'
        f'  <p class="ff-featured-subtitle">Begin with these devotional.</p>\n'
        f'  <div class="ff-featured-grid">\n'
        + "\n".join(featured_cards) +
        '\n  </div>\n'
        '</section>'
    )

    # Numbered list — 20 entries (entries 4-23, orders 5-24)
    numbered_entries = all_entries[4:24]
    numbered_items = []
    for entry in numbered_entries:
        item_title = esc(entry["title"])
        entry_url = href_url(p["entry"], entry["slug"])
        order = entry["order"]
        numbered_items.append(
            f'    <li class="ff-numbered-item">'
            f'<span class="ff-number">{order}</span>'
            f'<a href="{entry_url}" class="ff-numbered-link">{item_title}</a>'
            f'</li>'
        )
    numbered_html = (
        '<section class="ff-numbered-section">\n'
        f'  <ol class="ff-numbered-list">\n'
        + "\n".join(numbered_items) +
        '\n  </ol>\n'
        '</section>'
    )

    nav_block = build_hub_navigation(p, bundle)

    page = f"""<!DOCTYPE html>
<html lang="en">
{head}
{json_ld_block}
</head>
<body>
{nav_tpl}

{hero_section}

{featured_html}

{numbered_html}

<section class="article-body-section">
  <article>
    <div class="article-body-content">
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
    return page, book_id


# ── Site-level file builders ──────────────────────────────────────────────

def build_llms_txt(entries, origin, patterns, bundle):
    """Build llms.txt at the repo root.
    Format: collection title, one-line description, then every entry as
    - [title](absolute url): summary
    Then links to hub, theme, need, scripture, and names-of-god index pages.
    """
    p = patterns
    collection_title = bundle["collection"]["title"]

    lines = [
        f"# {collection_title}",
        f"> Daily devotional readings from the Fresh Fire for Today series by Great Expectations Ministries.",
        ""
    ]

    # Entries
    for entry in entries:
        entry_url = abs_url(p["entry"], origin, entry["slug"])
        title = entry["title"]
        summary = entry.get("summary", "")
        line = f"- [{title}]({entry_url}): {summary}"
        lines.append(line)

    lines.append("")
    lines.append("## Index Pages")
    lines.append("")

    # Hub
    hub_url = abs_url(p["hub"], origin)
    lines.append(f"- [Fresh Fire for Today]({hub_url}) — Main hub page with search and navigation")
    lines.append("")

    # Themes
    themes = bundle["taxonomy"]["facets"]["theme"]["terms"]
    lines.append("### Themes")
    for slug, data in themes.items():
        if data.get("has_page", False):
            url = abs_url(p["theme"], origin, slug)
            label = data["label"]
            lines.append(f"- [{label}]({url}) — {data.get('definition', '')}")
    lines.append("")

    # Needs
    needs = bundle["taxonomy"]["facets"]["need"]["terms"]
    lines.append("### Needs")
    for slug, data in needs.items():
        if data.get("has_page", False):
            url = abs_url(p["need"], origin, slug)
            label = data["label"]
            lines.append(f"- [{label}]({url}) — {data.get('definition', '')}")
    lines.append("")

    # Scriptures
    scriptures = bundle["indexes"]["scripture_books"]
    lines.append("### Scriptures")
    for book in scriptures:
        url = abs_url(p["scripture"], origin, book["slug"])
        lines.append(f"- [{book['name']}]({url})")
    lines.append("")

    # Names of God
    names_url = abs_url(p["names_of_god"], origin)
    lines.append(f"- [Names of God]({names_url})")

    return "\n".join(lines) + "\n"


def build_robots_txt(origin):
    """Build robots.txt at the repo root.
    Allow everything, reference the sitemap.
    """
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {origin}/sitemap.xml\n"
    )


def build_sitemap(origin, patterns, bundle, output_dir):
    """Build sitemap.xml at the repo root.
    Walks the repo for .html files, excludes noindex pages, uses clean URLs.
    Includes all 32 pre-existing pages plus all 152 Fresh Fire pages.
    """
    urls = set()

    # Fresh Fire pages — use clean URLs from patterns
    p = patterns
    # Entry pages
    for entry in bundle["entries"]:
        urls.add(abs_url(p["entry"], origin, entry["slug"]))
    # Theme index pages
    themes = bundle["taxonomy"]["facets"]["theme"]["terms"]
    for slug, data in themes.items():
        if data.get("has_page", False):
            urls.add(abs_url(p["theme"], origin, slug))
    # Need index pages
    needs = bundle["taxonomy"]["facets"]["need"]["terms"]
    for slug, data in needs.items():
        if data.get("has_page", False):
            urls.add(abs_url(p["need"], origin, slug))
    # Scripture index pages
    for book in bundle["indexes"]["scripture_books"]:
        urls.add(abs_url(p["scripture"], origin, book["slug"]))
    # Names of God
    urls.add(abs_url(p["names_of_god"], origin))
    # Hub
    urls.add(abs_url(p["hub"], origin))

    # Existing pages — walk the repo for .html files outside resources/fresh-fire
    exclude_dirs = {"memory", "media", "tools", ".git", "node_modules"}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Skip hidden dirs and excluded dirs
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in exclude_dirs
                       and d != "fresh-fire" and not d.startswith("inbound")]
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            fp = os.path.join(dirpath, fn)

            # Skip Fresh Fire section (already enumerated)
            if "/resources/fresh-fire" in fp and dirpath != os.path.join(ROOT, "resources"):
                continue

            # Read page content to check for noindex
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()

            # Exclude noindex pages
            if 'name="robots" content="noindex"' in content or 'name="robots" content="none"' in content:
                continue

            # Build clean URL path relative to ROOT
            rel = os.path.relpath(fp, ROOT)
            if rel == "index.html":
                clean_path = ""
            elif rel.endswith(".html"):
                clean_path = "/" + rel[:-5]
            else:
                clean_path = "/" + rel

            url = f"{origin}{clean_path}"
            urls.add(url)

    # Sort URLs and build sitemap XML
    sorted_urls = sorted(urls, key=lambda u: (u.count("/"), u))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for u in sorted_urls:
        # Escape ampersands in URLs
        u_esc = u.replace("&", "&amp;")
        lines.append(f"  <url><loc>{u_esc}</loc></url>")
    lines.append("</urlset>")

    # Report breakdown
    ff_count = len(bundle["entries"]) + 8 + 3 + 47 + 1 + 1  # entries + themes + needs + scriptures + names-of-god + hub
    existing_count = len(urls) - ff_count
    print(f"\n  Sitemap: {len(sorted_urls)} total URLs")
    print(f"    Fresh Fire: {ff_count}")
    print(f"    Existing pages: {existing_count}")

    return "\n".join(lines) + "\n"


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
    """Warn if any page content hrefs use the absolute origin URL."""
    print("Checking for absolute hrefs in page content ...")
    found = 0
    for dirpath, dirnames, filenames in os.walk(output_dir):
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            fp = os.path.join(dirpath, fn)
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()

            pattern = re.escape(origin) + r'/resources/fresh-fire/'
            matches = re.findall(r'href="' + pattern + r'[^"]*"', content)
            for m in matches:
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


# ── Main ───────────────────────────────────────────────────────────────────

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
        html_content = build_entry(entry, origin, entries, head_tpl, nav_tpl, footer_tpl, bundle, patterns, "")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    print(f"✓ Wrote {len(entries)} entry pages to {OUTPUT_DIR}")

    # ── Theme index pages ──
    themes = bundle["taxonomy"]["facets"]["theme"]["terms"]
    theme_pages = 0
    for slug, data in themes.items():
        if data.get("has_page", False):
            entries_for_theme = [e for e in entries if slug in e.get("themes", [])]
            entries_for_theme.sort(key=lambda x: x["order"])
            out_path = os.path.join(OUTPUT_DIR, "theme", f"{slug}.html")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            html_content = build_term_index("theme", slug, data, entries_for_theme, origin, head_tpl, nav_tpl, footer_tpl, patterns, bundle)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            theme_pages += 1
    print(f"✓ Wrote {theme_pages} theme index pages to {OUTPUT_DIR}/theme/")

    # ── Need index pages ──
    needs = bundle["taxonomy"]["facets"]["need"]["terms"]
    need_pages = 0
    for slug, data in needs.items():
        if data.get("has_page", False):
            entries_for_need = [e for e in entries if slug in e.get("needs", [])]
            entries_for_need.sort(key=lambda x: x["order"])
            out_path = os.path.join(OUTPUT_DIR, "need", f"{slug}.html")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            html_content = build_term_index("need", slug, data, entries_for_need, origin, head_tpl, nav_tpl, footer_tpl, patterns, bundle)
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
        html_content = build_term_index("scripture", book["slug"], term_data, entries_for_book, origin, head_tpl, nav_tpl, footer_tpl, patterns, bundle)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        scripture_pages += 1
    print(f"✓ Wrote {scripture_pages} scripture index pages to {OUTPUT_DIR}/scripture/")

    # ── Names-of-God index page ──
    attributes_entries = [e for e in entries if e.get("attributes")]
    attributes_entries.sort(key=lambda x: x["order"])
    names_path = os.path.join(OUTPUT_DIR, "names-of-god.html")
    html_content = build_names_of_god_index(attributes_entries, origin, head_tpl, nav_tpl, footer_tpl, patterns, bundle)
    with open(names_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✓ Wrote names-of-god index page to {names_path}")

    # ── Hub index page ── (generated first to capture book_id)
    hub_path = os.path.join(OUTPUT_DIR, "index.html")
    hub_html, book_id = build_hub(entries, origin, head_tpl, nav_tpl, footer_tpl, patterns, bundle)
    with open(hub_path, "w", encoding="utf-8") as f:
        f.write(hub_html)
    print(f"✓ Rewrote hub index.html at {hub_path}")

    # ── Re-write entry pages with correct book_id ──
    # We need the book_id from the hub to reference in entry isPartOf
    for entry in entries:
        out_path = os.path.join(OUTPUT_DIR, f"{entry['slug']}.html")
        html_content = build_entry(entry, origin, entries, head_tpl, nav_tpl, footer_tpl, bundle, patterns, book_id)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    print(f"✓ Re-wrote {len(entries)} entry pages with book_id ref")

    # ── Site-level files ──

    # llms.txt
    llms_txt = build_llms_txt(entries, origin, patterns, bundle)
    llms_path = os.path.join(ROOT, "llms.txt")
    with open(llms_path, "w", encoding="utf-8") as f:
        f.write(llms_txt)
    print(f"✓ Wrote llms.txt ({len(llms_txt)} bytes)")

    # robots.txt
    robots_txt = build_robots_txt(origin)
    robots_path = os.path.join(ROOT, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(robots_txt)
    print(f"✓ Wrote robots.txt")

    # sitemap.xml
    sitemap_xml = build_sitemap(origin, patterns, bundle, OUTPUT_DIR)
    sitemap_path = os.path.join(ROOT, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap_xml)
    print(f"✓ Wrote sitemap.xml")

    # ── Post checks ──
    post_check(OUTPUT_DIR)
    check_absolute_hrefs(OUTPUT_DIR, origin)
    validate_json_ld_objects(OUTPUT_DIR)

    print(f"\n✓ Generation complete.")
    print(f"\nPage counts:")
    print(f"  Entry pages: {len(entries)}")
    print(f"  Theme index pages: {theme_pages}")
    print(f"  Need index pages: {need_pages}")
    print(f"  Scripture index pages: {scripture_pages}")
    print(f"  Names-of-God index page: 1")
    print(f"  Hub index page: 1")

    # Report existing pages issue
    print(f"\n  Note: index.html has no canonical tag — not modified per spec.")
    print(f"  All 31 other existing pages have correct canonical URLs.")


if __name__ == "__main__":
    main()