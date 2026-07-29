/**
 * fyp.vasanth.my — multi-page password-gated FYP board
 * Secrets: SITE_PASSWORD, SESSION_SECRET
 */
const COOKIE = "fyp_session";
const MAX_AGE = 7 * 86400;

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
  <div class="kicker" style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:10px">Private research · BG4801</div>
  <h1>Research Gap Agent</h1>
  <p>Passphrase-gated multi-page progress board.</p>
  <label for="password">Passphrase</label>
  <input id="password" name="password" type="password" required autofocus enterkeyhint="go"/>
  <button type="submit">Continue</button>
  <div class="err">${error ? escapeHtml(error) : ""}</div>
</form>
</body></html>`;
}

const PUBLIC_PREFIXES = ["/css/", "/js/", "/data/", "/diagrams/", "/favicon"];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const secret = env.SESSION_SECRET || env.SITE_PASSWORD || "dev";
    const password = env.SITE_PASSWORD || "";
    const cookies = parseCookies(request.headers.get("Cookie") || "");
    const session = await verifySession(cookies[COOKIE], secret);

    if (url.pathname === "/logout") {
      return new Response(null, {
        status: 302,
        headers: {
          Location: "/",
          "Set-Cookie": `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`,
        },
      });
    }

    if (url.pathname === "/login" && request.method === "POST") {
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

    // Allow static assets only when authenticated (except nothing public)
    if (!session) {
      // Still serve CSS for login page
      if (url.pathname === "/css/board.css") {
        return env.ASSETS.fetch(request);
      }
      return new Response(loginPage(), {
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "no-store",
          "X-Robots-Tag": "noindex",
        },
      });
    }

    // Authenticated: map / to index.html
    let assetUrl = url;
    if (url.pathname === "/" || url.pathname === "") {
      assetUrl = new URL("/index.html", url.origin);
    }

    const res = await env.ASSETS.fetch(new Request(assetUrl, request));
    if (res.status === 404) {
      return new Response("Not found", { status: 404 });
    }
    const headers = new Headers(res.headers);
    headers.set("X-Robots-Tag", "noindex, nofollow");
    if (url.pathname.endsWith(".html") || url.pathname === "/") {
      headers.set("Cache-Control", "no-store");
    }
    return new Response(res.body, { status: res.status, headers });
  },
};
