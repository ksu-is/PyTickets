# Live Crawl Findings and Browser-Backed Fetch Plan

## Current Commit State

Recent local commits:

- `7e177fd` Handle rate limits without interactive prompt
- `3bde805` Route Ticketmaster event crawls through Discovery API
- `cb6a5e6` Fix live Scrapy runtime startup
- `49f0e52` Add PyTickets PowerPoint presentation
- `3e6f2de` Add Ticketmaster and SeatGeek adapters
- `fd1af2f` Implement phase 2 operations platform
- `adfa492` Complete phase 1 manual notification workflow

## Live Crawl Results

### Ticketmaster Public Event Page

Command:

```powershell
python -m scrapy crawl tickets_refactored -a site=ticketmaster -a url="https://www.ticketmaster.com/j-cole-the-falloff-tour-charlotte-north-carolina-07-10-2026/event/2D0064529D46D781?landing=c"
```

Result:

- The spider starts and closes cleanly.
- Ticketmaster public page returned HTTP `401 Unauthorized`.
- No ticket links were extracted.
- No notifications were sent.

Fixes made:

- Replaced assignment to Scrapy's read-only `logger` property with `app_logger`.
- Changed config loading so only the selected site's environment variables are resolved.
- Added Ticketmaster Discovery API URL routing when `TICKETMASTER_API_KEY` is set.

### SeatGeek Public Listing Page

Command:

```powershell
python -m scrapy crawl tickets_refactored -a site=seatgeek -a url="https://seatgeek.com/j-cole-tickets/charlotte"
```

Result:

- The spider starts and closes cleanly.
- SeatGeek public page returned HTTP `403 Forbidden`.
- No ticket links were extracted.
- No notifications were sent.

Fix made:

- Removed the interactive `input()` pause for rate limits/blocks.
- The crawler now records the block and exits cleanly with `rate_limited`.

## Problem Summary

The crawler code runs, but major ticket platforms block raw Scrapy HTTP requests:

- Ticketmaster returned `401`.
- SeatGeek returned `403`.

This means the next reliability improvement is not more XPath parsing. The crawler needs a browser-backed fetch path so the page is loaded through Selenium first, then parsed from rendered browser HTML.

## Browser-Backed Fetch Plan

### Goal

Allow selected adapters to fetch public pages through Selenium/Chrome instead of raw Scrapy when a site blocks direct requests.

### Proposed Behavior

1. Spider receives the original event/search URL.
2. If the site config enables browser fetch, Selenium loads the page.
3. The spider waits for the page to render.
4. The spider captures `browser.page_source`.
5. The spider wraps that HTML in a Scrapy `HtmlResponse`.
6. Existing adapter parsing runs against that rendered HTML.
7. Existing dedupe, database, notification, and scheduler workflows remain unchanged.

### Config Addition

Add this to site configs that need it:

```json
{
  "fetch": {
    "mode": "browser",
    "wait_seconds": 5,
    "wait_for_css": "body"
  }
}
```

Supported modes:

- `scrapy`: current raw HTTP behavior
- `browser`: Selenium-backed fetch
- `api`: official API route when available

### Code Changes Needed

1. Add a fetch mode helper to `tickets_refactored.py`.
2. Add `_fetch_with_browser(url)` that returns an `HtmlResponse`.
3. Route browser-mode URLs directly into `parse()` without raw Scrapy download.
4. Preserve Ticketmaster API routing when `TICKETMASTER_API_KEY` is set.
5. Add tests with mocked browser page source.
6. Add config flags for Ticketmaster and SeatGeek browser fallback.

### Risks

- Ticketmaster and SeatGeek may still show CAPTCHA/challenge pages in Selenium.
- Selectors may need adjustment after seeing real rendered HTML.
- Selenium runs are slower and heavier than Scrapy requests.
- Proxies may be needed for repeated live crawling.

### Recommended Implementation Order

1. Add browser fetch mode and tests.
2. Enable browser fallback for SeatGeek first.
3. Test Ticketmaster with API key route.
4. If API key is unavailable or insufficient, enable browser fallback for Ticketmaster.
5. Add screenshot/debug HTML capture when browser fetch produces zero tickets.
