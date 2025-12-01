"""Fuzzy matching utilities for auto-tagging"""
from rapidfuzz import fuzz, process
from typing import Dict, Tuple, List


class FuzzyMatcher:
    """Fuzzy string matching for auto-tagging"""

    def __init__(self, master_guide: Dict[str, str], confidence_threshold: float = 0.92):
        """
        Initialize with master guide dictionary

        Args:
            master_guide: Dict mapping patterns to tags
            confidence_threshold: Minimum confidence for auto-approval
        """
        self.master_guide = master_guide
        self.threshold = confidence_threshold

    def match(self, input_string: str) -> Tuple[str, float]:
        """
        Find best match for input string

        Returns:
            (matched_tag, confidence_score)
        """
        if not input_string:
            return "Unknown", 0.5

        input_clean = input_string.strip()

        # Exact match first
        if input_clean in self.master_guide:
            return self.master_guide[input_clean], 1.0

        # Exact substring match
        for pattern, tag in self.master_guide.items():
            if pattern.lower() in input_clean.lower():
                return tag, 1.0

        # Fuzzy match
        best_match, best_score, _ = process.extractOne(
            input_clean,
            self.master_guide.keys(),
            scorer=fuzz.partial_ratio
        )

        if best_match:
            confidence = best_score / 100
            if confidence > 0.7:
                return self.master_guide[best_match], confidence

        return "Unknown", 0.5

    def batch_match(self, input_strings: List[str]) -> List[Tuple[str, float]]:
        """Match multiple strings at once"""
        return [self.match(s) for s in input_strings]

    def needs_review(self, confidence: float) -> bool:
        """Check if item needs manual review"""
        return confidence < self.threshold


# Example usage:
# matcher = FuzzyMatcher({"Regular Pay": "Base Wages", "OT": "Overtime"})
# tag, confidence = matcher.match("Regular Pay Hours")
# if matcher.needs_review(confidence):
#     # Flag for user review
