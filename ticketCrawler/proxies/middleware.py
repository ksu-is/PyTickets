# -*- coding: utf-8 -*-
"""Scrapy downloader middleware for PyTickets proxy rotation."""
from .proxy_manager import ProxyManager


class ProxyRotationMiddleware:
    """Attach a rotating proxy to Scrapy requests when configured."""

    def __init__(self, manager=None):
        self.manager = manager or ProxyManager.from_env()

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider=None):
        proxy = self.manager.get_next_proxy()
        if proxy:
            request.meta["proxy"] = proxy
            request.meta["pytickets_proxy"] = proxy

    def process_response(self, request, response, spider=None):
        proxy = request.meta.get("pytickets_proxy")
        if proxy:
            if response.status in {403, 429, 500, 502, 503, 504}:
                self.manager.mark_failed(proxy)
            else:
                self.manager.mark_successful(proxy)
        return response

    def process_exception(self, request, exception, spider=None):
        proxy = request.meta.get("pytickets_proxy")
        if proxy:
            self.manager.mark_failed(proxy)
