# citation-ready

**Does AI cite you — and is your page even built to be cited?** Check a page for
the structural signals our AI Visibility Index *observes* on content that AI
engines (ChatGPT, Perplexity, Claude, Gemini, Google AI) tend to quote and
recommend.

These are **observed correlations, not guarantees.** A high score means your page
looks like the pages that get cited — it does not promise a citation. The only way
to know whether AI actually cites you is to measure it (see below).

- **Zero dependencies** — Python standard library only.
- **Mock mode by default** — runs offline against a built-in demo page.
- **Honest framing** — every report says these are correlations from measurement,
  not a ranking guarantee.

## Usage

Offline demo (no network needed):

```bash
python citation_ready.py --mock
```

Check a live URL (also looks for `/llms.txt`):

```bash
python citation_ready.py --url https://example.com
```

Check a local HTML file:

```bash
python citation_ready.py --file page.html
```

Machine-readable output:

```bash
python citation_ready.py --url https://example.com --json
```

### Example output

```
Strong signals — 100/100
(built-in demo page)

  ✓  Valid schema (JSON-LD) for AI parsing
  ✓  Answer-first structure (direct summary + lists/tables)
  ✓  Clear heading outline (one H1, descriptive H2s)
  ✓  Freshness signal (dateModified or a recent visible date)
  ✓  Consistent entity (Organization + sameAs / profiles)
  ✓  llms.txt present / referenced

These are observed correlations from our AI Visibility Index measurement — signals
that tend to accompany pages AI engines cite. They are not guarantees; the measured
answer for your domain comes from a teardown.
Measure the real thing: https://clearcited.com/free-teardown/
```

## What it checks

Six structural signals, each with the honest reason it correlates with getting cited:

| Signal | Why it correlates |
|---|---|
| **Valid schema (JSON-LD)** | Structured data lets engines extract entities and claims cleanly. |
| **Answer-first structure** | Engines quote pages that state the answer early and in extractable chunks. |
| **Clear heading outline** | A clean outline maps to the sub-questions engines answer. |
| **Freshness signal** | Engines favour pages that show they are current. |
| **Consistent entity** | A stable, cross-linked entity is easier to attribute and trust. |
| **llms.txt** | An llms.txt gives agents a curated map of your canonical content. |

The score is a weighted sum of the signals present, banded into *Strong* /
*Developing* / *Weak*. Detection is plain regex over the HTML — no headless
browser, no JavaScript execution.

## How this connects to real measurement

This CLI is a **heuristic**. It reads your page and predicts, from structure alone,
whether it looks like content AI engines cite. It never sends a prompt to an engine,
so it cannot tell you whether you are *actually* cited today.

The measured answer is a **teardown**: we run real buyer prompts across every major
engine, several runs each, and report where you show up versus competitors — with a
confidence interval, the same way every time. The signals this tool checks are drawn
from what our **AI Visibility Index** observes on pages that earn those citations.

- **How we measure:** <https://clearcited.com/methodology/>
- **Get the measured answer for your domain:** <https://clearcited.com/free-teardown/>

Honest distinction: `citation-ready` is instant-but-predictive (structure only,
offline); the teardown is measured-but-async (real prompts, every engine, human QC).

## License

MIT © Clear Cited

---

This is a free, lite tool. The full **[Clear Cited](https://clearcited.com)**
service measures citations across every major engine (ChatGPT, Perplexity, Claude,
Gemini, Google AI Overviews), with human QC and a fix roadmap.
[Get a free teardown →](https://clearcited.com/free-teardown/)
