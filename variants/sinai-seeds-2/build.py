#!/usr/bin/env python3
"""Build the "no Facebook" version of the Sinai Seeds card.

Reads the single source of truth (../../site/index.html), removes every trace of
Facebook from it, and writes the result next to this script. Nothing is edited
by hand in the generated file: re-run this after changing site/index.html.

What it removes:
  1. the Facebook icon button in the social row (grid goes from 4 to 3 columns)
  2. the Facebook URL from the vCard the "Save contact" button builds
  3. adds <meta name="robots" content="noindex"> because this is a preview copy

Assets (img/, og.jpg, og.png) are copied from ../../site so the page works
standalone. Run:  python3 build.py
"""
import pathlib, re, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent.parent / "site"      # the real card, the single source of truth
OUT = HERE / "site"                     # what gets deployed (wrangler assets dir)

FACEBOOK_URL = "https://www.facebook.com/share/1ChyrUYQ5d/?mibextid=wwXIfr"


def main() -> int:
    src = (SITE / "index.html").read_text(encoding="utf-8")
    out = src

    # 1. drop the Facebook button in the social row
    before = out
    out = re.sub(
        r'\n[ \t]*<a href="https://www\.facebook\.com/[^"]*"[^>]*>.*?</a>',
        "",
        out,
        flags=re.S,
    )
    if out == before:
        sys.exit("Facebook button not found in site/index.html")

    # 2. three icons instead of four
    out = out.replace('class="sscx-social sscx-social4"', 'class="sscx-social sscx-social3"')
    out = out.replace(
        ".sscx-social.sscx-social4 { grid-template-columns: repeat(4, 1fr); }",
        ".sscx-social.sscx-social4 { grid-template-columns: repeat(4, 1fr); }\n"
        ".sscx-social.sscx-social3 { grid-template-columns: repeat(3, 1fr); }",
    )

    # 3. no Facebook link in the saved contact
    if FACEBOOK_URL not in out:
        sys.exit("Facebook URL not found in the vCard builder")
    out = out.replace(f" 'URL:{FACEBOOK_URL}',", "")

    # 4. this is a preview copy, keep it out of search results
    out = out.replace(
        '<meta charset="UTF-8">',
        '<meta charset="UTF-8">\n<meta name="robots" content="noindex">',
        1,
    )

    # a CSS comment still mentions that the logo came from a Facebook post, that is fine
    if "facebook.com" in out.lower():
        sys.exit("A Facebook link survived the cleaning")

    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(out, encoding="utf-8")

    dst = OUT / "img"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SITE / "img", dst)
    for name in ("og.jpg", "og.png"):
        shutil.copy2(SITE / name, OUT / name)

    print("wrote", OUT / "index.html", len(out), "bytes; facebook.com links left:", out.lower().count("facebook.com"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
