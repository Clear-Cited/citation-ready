#!/usr/bin/env python3
"""citation-ready — is your page structured the way AI engines cite? A tiny self-check.

Scores the structural signals our AI Visibility Index *observes* on pages that get
cited by AI engines (ChatGPT, Perplexity, Claude, Gemini, Google AI) — and says so
honestly: these are OBSERVED CORRELATIONS from our measurement, not guarantees.
Given a page's HTML (fetched, local, or the built-in demo), it scores the checkable
signals and prints an honest report.

- Stdlib only. No pip install.
- MOCK mode by default (a built-in demo page, runs offline).
- Point it at a live URL and it will also look for /llms.txt.

This is the standalone public cousin of the engine we run at Clear Cited. The check
logic here is parity-locked to our reference engine; the real service measures the
thing this only heuristically predicts.

Examples
--------
    python citation_ready.py --mock
    python citation_ready.py --url https://example.com
    python citation_ready.py --file page.html
    python citation_ready.py --url https://example.com --json

Made by Clear Cited — https://clearcited.com
"""
from __future__ import annotations
import argparse, json, sys, re, urllib.request, urllib.error, urllib.parse

# ---------------------------------------------------------------------------------------------------
# CHECK ENGINE — parity-locked, byte-identical logic to the Clear Cited reference engine.
# A parity test asserts citation_ready.check(...) == the reference check(...) over fixtures.
# Do NOT "improve" anything between here and the end of the engine block.
# ---------------------------------------------------------------------------------------------------

# The observed-correlation framing that MUST ride every report (honesty rail).
FRAMING = ("These are observed correlations from our AI Visibility Index measurement — signals that "
           "tend to accompany pages AI engines cite. They are not guarantees; the measured answer for "
           "your domain comes from a teardown.")
METHODOLOGY_URL = "/methodology/"

# Each signal: an id, a human label, a weight, and the honest reason it correlates with citations.
# Detection is pure-regex over the HTML string so the JS mirror can match it 1:1.
SIGNALS = [
    {"id": "schema", "label": "Valid schema (JSON-LD) for AI parsing", "weight": 22,
     "why": "Structured data lets engines extract entities and claims cleanly."},
    {"id": "answer_first", "label": "Answer-first structure (direct summary + lists/tables)", "weight": 22,
     "why": "Engines quote pages that state the answer early and in extractable chunks."},
    {"id": "headings", "label": "Clear heading outline (one H1, descriptive H2s)", "weight": 16,
     "why": "A clean outline maps to the sub-questions engines answer."},
    {"id": "freshness", "label": "Freshness signal (dateModified or a recent visible date)", "weight": 16,
     "why": "Engines favour pages that show they are current."},
    {"id": "entity", "label": "Consistent entity (Organization + sameAs / profiles)", "weight": 14,
     "why": "A stable, cross-linked entity is easier to attribute and trust."},
    {"id": "llms_txt", "label": "llms.txt present / referenced", "weight": 10,
     "why": "An llms.txt gives agents a curated map of your canonical content."},
]
_MAXW = sum(s["weight"] for s in SIGNALS)


def _has_schema(html, meta):
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         html, re.S | re.I):
        blob = m.group(1)
        # minimally valid: an @context + @type + a name/headline (parse if we can, else regex)
        try:
            data = json.loads(blob)
            items = data if isinstance(data, list) else [data]
            for it in items:
                if isinstance(it, dict) and it.get("@type") and (it.get("name") or it.get("headline")):
                    return True
        except Exception:
            if re.search(r'"@type"', blob) and re.search(r'"(name|headline)"', blob):
                return True
    return False


def _has_answer_first(html, meta):
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    # a list or a table (extractable chunks) ...
    has_chunk = bool(re.search(r"<(ul|ol|table)\b", body, re.I))
    # ... and a question-style heading OR an early lead paragraph in the first stretch of the body
    heads = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", body, re.S | re.I)
    q_head = any("?" in re.sub(r"<[^>]+>", "", h) or
                 re.match(r"\s*(what|how|why|best|which|when|is |are |should)\b",
                          re.sub(r"<[^>]+>", "", h), re.I) for h in heads)
    m = re.search(r"<h1\b", body, re.I)
    early = body[m.start(): m.start() + 1200] if m else body[:1200]
    lead = bool(re.search(r"<p[^>]*>\s*\w[\w\s,.'\"-]{60,}", early, re.I))
    return has_chunk and (q_head or lead)


