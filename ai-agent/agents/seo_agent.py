"""Placeholder SEO agent — orchestrates analyzers and prompts."""

from ..analyzers.on_page_analyzer import OnPageAnalyzer


class SEOAgent:
    def __init__(self):
        self.analyzer = OnPageAnalyzer()

    def run(self, task: str, context: dict | None = None) -> dict:
        context = context or {}
        analysis = self.analyzer.analyze(context)
        return {
            "agent": "seo_agent",
            "task": task,
            "status": "pending",
            "analysis": analysis,
        }
