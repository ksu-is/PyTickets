# -*- coding: utf-8 -*-
"""
Refactored Tickets Spider using modular architecture.

This spider discovers ticket links, filters and deduplicates them, sends
manual-purchase links via configured notifications, and then stops.
"""

import json
import os
import random
import time

import scrapy
from scrapy.exceptions import CloseSpider
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from ticketCrawler.adapters.factory import AdapterFactory
from ticketCrawler.auth.factory import AuthenticatorFactory
from ticketCrawler.config.app_config import config
from ticketCrawler.config.config_loader import ConfigLoader
from ticketCrawler.database import Database
from ticketCrawler.filters.factory import FilterFactory
from ticketCrawler.notifications.manager import NotificationFactory, NotificationManager
from ticketCrawler.proxies import ProxyManager
from ticketCrawler.utils.error_handler import ErrorHandler
from ticketCrawler.utils.helpers import TextHelper
from ticketCrawler.utils.logger import LoggerFactory
from ticketCrawler.utils.url_cache import URLCache


class RefactoredTicketsSpider(scrapy.Spider):
    """Multi-site spider for manual ticket link notifications."""

    name = "tickets_refactored"

    custom_settings = {
        "DOWNLOAD_DELAY": 0.25,
        "HTTPERROR_ALLOWED_CODES": [401, 403, 429]
    }

    def __init__(self, site='dutch_tickets', url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        LoggerFactory.setup()
        self.app_logger = LoggerFactory.get_logger(__name__)
        self.app_logger.info(f"Initializing spider for site: {site}")

        self.site_name = site
        self.config_loader = ConfigLoader()
        self.site_config = self.config_loader.get_config(site)
        self.base_url = self.site_config.get('base_url')

        self.adapter = AdapterFactory.create_adapter(site, self.site_config)

        auth_config = self.site_config.get('auth', {})
        auth_type = auth_config.get('type', 'none')
        self.authenticator = (
            AuthenticatorFactory.create_authenticator(auth_type, auth_config)
            if auth_type != 'none'
            else None
        )

        self.notification_manager = self._setup_notifications()
        self.ticket_filter = self._setup_filters()
        self.notify_mode = config.notify_mode
        self.debug_dir = config.debug_dir

        self.url_cache = URLCache(
            cache_path=config.url_cache_path,
            ttl_days=int(os.environ.get('PYTICKETS_URL_CACHE_TTL_DAYS', '30'))
        )
        self.database = Database(config.database_path)
        self.crawl_run_id = self.database.start_crawl_run(site)
        self.tickets_found = 0
        self.tickets_notified = 0
        self.errors = []

        self.proxy_manager = ProxyManager.from_env()
        self.browser = self._create_browser()
        self.browser.get(self.base_url)

        if self.authenticator:
            self._authenticate()

        self.start_urls = [self._normalize_start_url(url)] if url else []
        self.first_sold_ticket_url = None
        self.successful = False
        self.iteration = 0

    def _setup_notifications(self):
        """Setup notification manager from env configuration."""
        manager = NotificationManager()

        notifications_config = os.environ.get('NOTIFICATIONS_CONFIG')
        if notifications_config:
            try:
                parsed_config = json.loads(notifications_config)
                configs = parsed_config if isinstance(parsed_config, list) else [parsed_config]
                for notifier_config in configs:
                    notifier_type = notifier_config.pop('type')
                    manager.add_notifier_config(notifier_type, notifier_config)
            except Exception as e:
                self.app_logger.warning(f"Could not load NOTIFICATIONS_CONFIG: {str(e)}")

        email_sender = os.environ.get('EMAIL_SENDER') or os.environ.get('email_sender')
        email_recipient = os.environ.get('EMAIL_RECIPIENT') or os.environ.get('email_recipient')
        if email_sender and email_recipient:
            email_config = {
                'provider': os.environ.get('EMAIL_PROVIDER', os.environ.get('email_provider', 'smtp')),
                'sender': email_sender,
                'recipient': email_recipient,
                'smtp_host': os.environ.get('SMTP_HOST') or os.environ.get('smtp_host'),
                'smtp_port': int(os.environ.get('SMTP_PORT', os.environ.get('smtp_port', '587'))),
                'smtp_user': os.environ.get('SMTP_USER') or os.environ.get('smtp_user') or email_sender,
                'smtp_password': os.environ.get('SMTP_PASSWORD') or os.environ.get('smtp_password'),
                'mailgun_key': os.environ.get('MAILGUN_KEY') or os.environ.get('mailgun_key'),
                'mailgun_domain': os.environ.get('MAILGUN_DOMAIN') or os.environ.get('mailgun_domain'),
            }
            try:
                manager.add_notifier_config('email', email_config)
            except Exception as e:
                self.app_logger.warning(f"Email notifications are not configured correctly: {str(e)}")

        token = os.environ.get('telegram_token')
        chat_id = os.environ.get('telegram_chat_id')
        if token and chat_id:
            telegram_notifier = NotificationFactory.create_notifier(
                'telegram',
                {'token': token, 'chat_id': chat_id}
            )
            manager.add_notifier(telegram_notifier)

        return manager

    def _create_browser(self):
        """Create Selenium browser, applying a configured proxy if present."""
        options = Options()
        proxy = self.proxy_manager.get_next_proxy()
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
        return webdriver.Chrome(options=options)

    def _setup_filters(self):
        """Setup ticket filters from environment variables."""
        filters_config = []

        min_price = os.environ.get('min_price')
        max_price = os.environ.get('max_price')
        if min_price or max_price:
            filters_config.append({
                'type': 'price',
                'min_price': float(min_price) if min_price else None,
                'max_price': float(max_price) if max_price else None
            })

        seat_types = os.environ.get('seat_types')
        if seat_types:
            filters_config.append({
                'type': 'seat_type',
                'seat_types': seat_types.split(',')
            })

        if filters_config:
            return FilterFactory.create_combined_filter(filters_config, require_all=True)

        return None

    def _authenticate(self):
        """Authenticate with the website."""
        try:
            self.app_logger.info(f"Authenticating with {self.site_config['auth']['type']}")
            self.authenticator.authenticate(self.browser)

            if self.authenticator.is_authenticated(self.browser):
                self.app_logger.info("Authentication successful")
            else:
                self.app_logger.warning("Authentication may have failed - check browser")

        except Exception as e:
            self.app_logger.error(f"Authentication failed: {str(e)}")
            self._record_error(e)
            raise

    async def start(self):
        """Generate initial requests."""
        if not self.start_urls:
            self.app_logger.warning("No URLs provided. Use: scrapy crawl tickets_refactored -a url=<url>")
            return

        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.visit_first_sold_ticket,
                dont_filter=True
            )

    def _normalize_start_url(self, url):
        """Let adapters rewrite public URLs to official API URLs when configured."""
        normalizer = getattr(self.adapter, "normalize_start_url", None)
        if not normalizer:
            return url
        normalized = normalizer(url)
        if normalized != url:
            self.app_logger.info(f"Normalized start URL for {self.site_name}: {normalized}")
        return normalized

    def visit_first_sold_ticket(self, response):
        """Find and visit the first sold ticket listing."""
        try:
            self.app_logger.info("Looking for first sold ticket listing")
            self.first_sold_ticket_url = self.adapter.get_first_sold_ticket_url(response)

            if self.first_sold_ticket_url:
                self.app_logger.info(f"Opening: {self.first_sold_ticket_url}")
                yield scrapy.Request(
                    url=self.first_sold_ticket_url,
                    callback=self.parse,
                    dont_filter=True
                )
            else:
                self.app_logger.error("Could not find first sold ticket URL")
                self._save_debug_html(response.body, 'no_sold_tickets.html')

        except Exception as e:
            self.app_logger.error(f"Error in visit_first_sold_ticket: {str(e)}")
            self._record_error(e)
            self._save_debug_html(response.body, 'error_visit_sold.html')

    def parse(self, response):
        """Parse ticket listing page and send matching manual purchase links."""
        self.iteration += 1
        self.app_logger.info(f"Parse iteration #{self.iteration}")

        try:
            if not self.adapter.check_tickets_available(response):
                self.app_logger.info("No tickets available, sleeping before retry")

                rate_limits = self.adapter.get_rate_limits()
                sleep_duration = random.uniform(rate_limits['min_delay'], rate_limits['max_delay'])
                time.sleep(sleep_duration)

                yield scrapy.Request(
                    url=self.first_sold_ticket_url,
                    callback=self.parse,
                    dont_filter=True
                )
                return

            if self.adapter.is_rate_limited(response):
                self.app_logger.warning("Rate limited! Notifying and pausing")
                self.notification_manager.notify("Rate limited. Waiting for manual reset.")
                self._record_error("rate limit or access block detected")
                raise CloseSpider("rate_limited")

            tickets = self.adapter.extract_tickets(response)
            self.app_logger.info(f"Found {len(tickets)} ticket(s)")
            self.tickets_found += len(tickets)
            pending_notifications = []

            for ticket in tickets:
                try:
                    ticket_url = self.adapter.get_ticket_url(ticket)
                    if not ticket_url:
                        continue

                    ticket_data = self._build_ticket_data(ticket, ticket_url)

                    if self.ticket_filter and not self.ticket_filter.matches(ticket_data):
                        self.app_logger.info(f"Ticket filtered out: {ticket_url}")
                        continue

                    if self._is_duplicate_ticket(ticket_url):
                        self.app_logger.info(f"Skipping duplicate ticket: {ticket_url}")
                        continue

                    self.database.save_ticket(ticket_data)
                    pending_notifications.append(ticket_data)

                    if self.notify_mode != "batch":
                        self._send_ticket_notifications(pending_notifications)
                        raise CloseSpider("ticket_links_sent")

                except CloseSpider:
                    raise
                except Exception as e:
                    self.app_logger.error(f"Error processing ticket: {str(e)}")
                    self._record_error(e)
                    continue

            if pending_notifications and self.notify_mode == "batch":
                self._send_ticket_notifications(pending_notifications)
                raise CloseSpider("ticket_links_sent")

        except CloseSpider:
            raise
        except Exception as e:
            self.app_logger.error(f"Error in parse: {str(e)}")
            self._record_error(e)
            self._save_debug_html(response.body, 'error_parse.html')

    def _build_ticket_data(self, ticket, ticket_url):
        """Create normalized ticket metadata from a selector."""
        if isinstance(ticket, dict):
            metadata = ticket.get("metadata", {}).copy()
            metadata.setdefault("site_base_url", self.base_url)
            return {
                "url": ticket_url,
                "site": self.site_config.get("name", "Unknown"),
                "price": ticket.get("price"),
                "seat_type": ticket.get("seat_type") or ticket.get("title"),
                "date": ticket.get("date"),
                "quantity": ticket.get("quantity"),
                "metadata": metadata,
            }

        text_values = ticket.xpath('.//text()').extract() if hasattr(ticket, 'xpath') else []
        clean_text = TextHelper.clean_text(' '.join(text_values))
        return {
            'url': ticket_url,
            'site': self.site_config.get('name', 'Unknown'),
            'price': TextHelper.extract_price(clean_text),
            'seat_type': clean_text,
            'date': None,
            'quantity': None,
            'metadata': {
                'source_text': clean_text,
                'site_base_url': self.base_url,
            }
        }

    def _send_ticket_notifications(self, tickets):
        """Send one or more ticket links and mark sent links as visited."""
        if len(tickets) == 1:
            results = self.notification_manager.notify_ticket_found(
                tickets[0],
                subject="PyTickets: Ticket link found"
            )
        else:
            message = self._format_batch_message(tickets)
            results = self.notification_manager.notify(
                message,
                subject=f"PyTickets: {len(tickets)} ticket links found",
                html=self._format_batch_html(tickets),
            )

        notification_sent = any(results.values()) if results else False

        for ticket_data in tickets:
            ticket_url = ticket_data["url"]
            status = "sent" if notification_sent else "not_configured"
            self.database.mark_ticket_notified(ticket_url, status=status)

            if notification_sent:
                self.tickets_notified += 1
                self.database.mark_url_visited(ticket_url, ticket_data)
                self.url_cache.mark_visited(ticket_url, ticket_data)
            else:
                self.app_logger.warning(f"Ticket link was not sent; leaving URL retryable: {ticket_url}")

        if notification_sent:
            self.successful = True
            self.url_cache.save_to_disk()

    @staticmethod
    def _format_batch_message(tickets):
        lines = ["Ticket links found:", ""]
        for index, ticket in enumerate(tickets, start=1):
            lines.extend([
                f"{index}. {ticket.get('url')}",
                f"   Price: {ticket.get('price', 'N/A')}",
                f"   Seat: {ticket.get('seat_type', 'N/A')}",
                "",
            ])
        return "\n".join(lines)

    @staticmethod
    def _format_batch_html(tickets):
        rows = []
        for ticket in tickets:
            rows.append(
                "<tr>"
                f"<td><a href=\"{ticket.get('url')}\">Open Ticket</a></td>"
                f"<td>{ticket.get('price', 'N/A')}</td>"
                f"<td>{ticket.get('seat_type', 'N/A')}</td>"
                "</tr>"
            )
        return (
            "<html><body><h2>Ticket links found</h2>"
            "<table border=\"1\" cellpadding=\"8\">"
            "<tr><th>Link</th><th>Price</th><th>Seat</th></tr>"
            f"{''.join(rows)}</table></body></html>"
        )

    def _is_duplicate_ticket(self, ticket_url):
        """Check both JSON cache and SQLite history for a duplicate URL."""
        return (
            self.url_cache.is_visited(ticket_url) or
            self.database.is_url_visited(ticket_url)
        )

    def _record_error(self, error):
        """Store a compact classified error for crawl-run history."""
        self.errors.append({
            'type': ErrorHandler.classify_error(error).value,
            'message': str(error),
            'retryable': ErrorHandler.is_retryable(error),
            'suggestion': ErrorHandler.suggest_action(error),
        })

    def _save_debug_html(self, html_body, filename='debug.html'):
        """Save HTML for debugging."""
        try:
            os.makedirs(self.debug_dir, exist_ok=True)
            path = os.path.join(self.debug_dir, filename)
            with open(path, 'wb') as f:
                f.write(html_body)
            self.app_logger.info(f"Saved debug HTML: {path}")
        except Exception as e:
            self.app_logger.warning(f"Could not save debug HTML: {str(e)}")

    def closed(self, reason):
        """Clean up when spider closes."""
        self.url_cache.save_to_disk()

        status = "completed" if reason in ("finished", "ticket_links_sent") else "failed"
        self.database.finish_crawl_run(
            self.crawl_run_id,
            status=status,
            tickets_found=self.tickets_found,
            tickets_notified=self.tickets_notified,
            errors=self.errors
        )

        if self.browser:
            self.browser.quit()

        summary = "Ticket links sent" if self.successful else "No new tickets notified"
        self.app_logger.info(f"Spider closed. Status: {summary}. Reason: {reason}")
