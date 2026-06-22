

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Abstract base class for all QTrustCode agents.

    Every agent in the autonomous multi-agent framework must:
    1. Accept some form of input for analysis.
    2. Produce a structured dictionary output.
    3. Expose a confidence score that can later be consumed by
       the verification and quantum feature construction pipelines.
    """

    @abstractmethod
    def analyze(self, *args, **kwargs) -> dict:
        """
        Execute the agent's reasoning process and return a
        structured result dictionary.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement analyze()."
        )