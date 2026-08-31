#!/usr/bin/env python3
"""
check-fresh-fire-links.py — Standalone link checker for the Fresh Fire section.

Walks every generated .html file under resources/fresh-fire/, extracts hrefs
pointing to /resources/fresh-fire/* (both relative and full-URL forms), maps
them to filesystem paths (accounting for cleanUrls), and asserts each target
file exists on disk. Reports every miss with source page and href.
Exit code 0 = clean, 1 = broken.
"""

import os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF_DIR = os.path.join(ROOT, "resources", "fresh-fire")

# Matches href values that point into the Fresh Fire section.
# Handles both relative (/resources/fresh-fire/...) and full-URL
# (https://*.vercel.app/resources/fresh-fire/...) forms.
HREF_PATTERN = re.compile(
    r'href="(?:https://[^/]+)?(/resources/fresh-fire[^"]*)"'
)


def clean_url_to_fs_path(href):
    """
    Convert a clean-URL path like /resources/fresh-fire/scripture/psalm
    to its expected filesystem path: resources/fresh-fire/scripture/psalm.html
    """
    # Remove leading / (href starts with /)
    path = href.lstrip("/")
    # If the path has an explicit .html extension, use as-is
    if path.endswith(".html"):
        return path
    # /resources/fresh-fire (exact, no trailing path) → index.html
    if path == "resources/fresh-fire":
        return "resources/fresh-fire/index.html"
    # Any other path → append .html (cleanUrls)
    return path + ".html"


def check_links():
    if not os.path.isdir(FF_DIR):
        print(f"FAIL: {FF_DIR} does not exist", file=sys.stderr)
        sys.exit(1)

    # Gather all .html files under FF_DIR
    html_files = []
    for dirpath, dirnames, filenames in os.walk(FF_DIR):
        for fn in filenames:
            if fn.endswith(".html"):
                html_files.append(os.path.join(dirpath, fn))

    if not html_files:
        print("FAIL: no .html files found under resources/fresh-fire/", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {len(html_files)} source files for internal hrefs ...\n")

    visited = {}   # source -> set of hrefs
    broken = []    # list of (source_relative, href, expected_fs_path)

    for fp in html_files:
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        rel = os.path.relpath(fp, ROOT)
        hrefs = HREF_PATTERN.findall(content)

        if not hrefs:
            continue

        visited[rel] = set(hrefs)

        for href in hrefs:
            expected_fs = clean_url_to_fs_path(href)
            expected_abs = os.path.join(ROOT, expected_fs)

            if not os.path.isfile(expected_abs):
                broken.append((rel, href, expected_fs))

    # Deduplicate identical broken entries
    broken = list(set(broken))
    broken.sort()

    # Report
    if broken:
        print(f"  BROKEN LINKS FOUND: {len(broken)}\n")
        for src, href, expected in broken:
            print(f"    Source: {src}")
            print(f"    Href:   {href}")
            print(f"    Expect: {expected}")
            print()
        print(f"  Run: {len(html_files)} source files scanned, {len(visited)} had internal links.")
        print(f"  Broken: {len(broken)}")
        sys.exit(1)
    else:
        print(f"  ✓ All internal links resolve. No broken links found.")
        print(f"  Run: {len(html_files)} source files scanned, {len(visited)} had internal links.")
        return True


if __name__ == "__main__":
    check_links()