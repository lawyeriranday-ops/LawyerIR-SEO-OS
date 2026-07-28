"""Base analyzer interface for SEO data."""

from abc import ABC, abstractmethod


class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, data: dict) -> dict:
        pass
