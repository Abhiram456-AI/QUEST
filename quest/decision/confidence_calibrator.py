import json
from typing import Dict, List

class ConfidenceCalibrator:
    """
    Calibrates decision and assistant response confidence scores based on multi-signal inputs.
    Delegates to the single authoritative FinalDecisionResolver to ensure mathematical unity.
    """

    def __init__(self):
        pass

    def calibrate(self, context: Dict) -> float:
        """
        Computes unified calibrated confidence score from FinalDecisionResolver.
        """
        from quest.decision.final_decision_resolver import FinalDecisionResolver
        resolver = FinalDecisionResolver()
        res = resolver.resolve(context, "")
        return res["resolved_confidence"]
