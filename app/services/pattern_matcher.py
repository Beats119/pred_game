from typing import List, Dict, Optional, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────
# DESIRED PATTERNS (hardcoded from Images folder)
# Each pattern is a list of 10 values (newest → oldest)
# 'B' = Big (number 5-9), 'S' = Small (number 0-4)
# ─────────────────────────────────────────────
DESIRED_PATTERNS = [
    {
        "name": "🔴 All 10 BIG",
        "emoji": "🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴",
        "sequence": ["B", "B", "B", "B", "B", "B", "B", "B", "B", "B"],
    },
    {
        "name": "🔵 All 10 SMALL",
        "emoji": "🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵",
        "sequence": ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    },
    {
        "name": "🔄 Alternating B-S-B-S... (Big first)",
        "emoji": "🔴🔵🔴🔵🔴🔵🔴🔵🔴🔵",
        "sequence": ["B", "S", "B", "S", "B", "S", "B", "S", "B", "S"],
    },
    {
        "name": "🔄 Alternating S-B-S-B... (Small first)",
        "emoji": "🔵🔴🔵🔴🔵🔴🔵🔴🔵🔴",
        "sequence": ["S", "B", "S", "B", "S", "B", "S", "B", "S", "B"],
    },
    # Bonus: 5-streak patterns (also valuable signals)
    {
        "name": "🔴 5x Big Streak",
        "emoji": "🔴🔴🔴🔴🔴",
        "sequence": ["B", "B", "B", "B", "B"],
    },
    {
        "name": "🔵 5x Small Streak",
        "emoji": "🔵🔵🔵🔵🔵",
        "sequence": ["S", "S", "S", "S", "S"],
    },
]


class PatternMatcher:
    """Matches last N Big/Small results against hardcoded desired patterns."""

    def convert_to_bs(self, result: Dict) -> str:
        """Convert a result dict to 'B' or 'S' using the bigSmall field directly."""
        big_small = result.get("bigSmall", "")
        if big_small:
            bs = big_small.strip().lower()
            if bs == "big":
                return "B"
            elif bs == "small":
                return "S"
        # Fallback: use number
        number = result.get("number", -1)
        if isinstance(number, int) and number >= 5:
            return "B"
        return "S"

    def analyze_history(self, history: List[Dict]) -> Optional[Tuple[str, str, str]]:
        """
        Checks the last N results (newest first) against all DESIRED_PATTERNS.
        Returns (PatternName, SequenceString, LatestPeriod) on first match, else None.
        """
        if not history:
            return None

        # Build B/S sequence newest-first
        sequence = [self.convert_to_bs(r) for r in history]
        latest_period = history[0].get("period", "Unknown")

        logger.debug(f"Live sequence (newest first): {sequence[:10]}")

        for pattern in DESIRED_PATTERNS:
            pat_seq = pattern["sequence"]
            n = len(pat_seq)

            if len(sequence) < n:
                continue

            if sequence[:n] == pat_seq:
                seq_str = " → ".join(
                    ["🔴 Big" if s == "B" else "🔵 Small" for s in pat_seq]
                )
                logger.info(f"✅ PATTERN MATCHED: {pattern['name']}")
                return (pattern["name"], seq_str, latest_period)

        logger.debug("No pattern matched this cycle.")
        return None


matcher = PatternMatcher()
