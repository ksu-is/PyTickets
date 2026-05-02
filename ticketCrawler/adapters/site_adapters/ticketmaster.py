# -*- coding: utf-8 -*-
"""Adapter for Ticketmaster event/search pages."""
import json
import re
from urllib.parse import urlencode, urlparse

from ..base_adapter import BaseAdapter


class TicketmasterAdapter(BaseAdapter):
    """Discover Ticketmaster ticket links for manual purchase."""

    def __init__(self, config):
        super().__init__(config)
        self.selectors = config.get("selectors", {})
        self.api_config = config.get("api", {})

    def normalize_start_url(self, url):
        """Use the official Discovery API when an API key and event ID are available."""
        api_key = self.api_config.get("apikey")
        event_id = self._extract_event_id(url)
        if not api_key or not event_id:
            return url

        endpoint = self.api_config.get(
            "event_endpoint",
            "https://app.ticketmaster.com/discovery/v2/events/{event_id}.json",
        )
        return endpoint.format(event_id=event_id) + "?" + urlencode({"apikey": api_key})

    def authenticate(self, browser):
        """Ticketmaster discovery runs without login by default."""
        return True

    def check_tickets_available(self, response):
        body = self._body_text(response).lower()
        no_ticket_text = self.selectors.get("no_tickets_text", [])
        return not any(text.lower() in body for text in no_ticket_text)

    def get_first_sold_ticket_url(self, response):
        """Ticketmaster event/search URLs can be parsed directly."""
        return response.url

    def extract_tickets(self, response):
        tickets = []
        tickets.extend(self._extract_api_events(response))
        tickets.extend(self._extract_json_ld_offers(response))
        tickets.extend(self._extract_anchor_links(response))
        return self._dedupe(tickets)

    def get_ticket_url(self, ticket_element):
        if isinstance(ticket_element, dict):
            return ticket_element.get("url")
        link_xpath = self.selectors.get("ticket_link_xpath", "./@href")
        link = ticket_element.xpath(link_xpath).extract_first()
        return ticket_element.response.urljoin(link) if link else None

    def check_ticket_available(self, browser):
        body = browser.page_source.lower()
        no_ticket_text = self.selectors.get("no_tickets_text", [])
        return not any(text.lower() in body for text in no_ticket_text)

    def buy_ticket(self, browser):
        """Disabled: PyTickets sends links for manual purchase only."""
        return False

    def check_reservation_success(self, browser):
        return False

    def is_rate_limited(self, response):
        body = self._body_text(response).lower()
        rate_limit_text = self.selectors.get("rate_limit_text", [])
        return any(text.lower() in body for text in rate_limit_text)

    def _extract_anchor_links(self, response):
        xpath = self.selectors.get(
            "ticket_array_xpath",
            "//a[contains(@href, '/event/') or contains(@href, 'ticketmaster.com/event')]",
        )
        tickets = []
        try:
            anchors = response.xpath(xpath)
        except ValueError:
            return tickets
        for anchor in anchors:
            href = anchor.xpath("./@href").extract_first()
            if not href:
                continue
            text = " ".join(anchor.xpath(".//text()").extract())
            tickets.append({
                "url": response.urljoin(href),
                "seat_type": text.strip(),
                "metadata": {"source": "anchor"},
            })
        return tickets

    def _extract_api_events(self, response):
        try:
            data = json.loads(self._body_text(response))
        except json.JSONDecodeError:
            return []

        events = data.get("_embedded", {}).get("events", [])
        if not events and data.get("url"):
            events = [data]
        tickets = []
        for event in events:
            url = event.get("url")
            if not url:
                continue
            price_ranges = event.get("priceRanges") or []
            price = price_ranges[0].get("min") if price_ranges else None
            start = event.get("dates", {}).get("start", {})
            tickets.append({
                "url": url,
                "price": price,
                "seat_type": event.get("name"),
                "date": start.get("dateTime") or start.get("localDate"),
                "metadata": {"source": "ticketmaster_discovery_api"},
            })
        return tickets

    def _extract_json_ld_offers(self, response):
        tickets = []
        try:
            scripts = response.xpath("//script[@type='application/ld+json']/text()").extract()
        except ValueError:
            return tickets
        for script in scripts:
            try:
                data = json.loads(script)
            except json.JSONDecodeError:
                continue
            for item in self._walk_json(data):
                if not isinstance(item, dict):
                    continue
                offers = item.get("offers")
                if not offers:
                    continue
                for offer in offers if isinstance(offers, list) else [offers]:
                    url = offer.get("url") if isinstance(offer, dict) else None
                    if not url:
                        continue
                    tickets.append({
                        "url": response.urljoin(url),
                        "price": offer.get("price"),
                        "seat_type": item.get("name"),
                        "date": item.get("startDate"),
                        "metadata": {"source": "json_ld"},
                    })
        return tickets

    @staticmethod
    def _extract_event_id(url):
        parsed = urlparse(url)
        match = re.search(r"/event/([^/?#]+)", parsed.path)
        return match.group(1) if match else None

    @staticmethod
    def _walk_json(value):
        yield value
        if isinstance(value, dict):
            for child in value.values():
                yield from TicketmasterAdapter._walk_json(child)
        elif isinstance(value, list):
            for child in value:
                yield from TicketmasterAdapter._walk_json(child)

    @staticmethod
    def _dedupe(tickets):
        seen = set()
        deduped = []
        for ticket in tickets:
            url = ticket.get("url")
            if url and url not in seen:
                seen.add(url)
                deduped.append(ticket)
        return deduped

    @staticmethod
    def _body_text(response):
        body = response.text if hasattr(response, "text") else response
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="ignore")
        return str(body)