def _has_headings(html, meta):
    h1 = len(re.findall(r"<h1\b", html, re.I))
    h2 = len(re.findall(r"<h2\b", html, re.I))
    return h1 == 1 and h2 >= 2


def _has_freshness(html, meta):
    if re.search(r'"dateModified"', html) or re.search(r'datetime=', html, re.I):
        return True
    # a visible recent year (this year or last two) in prose
    yrs = re.findall(r"\b(20\d\d)\b", re.sub(r"<[^>]+>", " ", html))
    if yrs:
        y = max(int(x) for x in yrs)
        return y >= (meta.get("this_year", 2026) - 1)
    return False


def _has_entity(html, meta):
    if re.search(r'"@type"\s*:\s*"Organization"', html) or re.search(r'"sameAs"', html):
        return True
    profiles = len(re.findall(r"(linkedin\.com|twitter\.com|x\.com/|github\.com|youtube\.com)", html, re.I))
    return profiles >= 2


def _has_llms(html, meta):
    if meta.get("llms_txt_found"):        # the CLI can actually fetch /llms.txt
        return True
    return bool(re.search(r"llms\.txt", html, re.I))


_DETECT = {"schema": _has_schema, "answer_first": _has_answer_first, "headings": _has_headings,
           "freshness": _has_freshness, "entity": _has_entity, "llms_txt": _has_llms}


def check(html, url=None, meta=None):
    """The honest report. html = the page source; meta may carry {this_year, llms_txt_found}
    (the CLI fills llms_txt_found by fetching /llms.txt). Returns a dict — never a bare grade."""
    html = html or ""
    meta = dict(meta or {})
    meta.setdefault("this_year", 2026)
    signals, earned = [], 0
    for s in SIGNALS:
        present = bool(_DETECT[s["id"]](html, meta))
        if present:
            earned += s["weight"]
        signals.append({"id": s["id"], "label": s["label"], "weight": s["weight"],
                        "present": present, "why": s["why"]})
    score = round(100 * earned / _MAXW)
    band = "Strong signals" if score >= 75 else "Developing signals" if score >= 45 else "Weak signals"
    fixes = [s["label"] for s in signals if not s["present"]]
    return {"url": url, "score": score, "band": band, "signals": signals,
            "top_fixes": fixes[:3], "framing": FRAMING, "methodology_url": METHODOLOGY_URL}


# ------------------------------------------------------------------------------------ fixtures + test
_GOOD = """<!doctype html><html><head>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization",
"name":"Acme","sameAs":["https://linkedin.com/company/acme","https://github.com/acme"],
"dateModified":"2026-06-01"}</script></head><body>
<h1>Best CI/CD platform for a Series A startup</h1>
<p>The short answer: for most Series A teams the best CI/CD platform is the one that fits your
stack and budget — here is how the leaders compare and when each wins.</p>
<h2>What should you look for?</h2><ul><li>Speed</li><li>Cost</li><li>Integrations</li></ul>
<h2>How the leaders compare</h2><table><tr><td>A</td><td>B</td></tr></table>
<p><a href="/llms.txt">llms.txt</a></p></body></html>"""

_HOLLOW = """<!doctype html><html><head><title>Acme</title></head><body>
<div>Welcome to Acme. We are a company. Contact us.</div>
<img src="hero.png"></body></html>"""

# ---------------------------------------------------------------------------------------------------
# END engine block. Everything below is the CLI wrapper (fetching, formatting) — non-parity.
# ---------------------------------------------------------------------------------------------------

_UA = "citation-ready/1.0 (+https://clearcited.com; stdlib urllib)"
_BRIDGE = "Measure the real thing: https://clearcited.com/free-teardown/"


