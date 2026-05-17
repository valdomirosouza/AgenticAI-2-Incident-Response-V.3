"""Domain service: exact percentile rank computation (ADR-0035, Spec LIM-02 §3.4).

Supports RQ1 (MTTD reduction): determines which 0-based rank to request from Redis
ZRANGE so that the adapter returns the exact latency value at percentile p.

No I/O — pure math. The Redis adapter calls rank_for() to resolve the ZRANGE index.
"""

from __future__ import annotations

import math


class PercentileCalculator:
    """Exact percentile rank math over a Redis Sorted Set (ADR-0035).

    All methods are static: this class carries no state and is never instantiated.
    """

    @staticmethod
    def rank_for(cardinality: int, percentile: int) -> int:
        """Compute the 0-based rank for percentile ``p`` in a set of ``n`` values.

        Algorithm (Spec LIM-02 §3.4, ADR-0035):
            rank = max(0, min(ceil(p / 100 * n) - 1, n - 1))

        Args:
            cardinality: Total number of entries in the sorted set (ZCARD result). Must be > 0.
            percentile: Integer in [1, 99].

        Returns:
            0-based rank suitable for use as the ``start`` and ``stop`` arguments of ZRANGE.

        Raises:
            ValueError: if cardinality ≤ 0 or percentile not in [1, 99].
        """
        if cardinality <= 0:
            raise ValueError(f"cardinality must be positive, got {cardinality}")
        if not 1 <= percentile <= 99:
            raise ValueError(f"percentile must be in [1, 99], got {percentile}")

        rank = math.ceil(percentile / 100 * cardinality) - 1
        return max(0, min(rank, cardinality - 1))

    @staticmethod
    def compute_from_values(values: list[float], percentile: int) -> float:
        """Compute the exact percentile from an in-memory list of numeric values.

        Applies the same algorithm as rank_for() after sorting ``values``.
        Intended for unit testing and for callers that already hold all values in memory.

        Args:
            values: Unsorted list of numeric measurements (e.g. latencies in ms).
            percentile: Integer in [1, 99].

        Returns:
            The value at the computed rank. Returns 0.0 for an empty list.
        """
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        rank = PercentileCalculator.rank_for(len(sorted_vals), percentile)
        return sorted_vals[rank]
