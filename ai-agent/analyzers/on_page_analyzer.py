"""Placeholder on-page SEO analyzer."""

from .base_analyzer import BaseAnalyzer


class OnPageAnalyzer(BaseAnalyzer):
    def analyze(self, data: dict) -> dict:
        return {
            "analyzer": "on_page",
            "status": "pending",
            "input_keys": list(data.keys()),
            "findings": [],
        }
