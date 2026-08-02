# Changelog

All notable changes to this project are documented here.
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html), and
the format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Every release is archived on Zenodo. The **concept DOI**
[10.5281/zenodo.21757510](https://doi.org/10.5281/zenodo.21757510) always resolves to the latest
version; each release below also has its own version DOI.

## [0.1.0] - 2026-08-02

First public release.

### Added

- `citation_ready.py` — checks a page for six structural signals observed on
  content AI answer engines tend to cite: JSON-LD schema, answer-first structure,
  heading outline, freshness, entity consistency, and `llms.txt`.
- `--mock`, `--url`, `--file` and `--json` modes. Mock mode is the default and
  runs offline against a built-in demo page.
- `CITATION.cff` and `.zenodo.json`, so the repository is citable and archives
  automatically on release.

### Notes

- Version DOI: [10.5281/zenodo.21757511](https://doi.org/10.5281/zenodo.21757511)
- Published to PyPI as [`citation-ready`](https://pypi.org/project/citation-ready/) via Trusted Publishing, with provenance attestations.
- Mirrored to [Codeberg](https://codeberg.org/clear-cited/citation-ready), tags included.

[0.1.0]: https://github.com/Clear-Cited/citation-ready/releases/tag/v0.1.0
