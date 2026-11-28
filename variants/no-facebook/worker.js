// Sinai Seeds card: minimal Cloudflare Worker (module syntax).
// NOTE: reconstructed from the live site. The deployed script embeds the same
// files as constants; this version reads them from the ../site folder at build time.
// Simplest deploy: `npx wrangler deploy` using the wrangler.toml next to this file
// (static assets from ../site). The Worker code below only adds /og.jpg and /og.png caching headers.
// The live script serves /og.jpg (image/jpeg, the link-preview image used by og:image); /og.png stays for old cached previews.
export default {
  async fetch(request, env) {
    const res = await env.ASSETS.fetch(request);
    const url = new URL(request.url);
    if (url.pathname === "/og.png" || url.pathname === "/og.jpg") {
      const r = new Response(res.body, res);
      r.headers.set("Cache-Control", "public, max-age=300");
      return r;
    }
    return res;
  },
};
