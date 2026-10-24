// TollBit integration for thedosagemag.com (Netlify Edge Function)
//
// What it does
//   1. Sends known AI bots to The Dosage's TollBit subdomain with a 302,
//      where TollBit can let them read for free, charge them, or refuse them.
//   2. Optionally sends a one-line log of each page request to TollBit's
//      Log Sink API so the TollBit dashboard can show bot traffic.
//
// It does nothing until the environment variables below are set in
// Netlify (Site configuration > Environment variables). With neither set,
// every request passes straight through, so merging this is safe.
//
//   TOLLBIT_SUBDOMAIN   e.g. tollbit.thedosagemag.com   (turns on redirects)
//   TOLLBIT_KEY         secret key from the TollBit dashboard (turns on logs)
//
// Never put the key in this file or anywhere in the repo.
// Docs: https://docs.tollbit.com/docs/other  and  /docs/verifying-a-property

// Bot list from TollBit's general integration guide (Oct 2026).
// Keep it in step with Bot Management in the TollBit dashboard.
const BOTS = [
  "chatgpt-user", "perplexitybot", "gptbot", "anthropic-ai", "ccbot",
  "claude-web", "claudebot", "claude-user", "claude-searchbot", "cohere-ai",
  "youbot", "diffbot", "oai-searchbot", "meta-externalagent", "timpibot",
  "amazonbot", "bytespider", "perplexity-user", "shapbot", "shap-user",
];

// Files every crawler should still be able to read on the main site.
const ALWAYS_SERVE = new Set([
  "/robots.txt", "/sitemap.xml", "/news-sitemap.xml", "/feed.xml",
  "/smartnews.xml", "/ads.txt",
]);

function isBot(ua) {
  const s = ua.toLowerCase();
  if (s.includes("tollbot")) return false; // TollBit's own crawler
  return BOTS.some((b) => s.includes(b));
}

function sendLog(context, key, req, url, status, ua) {
  const line = JSON.stringify({
    timestamp: new Date().toISOString(),
    host: url.host,
    url: url.pathname + url.search,
    request_method: req.method,
    request_user_agent: ua,
    request_referer: req.headers.get("referer") || "",
    response_status: status,
    ip_address: context.ip || "",
    country: (context.geo && context.geo.country && context.geo.country.code) || "",
  });
  const p = fetch("https://log.tollbit.com/log", {
    method: "POST",
    headers: { "TollbitKey": key, "Content-Type": "application/json" },
    body: line + "\n",
  }).catch(() => {}); // logging must never break the page
  if (typeof context.waitUntil === "function") context.waitUntil(p);
}

export default async (req, context) => {
  const sub = Netlify.env.get("TOLLBIT_SUBDOMAIN");
  const key = Netlify.env.get("TOLLBIT_KEY");
  if (!sub && !key) return; // not switched on yet: serve the site as normal

  const url = new URL(req.url);
  const ua = req.headers.get("user-agent") || "";

  if (sub && isBot(ua) && !ALWAYS_SERVE.has(url.pathname)) {
    if (key) sendLog(context, key, req, url, 302, ua);
    return new Response(null, {
      status: 302, // temporary, as TollBit asks, so nothing gets cached
      headers: { Location: `https://${sub}${url.pathname}${url.search}` },
    });
  }

  const res = await context.next();
  if (key) sendLog(context, key, req, url, res.status, ua);
  return res;
};

export const config = {
  path: "/*",
  // Skip images and other static files to keep edge invocations (and credits) down.
  excludedPath: [
    "/posts/img/*", "/*.jpg", "/*.jpeg", "/*.png", "/*.webp", "/*.gif",
    "/*.svg", "/*.ico", "/*.css", "/*.js", "/*.woff2", "/*.mp4",
  ],
};