def _fetch(url, timeout=10):
    """Fetch a page with a real User-Agent. Raises on any network/HTTP error (honest, no fabrication)."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    charset = "utf-8"
    ctype = ""
    try:
        ctype = r.headers.get("Content-Type", "") or ""
    except Exception:
        ctype = ""
    m = re.search(r"charset=([\w\-]+)", ctype, re.I)
    if m:
        charset = m.group(1)
    return raw.decode(charset, errors="replace")


def _fetch_llms_txt(url, timeout=10):
    """Try {scheme}://{host}/llms.txt — True iff it returns HTTP 200. Never raises."""
    try:
        parts = urllib.parse.urlsplit(url)
        if not parts.scheme or not parts.netloc:
            return False
        llms_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, "/llms.txt", "", ""))
        req = urllib.request.Request(llms_url, headers={"User-Agent": _UA}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return getattr(r, "status", r.getcode()) == 200
    except Exception:
        return False


def _print_report(rep, mock=False):
    print("%s — %d/100" % (rep["band"], rep["score"]))
    if rep.get("url"):
        print(rep["url"])
    print("")
    for s in rep["signals"]:
        mark = "✓" if s["present"] else "✗"
        print("  %s  %s" % (mark, s["label"]))
        if not s["present"]:
            print("        why it matters: %s" % s["why"])
    print("")
    print(rep["framing"])
    if mock:
        print("(This is the built-in demo page — pass --url or --file to check a real page.)")
    print(_BRIDGE)


def _selftest():
    print("=" * 70); print("citation-ready check - SELF-TEST"); print("=" * 70)
    P = F = 0

    def ck(name, cond):
        nonlocal P, F
        print(("  PASS  " if cond else "  FAIL  ") + name)
        P, F = (P + 1, F) if cond else (P, F + 1)

    g = check(_GOOD, url="https://acme.dev/")
    h = check(_HOLLOW, url="https://acme.dev/")
    ck("a well-structured page scores high (Strong)", g["score"] >= 75 and g["band"] == "Strong signals")
    ck("a hollow page scores low (Weak)", h["score"] < 45 and h["band"] == "Weak signals")
    ck("every report carries the observed-correlation framing (not a guarantee)",
       "observed correlations" in g["framing"] and "not guarantees" in g["framing"]
       and "not guarantees" in h["framing"])
    ck("the report is a structured signal set, never a naked grade",
       len(g["signals"]) == len(SIGNALS) and all("why" in s for s in g["signals"]))
    ck("hollow page surfaces top fixes to close", len(h["top_fixes"]) >= 3)
    ck("methodology link rides the report", g["methodology_url"] == METHODOLOGY_URL)
    print("=" * 70); print("SELF-TEST", "PASSED" if F == 0 else "FAILED (%d)" % F)
    return 0 if F == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Is your page structured the way AI engines cite? An honest heuristic self-check.")
    ap.add_argument("--url", help="fetch and check a live URL (also looks for /llms.txt)")
    ap.add_argument("--file", help="check a local HTML file")
    ap.add_argument("--mock", action="store_true", help="offline demo using a built-in page (default)")
    ap.add_argument("--json", action="store_true", help="machine-readable full report")
    ap.add_argument("--selftest", action="store_true", help="run the offline self-test and exit")
    a = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if a.selftest:
        return _selftest()

    meta = {}
    if a.url:
        try:
            html = _fetch(a.url)
        except urllib.error.HTTPError as e:
            sys.exit("Could not fetch %s — HTTP %s %s" % (a.url, e.code, e.reason))
        except urllib.error.URLError as e:
            sys.exit("Could not fetch %s — network error: %s" % (a.url, e.reason))
        except Exception as e:
            sys.exit("Could not fetch %s — %s" % (a.url, e))
        meta["llms_txt_found"] = _fetch_llms_txt(a.url)
        rep = check(html, url=a.url, meta=meta)
        mock = False
    elif a.file:
        try:
            html = open(a.file, encoding="utf-8", errors="replace").read()
        except OSError as e:
            sys.exit("Could not read %s — %s" % (a.file, e))
        rep = check(html, url=a.file, meta=meta)
        mock = False
    else:
        # default: offline demo, exactly like aeo-audit-lite defaults to mock
        rep = check(_GOOD, url="(built-in demo page)", meta=meta)
        mock = True

    if a.json:
        print(json.dumps(rep, indent=2))
    else:
        _print_report(rep, mock=mock)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
