# US Women Shoes Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a daily multi-platform US women's shoes monitor that scores independent Amazon, TikTok, and Temu records and generates a Chinese report.

**Architecture:** Playwright collectors emit a shared row schema. Pure analyzer and report modules transform those rows, while `main.py` handles persistence and orchestration. GitHub Actions installs Chromium, runs the monitor at UTC 01:00, and commits generated artifacts.

**Tech Stack:** Python 3.11, Playwright, Pandas, pytest, GitHub Actions

---

### Task 1: Define analysis behavior

**Files:**
- Create: `tests/test_analyzer.py`
- Create: `analyzer.py`

- [ ] Write failing tests for number parsing, trend words, and platform-specific scores.
- [ ] Run `pytest tests/test_analyzer.py -v` and confirm missing-module failure.
- [ ] Implement normalization and scoring functions.
- [ ] Run `pytest tests/test_analyzer.py -v` and confirm all tests pass.

### Task 2: Define report and persistence behavior

**Files:**
- Create: `tests/test_report.py`
- Create: `tests/test_main.py`
- Create: `report.py`
- Create: `main.py`

- [ ] Write failing tests for required Chinese sections and CSV deduplication.
- [ ] Run focused tests and confirm failure.
- [ ] Implement report generation and history merging.
- [ ] Run focused tests and confirm all pass.

### Task 3: Implement platform collectors

**Files:**
- Create: `tests/test_scraper.py`
- Create: `scraper.py`

- [ ] Write failing tests for Amazon, TikTok, and Temu static HTML extraction.
- [ ] Run `pytest tests/test_scraper.py -v` and confirm failure.
- [ ] Implement resilient Playwright collection and HTML extractors.
- [ ] Run scraper tests and confirm all pass.

### Task 4: Add automation and documentation

**Files:**
- Create: `requirements.txt`
- Create: `.github/workflows/daily.yml`
- Create: `.gitignore`
- Create: `README.md`

- [ ] Add pinned-compatible dependencies and UTC 01:00 workflow.
- [ ] Document local setup, environment variables, outputs, limitations, and GitHub permissions.

### Task 5: Verify the complete project

- [ ] Run `python -m compileall .`.
- [ ] Run `pytest -v`.
- [ ] Inspect workflow schedule, output paths, and required report headings.

