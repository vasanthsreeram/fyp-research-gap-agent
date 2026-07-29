/**
 * fyp.vasanth.my — multi-page password-gated FYP board
 * Secrets: SITE_PASSWORD, SESSION_SECRET
 */
const COOKIE = "fyp_session";
const MAX_AGE = 7 * 86400;

/** Pretty path → asset file */
const ROUTES = {
  "/": "/index.html",
  "/index.html": "/index.html",
  "/overview": "/index.html",
  "/results": "/results.html",
  "/results.html": "/results.html",
  "/topics": "/topics.html",
  "/topics.html": "/topics.html",
  "/method": "/method.html",
  "/method.html": "/method.html",
  "/docs": "/docs.html",
  "/docs.html": "/docs.html",
};

function b64url(buf) {
  const bytes = buf instanceof ArrayBuffer ? new Uint8Array(buf) : buf;
  let s = "";
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function b64urlDecode(str) {
  str = str.replace(/-/g, "+").replace(/_/g, "/");
  while (str.length % 4) str += "=";
  const bin = atob(str);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}
async function hmacKey(secret) {
  return crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}
async function signSession(payload, secret) {
  const body = b64url(new TextEncoder().encode(JSON.stringify(payload)));
  const key = await hmacKey(secret);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
  return `${body}.${b64url(new Uint8Array(sig))}`;
}
async function verifySession(token, secret) {
  if (!token || !token.includes(".")) return null;
  const [body, sig] = token.split(".");
  if (!body || !sig) return null;
  try {
    const key = await hmacKey(secret);
    const ok = await crypto.subtle.verify(
      "HMAC",
      key,
      b64urlDecode(sig),
      new TextEncoder().encode(body)
    );
    if (!ok) return null;
    const data = JSON.parse(new TextDecoder().decode(b64urlDecode(body)));
    if (data.exp && Date.now() > data.exp) return null;
    return data;
  } catch {
    return null;
  }
}
function parseCookies(header) {
  const out = {};
  if (!header) return out;
  for (const part of header.split(";")) {
    const i = part.indexOf("=");
    if (i < 0) continue;
    out[part.slice(0, i).trim()] = part.slice(i + 1).trim();
  }
  return out;
}
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function loginPage(error = "") {
  return `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<meta name="robots" content="noindex,nofollow"/>
<meta name="theme-color" content="#141413"/>
<title>Research Gap Agent</title>
<link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@500&family=Inter:wght@400;600&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="/css/board.css"/>
</head>
<body class="login">
<form class="login-card" method="POST" action="/login" autocomplete="current-password">
  <div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:10px">Private research · BG4801</div>
  <h1>Research Gap Agent</h1>
  <p>Passphrase-gated multi-page progress board.</p>
  <label for="password">Passphrase</label>
  <input id="password" name="password" type="password" required autofocus enterkeyhint="go"/>
  <button type="submit">Continue</button>
  <div class="err">${error ? escapeHtml(error) : ""}</div>
</form>
</body></html>`;
}

function isStaticPath(pathname) {
  return (
    pathname.startsWith("/css/") ||
    pathname.startsWith("/js/") ||
    pathname.startsWith("/data/") ||
    pathname.startsWith("/diagrams/")
  );
}

async function asset(env, request, path) {
  const u = new URL(path, "https://assets.local");
  // Prefer ASSETS.fetch with path-only Request (Workers Assets API)
  const res = await env.ASSETS.fetch(new Request(u.toString(), request));
  return res;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    let path = url.pathname;
    if (path.length > 1 && path.endsWith("/")) path = path.slice(0, -1);

    const secret = env.SESSION_SECRET || env.SITE_PASSWORD || "dev";
    const password = env.SITE_PASSWORD || "";
    const cookies = parseCookies(request.headers.get("Cookie") || "");
    const session = await verifySession(cookies[COOKIE], secret);

    if (path === "/logout") {
      return new Response(null, {
        status: 302,
        headers: {
          Location: "/",
          "Set-Cookie": `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`,
        },
      });
    }

    if (path === "/login" && request.method === "POST") {
      const form = await request.formData();
      const pw = String(form.get("password") || "");
      if (!password || pw !== password) {
        return new Response(loginPage("Wrong passphrase."), {
          status: 401,
          headers: { "Content-Type": "text/html; charset=utf-8" },
        });
      }
      const token = await signSession(
        { ok: true, exp: Date.now() + MAX_AGE * 1000, t: Date.now() },
        secret
      );
      return new Response(null, {
        status: 302,
        headers: {
          Location: "/",
          "Set-Cookie": `${COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${MAX_AGE}`,
        },
      });
    }

    // CSS for login always allowed
    if (!session) {
      if (path === "/css/board.css") {
        const res = await asset(env, request, path);
        return res;
      }
      return new Response(loginPage(), {
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "no-store",
          "X-Robots-Tag": "noindex",
        },
      });
    }

    // Static assets
    if (isStaticPath(path)) {
      const res = await asset(env, request, path);
      if (res.status === 404) return new Response("Not found: " + path, { status: 404 });
      const headers = new Headers(res.headers);
      headers.set("X-Robots-Tag", "noindex");
      return new Response(res.body, { status: res.status, headers });
    }

    // HTML pages (pretty or .html)
    const file = ROUTES[path];
    if (!file) {
      return new Response("Not found", { status: 404 });
    }

    let res = await asset(env, request, file);
    // Retry once on flaky asset miss
    if (res.status === 404) {
      await new Promise((r) => setTimeout(r, 50));
      res = await asset(env, request, file);
    }
    if (res.status === 404) {
      return new Response("Page missing: " + file, { status: 404 });
    }
    const headers = new Headers(res.headers);
    headers.set("Content-Type", "text/html; charset=utf-8");
    headers.set("Cache-Control", "no-store");
    headers.set("X-Robots-Tag", "noindex, nofollow");
    headers.set("X-FYP-Page", file);
    return new Response(res.body, { status: 200, headers });
  },
};
