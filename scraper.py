"""
Single Expedia search session using Playwright.
One call to `search()` = one browser session = one result set.
"""

import random
import time
import logging
from typing import List, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PWTimeout
from config import cfg
from flight_parser import parse_flight_cards

logger = logging.getLogger(__name__)

EXPEDIA_BASE = "https://www.expedia.com"


def search(
    origin: str,
    destination: str,
    depart_date: str,
    trip_type: str = "round-trip",
    return_date: Optional[str] = None,
) -> List[dict]:
    """
    Launch a headless browser, run one Expedia flight search, return parsed flights.

    Args:
        origin:       IATA code e.g. "ORD"
        destination:  IATA code e.g. "JFK"
        depart_date:  "YYYY-MM-DD"
        trip_type:    "round-trip" or "one-way"
        return_date:  "YYYY-MM-DD" (required for round-trip)

    Returns:
        List of Flight dicts (may be empty if scrape fails).
    """
    with sync_playwright() as pw:
        # Initialize to None so finally block can safely check before closing.
        browser = None
        context = None
        try:
            browser = pw.chromium.launch(headless=cfg.headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
            page = context.new_page()
            _apply_stealth(context, page)

            url = _build_url(origin, destination, depart_date, trip_type, return_date)
            logger.info("Searching: %s → %s (%s) on %s", origin, destination, trip_type, depart_date)

            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            _random_pause()
            _dismiss_overlays(page)
            _wait_for_results(page)

            html = page.content()
            flights = parse_flight_cards(
                html,
                origin=origin,
                destination=destination,
                trip_type=trip_type,
                date=depart_date,
                return_date=return_date,
            )
            logger.info("Parsed %d flights for %s→%s", len(flights), origin, destination)
            return flights

        except PWTimeout:
            logger.warning("Timeout on %s→%s (%s)", origin, destination, trip_type)
            return []
        except Exception as exc:
            logger.error("Error on %s→%s: %s", origin, destination, exc, exc_info=True)
            return []
        finally:
            if context:
                context.close()
            if browser:
                browser.close()


def _build_url(origin: str, destination: str, depart_date: str,
               trip_type: str, return_date: Optional[str]) -> str:
    """
    Construct the Expedia deep-link URL for a flight search.

    Expedia URL format:
      /Flights-Search?trip=<roundtrip|oneway>
        &leg1=from:<origin>,to:<dest>,departure:<MMDDYYYY>TANYT
        &leg2=...  (round-trip only)
        &passengers=adults:1
        &mode=search
    """
    def fmt(d: str) -> str:
        # "YYYY-MM-DD" → "MMDDYYYY"
        y, m, day = d.split("-")
        return f"{m}{day}{y}"

    leg1 = f"from:{origin},to:{destination},departure:{fmt(depart_date)}TANYT"
    trip_param = "roundtrip" if trip_type == "round-trip" else "oneway"

    if trip_type == "round-trip" and return_date:
        leg2 = f"from:{destination},to:{origin},departure:{fmt(return_date)}TANYT"
        return (
            f"{EXPEDIA_BASE}/Flights-Search"
            f"?trip={trip_param}&leg1={leg1}&leg2={leg2}"
            f"&passengers=adults:1&mode=search&options=cabinclass:coach"
        )
    return (
        f"{EXPEDIA_BASE}/Flights-Search"
        f"?trip={trip_param}&leg1={leg1}"
        f"&passengers=adults:1&mode=search&options=cabinclass:coach"
    )


def _apply_stealth(context: BrowserContext, page: Page) -> None:
    """
    Apply stealth patches. playwright-stealth must be called on a Page;
    the init_script fallback is applied to the context so it runs on every page.
    """
    try:
        from playwright_stealth import stealth_sync
        stealth_sync(page)
        return
    except ImportError:
        pass

    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    """)


def _random_pause() -> None:
    """Sleep a random interval to mimic human pacing."""
    delay = random.uniform(cfg.min_delay_secs, cfg.max_delay_secs)
    time.sleep(delay)


def _dismiss_overlays(page: Page) -> None:
    """Close cookie banners or modal overlays if present."""
    selectors = [
        "button[data-testid='accept-button']",
        "button:has-text('Accept')",
        "button:has-text('No thanks')",
        "button[aria-label='Close']",
        "[data-testid='dialog-close']",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=1_500):
                btn.click()
                _random_pause()
                break
        except Exception:
            continue


def _wait_for_results(page: Page) -> None:
    """
    Wait for flight result cards to appear in the DOM.
    Expedia lazy-loads results via XHR — we wait for the list container.
    """
    result_selectors = [
        "[data-test-id='offer-listing']",
        "[data-testid='listings-container']",
        ".uitk-layout-grid",
        ".flight-module",
    ]
    for sel in result_selectors:
        try:
            page.wait_for_selector(sel, timeout=15_000)
            _random_pause()
            return
        except PWTimeout:
            continue
    time.sleep(4)
