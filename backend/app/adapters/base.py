from abc import ABC, abstractmethod
from typing import Iterable, Tuple

from app.adapters.types import DiscoveredThread, ParsedDealPost, ParsedDealItem


class SourceAdapter(ABC):
    """Base class for forum source adapters."""

    def __init__(self, base_url: str, user_agent: str):
        self.base_url = base_url
        self.user_agent = user_agent

    @abstractmethod
    def discover(self) -> Iterable[DiscoveredThread]:
        """
        Discover new threads/posts from the source.
        
        Returns:
            Iterator of DiscoveredThread objects
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_thread_html(self, url: str) -> str:
        """
        Fetch the raw HTML content of a thread.
        
        Args:
            url: Thread URL
            
        Returns:
            Raw HTML content
        """
        raise NotImplementedError

    @abstractmethod
    def parse_thread(
        self, html: str, url: str, category: str
    ) -> Tuple[ParsedDealPost, list[ParsedDealItem]]:
        """
        Parse a thread HTML into structured data.
        
        Args:
            html: Raw HTML content
            url: Thread URL
            category: Deal category
            
        Returns:
            Tuple of (ParsedDealPost, list of ParsedDealItem)
        """
        raise NotImplementedError
