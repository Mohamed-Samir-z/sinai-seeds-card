# Sinai Seeds - digital contact card (Aly Fayed)

Live: https://sinai-seeds.mo2868417.workers.dev

## Contents
- site/index.html      The whole card: HTML, CSS and JS in one file (no build step). Contains the logo SVG, the vCard generator ("Save contact"), and all 4 languages.
- site/og.jpg          1200x630 link-preview image (WhatsApp/Facebook, 67 KB), referenced by og:image / twitter:image. site/og.png is the old 534 KB version, kept so cached previews still load.
- site/og-preview.html The HTML the og.png was rendered from (served live at /og-preview).
- worker/              worker.js + wrangler.toml for Cloudflare Workers (see note below).
- assets/logo.svg      The three-leaf logo extracted from index.html.
- assets/contact.vcf   The vCard the "Save contact" button builds (name, company, phone, email, address, Facebook).
- qr/                  3 QR PNGs (poster, clean, round sticker) + generate_qr.py (needs: pip install segno pillow numpy) + og source used for the logo cut.

## Languages
Arabic (RTL), English, Turkish, Chinese. The switcher flips layout direction for Arabic.

## Deploy
1. cd worker && npx wrangler login   (or set CLOUDFLARE_API_TOKEN yourself with Workers Scripts Edit)
2. npx wrangler deploy
To change the link preview: re-render og-preview.html to a 1200x630 image (keep it under 300 KB for WhatsApp) and replace site/og.jpg. WhatsApp caches previews, so share the link with ?v=2 to test.

## Notes
- No tokens or secrets are included.
- worker/worker.js is a clean reconstruction using static assets, not a byte copy of the script currently deployed (that one inlines the files). Site files are byte copies from the live Worker.
- QR error correction is H; re-run generate_qr.py after changing URL in the script.

## Change log
- 2026-11-27: fonts no longer block rendering; closed language menu out of tab order; Arabic button icons fixed; empty toast hidden; 44px menu items; language button label; main landmark; og.png (534 KB) replaced by og.jpg (67 KB); new "Catalog" button (https://www.sinai-seeds.com/) in 4 languages; vCard has the website as first URL, Facebook second.
