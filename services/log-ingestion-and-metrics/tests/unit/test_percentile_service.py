"""Unit tests for PercentileCalculator domain service.

Covers Spec LIM-02 §3.4 (exact percentile algorithm) and ADR-0035 (ZRANK rank formula).
All expected values are derived from the worked examples in ADR-0035 §Decision table.
No I/O — purely domain logic under test.
"""

from __future__ import annotations

import pytest

from log_ingestion.domain.services.percentile_service import PercentileCalculator


class TestRankFor:
    """Verify rank_for() against the worked examples in ADR-0035."""

    def test_cardinality_1_p99_returns_rank_0(self) -> None:
        # ceil(0.99 * 1) - 1 = 0 → the only entry
        assert PercentileCalculator.rank_for(1, 99) == 0

    def test_cardinality_100_p50_returns_rank_49(self) -> None:
        # ceil(0.50 * 100) - 1 = 49
        assert PercentileCalculator.rank_for(100, 50) == 49

    def test_cardinality_100_p99_returns_rank_98(self) -> None:
        # ceil(0.99 * 100) - 1 = 98
        assert PercentileCalculator.rank_for(100, 99) == 98

    def test_cardinality_1000_p95_returns_rank_949(self) -> None:
        # ceil(0.95 * 1000) - 1 = 949
        assert PercentileCalculator.rank_for(1000, 95) == 949

    def test_cardinality_2_p50_returns_rank_0(self) -> None:
        # ceil(0.50 * 2) - 1 = 0  (Spec LIM-02 §4 acceptance criterion)
        assert PercentileCalculator.rank_for(2, 50) == 0

    def test_cardinality_2_p99_returns_rank_1(self) -> None:
        # ceil(0.99 * 2) - 1 = 1  (Spec LIM-02 §4 acceptance criterion)
        assert PercentileCalculator.rank_for(2, 99) == 1

    def test_rank_clamped_to_zero_minimum(self) -> None:
        # For any valid input, rank must never be negative
        assert PercentileCalculator.rank_for(1, 1) >= 0

    def test_rank_clamped_to_cardinality_minus_one(self) -> None:
        rank = PercentileCalculator.rank_for(5, 99)
        assert rank <= 4

    def test_p1_cardinality_100_returns_rank_0(self) -> None:
        # ceil(0.01 * 100) - 1 = 0
        assert PercentileCalculator.rank_for(100, 1) == 0

    def test_zero_cardinality_raises(self) -> None:
        with pytest.raises(ValueError, match="cardinality"):
            PercentileCalculator.rank_for(0, 50)

    def test_negative_cardinality_raises(self) -> None:
        with pytest.raises(ValueError, match="cardinality"):
            PercentileCalculator.rank_for(-1, 50)

    def test_percentile_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="percentile"):
            PercentileCalculator.rank_for(100, 0)

    def test_percentile_100_raises(self) -> None:
        with pytest.raises(ValueError, match="percentile"):
            PercentileCalculator.rank_for(100, 100)

    def test_percentile_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="percentile"):
            PercentileCalculator.rank_for(100, -1)


class TestComputeFromValues:
    """Verify compute_from_values() using Spec LIM-02 §4 acceptance criteria."""

    def test_p50_two_values_returns_smaller(self) -> None:
        # Spec LIM-02 §4: P50 for [48, 512] = 48 (rank=0)
        assert PercentileCalculator.compute_from_values([48.0, 512.0], 50) == 48.0

    def test_p99_two_values_returns_larger(self) -> None:
        # Spec LIM-02 §4: P99 for [48, 512] = 512 (rank=1)
        assert PercentileCalculator.compute_from_values([48.0, 512.0], 99) == 512.0

    def test_single_value_any_percentile_returns_it(self) -> None:
        assert PercentileCalculator.compute_from_values([42.0], 50) == 42.0
        assert PercentileCalculator.compute_from_values([42.0], 99) == 42.0

    def test_unsorted_input_sorted_before_rank(self) -> None:
        # Input in reverse order — must still return correct percentile
        assert PercentileCalculator.compute_from_values([512.0, 48.0], 50) == 48.0

    def test_empty_list_returns_zero(self) -> None:
        assert PercentileCalculator.compute_from_values([], 95) == 0.0

    def test_100_values_p50_returns_50th_smallest(self) -> None:
        values = list(range(1, 101))  # 1..100
        result = PercentileCalculator.compute_from_values([float(v) for v in values], 50)
        # rank = ceil(0.5 * 100) - 1 = 49 → sorted[49] = 50.0
        assert result == 50.0

    def test_100_values_p99_returns_99th_smallest(self) -> None:
        values = list(range(1, 101))
        result = PercentileCalculator.compute_from_values([float(v) for v in values], 99)
        # rank = ceil(0.99 * 100) - 1 = 98 → sorted[98] = 99.0
        assert result == 99.0

    def test_1000_values_p95_returns_950th_smallest(self) -> None:
        values = list(range(1, 1001))
        result = PercentileCalculator.compute_from_values([float(v) for v in values], 95)
        # rank = ceil(0.95 * 1000) - 1 = 949 → sorted[949] = 950.0
        assert result == 950.0
