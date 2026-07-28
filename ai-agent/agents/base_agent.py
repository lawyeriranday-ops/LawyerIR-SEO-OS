"""Base agent interface."""

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    @abstractmethod
    def run(self, task: str, context: dict | None = None) -> dict:
        pass
